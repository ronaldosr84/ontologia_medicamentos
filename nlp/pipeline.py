"""
Pipeline Text-to-SPARQL via LLM.

Fluxo:
    pergunta (PT)
      -> verifica catálogo (reusa se similar)
      -> LLM gera SPARQL (com schema + few-shot)
      -> executa contra a ontologia
      -> salva no catálogo
      -> formata resposta
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .catalogo import Catalogo, EntradaCatalogo
from .llm_cliente import ClienteLLM, MODELO_PADRAO
from .ontologia_loader import carregar_ontologia
from .schema_ontologia import SchemaOntologia, extrair_schema
from .sparql_llm import SparqlGerado, gerar_sparql


@dataclass
class ResultadoPipeline:
    pergunta: str
    sparql: str = ""
    explicacao: str = ""
    fonte: str = "llm"           # "llm" | "catalogo"
    reusada_de: Optional[int] = None
    resultados_brutos: list = field(default_factory=list)
    resposta: str = ""
    erro: Optional[str] = None
    entrada_catalogo: Optional[EntradaCatalogo] = None


class Pipeline:
    """Orquestra o fluxo Text-to-SPARQL."""

    def __init__(self, modelo: str = MODELO_PADRAO):
        self.onto, self.grafo = carregar_ontologia()
        self.schema: SchemaOntologia = extrair_schema(self.onto)
        self.cliente = ClienteLLM(modelo)
        self.catalogo = Catalogo.carregar()

    def responder(self, pergunta: str, forcar_llm: bool = False) -> ResultadoPipeline:
        res = ResultadoPipeline(pergunta=pergunta)

        # 1. Tentar reusar do catálogo
        if not forcar_llm:
            similar = self.catalogo.buscar_similar(pergunta)
            if similar is not None:
                res.fonte = "catalogo"
                res.reusada_de = similar.id
                res.sparql = similar.sparql
                res.explicacao = similar.explicacao

        # 2. Se não reusou, chama o LLM (com até 1 retry em caso de erro de execução)
        if not res.sparql:
            exemplos = self.catalogo.exemplos_few_shot(n=3)
            tentativas = 0
            erro_anterior = None
            sparql_anterior = None
            while tentativas < 2:
                ger: SparqlGerado = gerar_sparql(
                    pergunta, self.schema, self.cliente, exemplos,
                    erro_anterior=erro_anterior,
                    sparql_anterior=sparql_anterior,
                )
                if not ger.valido:
                    res.erro = ger.erro
                    res.resposta = f"Falha ao gerar SPARQL: {ger.erro}"
                    return res
                # Tenta executar pra ver se a query está sintaticamente válida
                try:
                    linhas = list(self.grafo.query(ger.sparql))
                    res.sparql = ger.sparql
                    res.explicacao = ger.explicacao
                    res.fonte = "llm" if tentativas == 0 else "llm-retry"
                    res.resultados_brutos = linhas
                    break
                except Exception as e:  # noqa: BLE001
                    tentativas += 1
                    erro_anterior = str(e)
                    sparql_anterior = ger.sparql
                    if tentativas >= 2:
                        res.sparql = ger.sparql
                        res.explicacao = ger.explicacao
                        res.fonte = "llm"
                        res.erro = f"Erro ao executar SPARQL (após {tentativas} tentativas): {e}"
                        res.resposta = res.erro
                        return res

        # 3. Se veio do catálogo, executa
        if res.fonte == "catalogo" and not res.resultados_brutos:
            try:
                res.resultados_brutos = list(self.grafo.query(res.sparql))
            except Exception as e:  # noqa: BLE001
                res.erro = f"Erro ao executar SPARQL do catálogo: {e}"
                res.resposta = res.erro
                return res

        res.resposta = self._formatar_resposta(res.resultados_brutos)

        # 4. Sempre salvar no catálogo (até reusos ficam registrados como referência)
        if res.fonte.startswith("llm"):
            res.entrada_catalogo = self.catalogo.adicionar(
                pergunta=pergunta,
                sparql=res.sparql,
                explicacao=res.explicacao,
            )
        else:
            # Reuso: registra a nova pergunta apontando para a original
            res.entrada_catalogo = self.catalogo.adicionar(
                pergunta=pergunta,
                sparql=res.sparql,
                explicacao=res.explicacao,
                reusada_de=res.reusada_de,
            )
        return res

    @staticmethod
    def _formatar_resposta(linhas: list) -> str:
        if not linhas:
            return "Nenhum resultado encontrado."

        # ASK -> booleano
        if len(linhas) == 1 and isinstance(linhas[0], bool):
            return "Sim." if linhas[0] else "Não."

        formatadas = []
        vistas_linhas = set()
        for l in linhas:
            try:
                vals = []
                for v in l:
                    if v is None:
                        continue
                    s = str(v)
                    # Se é URI, mostra só a parte depois do #
                    if "#" in s and s.startswith("http"):
                        s = s.split("#", 1)[1]
                    vals.append(s)
                # Dedup intra-linha (URI + nome legível costumam ser iguais)
                vistos = set()
                vals_unicos = []
                for v in vals:
                    if v not in vistos:
                        vistos.add(v)
                        vals_unicos.append(v)
                chave = tuple(vals_unicos)
                # Dedup inter-linha (varfarina<->ibuprofeno simétrico vira 2 linhas iguais)
                if chave in vistas_linhas:
                    continue
                vistas_linhas.add(chave)
                formatadas.append(" - " + " | ".join(vals_unicos))
            except TypeError:
                formatadas.append(f" - {l}")
        return "\n".join(formatadas)
