"""
Executa as consultas SPARQL geradas pelo LLM (catálogo consultas_sparql_by_llm.json).

Equivalente "novo" ao consultas_sparql.py original: em vez de queries hard-coded,
lê o catálogo construído pelo pipeline de Text-to-SPARQL e executa cada uma.

Uso:
    python consultas_sparql_by_llm.py                # executa todas
    python consultas_sparql_by_llm.py --listar       # só lista, sem executar
    python consultas_sparql_by_llm.py --id 3         # executa só a entrada #3
    python consultas_sparql_by_llm.py --limite 10    # limita resultados por query
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from owlready2 import default_world, get_ontology

CATALOGO_PATH = Path(__file__).resolve().parent / "consultas_sparql_by_llm.json"
ONTOLOGIA_PATH = Path(__file__).resolve().parent / "ontologia_povoada.owx"


def carregar_catalogo() -> list[dict]:
    if not CATALOGO_PATH.exists():
        print(
            f"Catálogo não encontrado em {CATALOGO_PATH.name}.\n"
            "Faça pelo menos uma pergunta com pergunta_natural.py para criá-lo."
        )
        sys.exit(1)
    with open(CATALOGO_PATH, encoding="utf-8") as f:
        return json.load(f).get("entradas", [])


def formatar_valor(v) -> str:
    s = str(v)
    if "#" in s and s.startswith("http"):
        s = s.split("#", 1)[1]
    return s


def executar_uma(grafo, entrada: dict, limite: int | None) -> None:
    print(f"\n{'=' * 70}")
    print(f"#{entrada['id']} — {entrada['pergunta']}")
    if entrada.get("reusada_de"):
        print(f"  (reusada da entrada #{entrada['reusada_de']})")
    print(f"  {entrada.get('explicacao', '')}")
    print(f"  [{entrada.get('timestamp', '')}]")
    print(f"{'-' * 70}")
    print("SPARQL:")
    for linha in entrada["sparql"].splitlines():
        print(f"  {linha}")
    print(f"{'-' * 70}")
    print("Resultado:")

    try:
        linhas = list(grafo.query(entrada["sparql"]))
    except Exception as e:  # noqa: BLE001
        print(f"  ❌ Erro ao executar: {e}")
        return

    if not linhas:
        print("  (nenhum resultado)")
        return

    # ASK -> bool
    if len(linhas) == 1 and isinstance(linhas[0], bool):
        print("  Sim." if linhas[0] else "  Não.")
        return

    vistas = set()
    mostradas = 0
    for l in linhas:
        try:
            vals = []
            for v in l:
                if v is None:
                    continue
                vals.append(formatar_valor(v))
            # dedup intra-linha (URI + nome)
            vistos = set()
            unicos = []
            for v in vals:
                if v not in vistos:
                    vistos.add(v)
                    unicos.append(v)
            chave = tuple(unicos)
            if chave in vistas:
                continue
            vistas.add(chave)
            print(f"  - {' | '.join(unicos)}")
            mostradas += 1
            if limite and mostradas >= limite:
                restantes = len(linhas) - mostradas
                if restantes > 0:
                    print(f"  ... (+{restantes} resultados, use --limite 0 para ver todos)")
                break
        except TypeError:
            print(f"  - {l}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Executa as consultas SPARQL do catálogo gerado pelo LLM."
    )
    parser.add_argument("--listar", action="store_true",
                        help="Apenas lista as perguntas do catálogo")
    parser.add_argument("--id", type=int, default=None,
                        help="Executa apenas a entrada com este ID")
    parser.add_argument("--limite", type=int, default=10,
                        help="Limita resultados por query (0 = sem limite, default: 10)")
    args = parser.parse_args()

    entradas = carregar_catalogo()
    if not entradas:
        print("Catálogo vazio.")
        return 0

    if args.listar:
        print(f"Catálogo: {len(entradas)} entradas\n")
        for e in entradas:
            marca = " (reuso)" if e.get("reusada_de") else ""
            print(f"  #{e['id']:>3}{marca:8s} {e['pergunta']}")
        return 0

    if args.id is not None:
        entradas = [e for e in entradas if e["id"] == args.id]
        if not entradas:
            print(f"Entrada #{args.id} não encontrada.")
            return 1

    print(f"Carregando ontologia: {ONTOLOGIA_PATH.name}")
    get_ontology(str(ONTOLOGIA_PATH)).load()
    grafo = default_world.as_rdflib_graph()

    limite = args.limite if args.limite > 0 else None
    for entrada in entradas:
        executar_uma(grafo, entrada, limite)

    print(f"\n{'=' * 70}")
    print(f"Total executado: {len(entradas)} consulta(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
