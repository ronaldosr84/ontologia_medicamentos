"""
Introspecção da ontologia: extrai schema (classes + propriedades + amostras)
para servir de grounding no prompt do LLM.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .ontologia_loader import ONT_PREFIX, carregar_ontologia


@dataclass
class PropriedadeInfo:
    nome: str
    dominio: List[str] = field(default_factory=list)
    contradominio: List[str] = field(default_factory=list)


@dataclass
class SchemaOntologia:
    prefixo: str
    classes: List[str] = field(default_factory=list)
    object_properties: List[PropriedadeInfo] = field(default_factory=list)
    data_properties: List[str] = field(default_factory=list)
    amostras: dict = field(default_factory=dict)  # classe -> [nomes]


def extrair_schema(onto, amostras_por_classe: int = 200) -> SchemaOntologia:
    """Lê o schema OWL e devolve uma representação compacta para prompt."""
    schema = SchemaOntologia(prefixo=ONT_PREFIX)

    for c in onto.classes():
        schema.classes.append(c.name)

    for p in onto.object_properties():
        schema.object_properties.append(
            PropriedadeInfo(
                nome=p.name,
                dominio=[d.name for d in p.domain if hasattr(d, "name")],
                contradominio=[r.name for r in p.range if hasattr(r, "name")],
            )
        )

    for p in onto.data_properties():
        schema.data_properties.append(p.name)

    # Princípios ativos: lista COMPLETA (são poucos, ~95).
    # Medicamentos: amostra (são 600+, prompt ficaria gigante).
    # Pacientes: lista completa (são poucos).
    PA = onto.search_one(iri="*Principio_Ativo")
    if PA:
        schema.amostras["Principio_Ativo"] = [ind.name for ind in PA.instances()]

    PAC = onto.search_one(iri="*Paciente")
    if PAC:
        schema.amostras["Paciente"] = [ind.name for ind in PAC.instances()]

    MED = onto.search_one(iri="*Medicamento")
    if MED:
        nomes = [ind.name for ind in MED.instances()]
        schema.amostras["Medicamento"] = nomes[:amostras_por_classe]

    return schema


def schema_para_prompt(schema: SchemaOntologia) -> str:
    """Renderiza o schema como texto enxuto para colocar no prompt do LLM."""
    linhas = []
    linhas.append(f"PREFIX ont: <{schema.prefixo}>")
    linhas.append("")
    linhas.append("# Classes:")
    for c in schema.classes:
        linhas.append(f"  ont:{c}")

    linhas.append("")
    linhas.append("# Object Properties (com domínio e contradomínio):")
    for p in schema.object_properties:
        dom = ", ".join(p.dominio) if p.dominio else "?"
        rng = ", ".join(p.contradominio) if p.contradominio else "?"
        linhas.append(f"  ont:{p.nome}  ({dom} -> {rng})")

    if schema.data_properties:
        linhas.append("")
        linhas.append("# Data Properties:")
        for p in schema.data_properties:
            linhas.append(f"  ont:{p}")

    if schema.amostras:
        linhas.append("")
        linhas.append("# INDIVÍDUOS DA ONTOLOGIA (use APENAS estes URIs — não invente):")
        for cls, nomes in schema.amostras.items():
            if not nomes:
                continue
            if cls == "Medicamento":
                linhas.append(f"  {cls} ({len(nomes)} primeiros, há mais; use ?med rdf:type ont:Medicamento para varrer todos):")
                linhas.append("    " + ", ".join(nomes[:30]))
            else:
                linhas.append(f"  {cls} (LISTA COMPLETA, {len(nomes)}):")
                # quebra em linhas de ~80 chars para legibilidade
                buf, linha_atual = [], ""
                for n in nomes:
                    if len(linha_atual) + len(n) + 2 > 90:
                        buf.append(linha_atual.rstrip(", "))
                        linha_atual = ""
                    linha_atual += n + ", "
                if linha_atual:
                    buf.append(linha_atual.rstrip(", "))
                for l in buf:
                    linhas.append("    " + l)

    return "\n".join(linhas)


if __name__ == "__main__":  # debug
    onto, _ = carregar_ontologia()
    s = extrair_schema(onto)
    print(schema_para_prompt(s))
