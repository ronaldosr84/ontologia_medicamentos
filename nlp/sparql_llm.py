"""
Gerador de SPARQL via LLM.

Recebe pergunta em PT + schema da ontologia + few-shot do catálogo,
e devolve uma query SPARQL pronta para executar.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import List, Optional

from .catalogo import EntradaCatalogo
from .schema_ontologia import SchemaOntologia, schema_para_prompt


@dataclass
class SparqlGerado:
    sparql: str
    explicacao: str
    erro: Optional[str] = None

    @property
    def valido(self) -> bool:
        return self.erro is None and bool(self.sparql.strip())


PROMPT_BASE = """Você é um especialista em SPARQL e ontologias OWL. Sua tarefa é traduzir perguntas em português para consultas SPARQL válidas que serão executadas contra a ontologia abaixo.

REGRAS CRÍTICAS:
1. Use APENAS classes e propriedades listadas no schema. NÃO invente propriedades.
2. **RESPEITE OS DOMÍNIOS E CONTRADOMÍNIOS DAS PROPRIEDADES.** Se `interageCom` tem domínio `Principio_Ativo`, ela só conecta DOIS princípios ativos — NUNCA medicamentos diretamente. Para "medicamento X interage com Y", o caminho é:
       med1 ont:temPrincipioAtivo ?pa1 .
       med2 ont:temPrincipioAtivo ?pa2 .
       ?pa1 ont:interageCom ?pa2 .
3. Use APENAS URIs de indivíduos que aparecem na lista de INDIVÍDUOS DA ONTOLOGIA. Se o usuário mencionar um nome que NÃO está na lista (ex: "penicilina", "dipirona"), retorne uma query que busque pelo NOME via FILTER, em vez de chutar um URI:
       FILTER(REGEX(STR(?x), "nome_buscado", "i"))
4. NÃO mapeie nomes do usuário para nomes comerciais por conta própria. Se o usuário diz "varfarina" e existe `varfarina` na lista de Principio_Ativo, use `ont:varfarina` — NÃO troque por nome comercial.
5. Sempre inclua os PREFIXes necessários no início da query.
6. **BIND vai sempre DENTRO do WHERE**, NUNCA na cláusula SELECT. Forma correta:
       SELECT ?med ?nome WHERE {
         ?med rdf:type ont:Medicamento .
         BIND(REPLACE(STR(?med), ".*#", "") AS ?nome)
       }
   Forma INCORRETA (sintaxe inválida):
       SELECT ?med (BIND(...) AS ?nome) WHERE { ... }   ← NÃO FAÇA ISSO
7. Use BIND(REPLACE(STR(?x), ".*#", "") AS ?nome) para retornar nomes legíveis em vez de URIs completas.
8. Para perguntas do tipo "existe...", use ASK. Para listar, use SELECT.
9. Se a pergunta envolver um indivíduo confirmado na lista, use o URI direto: ont:<nome_individual>.
10. Para Medicamento (lista parcial), nunca chute URIs — sempre use `?med rdf:type ont:Medicamento` e filtre por propriedades.
11. Sempre inclua o PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> quando usar `rdf:type`.

# EXEMPLOS DE RACIOCÍNIO

Pergunta: "Com o que a varfarina interage?"
Raciocínio: varfarina está em Principio_Ativo. interageCom liga PA->PA. Direto:
  SELECT ?nome WHERE {
    ont:varfarina ont:interageCom ?pa .
    BIND(REPLACE(STR(?pa), ".*#", "") AS ?nome)
  }

Pergunta: "Existe interação entre dipirona e ibuprofeno?"
Raciocínio: ibuprofeno está em PA. dipirona NÃO está. Use FILTER no nome do PA:
  ASK {
    ?pa1 a ont:Principio_Ativo .
    ?pa1 ont:interageCom ont:ibuprofeno .
    FILTER(REGEX(STR(?pa1), "dipirona", "i"))
  }

# SCHEMA DA ONTOLOGIA

{schema}

# FORMATO DA RESPOSTA

Responda APENAS com um JSON válido (sem cercas de código, sem texto extra) no formato:
{{"sparql": "<query SPARQL completa>", "explicacao": "<o que a query faz, em PT, 1-2 frases>"}}
"""

FEW_SHOT_TEMPLATE = """
# EXEMPLO {n}
Pergunta: {pergunta}
Resposta: {resposta_json}
"""


def montar_prompt(
    pergunta: str,
    schema: SchemaOntologia,
    exemplos: List[EntradaCatalogo],
) -> str:
    partes = [PROMPT_BASE.replace("{schema}", schema_para_prompt(schema))]

    for i, ex in enumerate(exemplos, 1):
        resposta = json.dumps(
            {"sparql": ex.sparql, "explicacao": ex.explicacao},
            ensure_ascii=False,
        )
        partes.append(
            f"\n# EXEMPLO {i}\nPergunta: {ex.pergunta}\nResposta: {resposta}\n"
        )

    partes.append(f"\n# PERGUNTA ATUAL\nPergunta: {pergunta}\nResposta:")
    return "\n".join(partes)


def _limpar_resposta(texto: str) -> str:
    """Remove cercas de código e espaços extras que o LLM pode adicionar."""
    texto = texto.strip()
    # Remove ```json ... ``` ou ``` ... ```
    texto = re.sub(r"^```(?:json)?\s*", "", texto)
    texto = re.sub(r"\s*```$", "", texto)
    return texto.strip()


def gerar_sparql(
    pergunta: str,
    schema: SchemaOntologia,
    cliente_llm,
    exemplos: Optional[List[EntradaCatalogo]] = None,
    erro_anterior: Optional[str] = None,
    sparql_anterior: Optional[str] = None,
) -> SparqlGerado:
    if cliente_llm is None or not cliente_llm.disponivel:
        return SparqlGerado(
            sparql="",
            explicacao="",
            erro="LLM indisponível. Configure OPENAI_API_KEY no .env.",
        )

    prompt = montar_prompt(pergunta, schema, exemplos or [])

    # Se é uma tentativa de correção, anexa contexto do erro
    if erro_anterior and sparql_anterior:
        prompt += (
            f"\n\n# TENTATIVA ANTERIOR FALHOU\n"
            f"SPARQL gerado: {sparql_anterior}\n"
            f"Erro: {erro_anterior}\n"
            f"Corrija a query mantendo a mesma intenção."
        )

    texto = cliente_llm.completar(prompt, max_tokens=800)
    if texto is None:
        return SparqlGerado(sparql="", explicacao="", erro="LLM retornou vazio.")

    texto = _limpar_resposta(texto)
    try:
        dados = json.loads(texto)
    except json.JSONDecodeError as e:
        return SparqlGerado(
            sparql="",
            explicacao="",
            erro=f"Resposta do LLM não é JSON válido: {e}\nResposta bruta:\n{texto}",
        )

    sparql = dados.get("sparql", "").strip()
    explicacao = dados.get("explicacao", "").strip()
    if not sparql:
        return SparqlGerado(
            sparql="", explicacao=explicacao,
            erro="LLM não devolveu SPARQL.",
        )
    return SparqlGerado(sparql=sparql, explicacao=explicacao)
