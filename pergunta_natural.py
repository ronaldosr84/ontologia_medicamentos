"""
CLI: pergunta natural -> Text-to-SPARQL via LLM -> resposta.

Uso:
    python pergunta_natural.py                       # modo interativo
    python pergunta_natural.py "sua pergunta"        # uma pergunta só
    python pergunta_natural.py --debug "..."         # mostra SPARQL e fonte
    python pergunta_natural.py --forcar-llm "..."    # ignora catálogo
"""
import argparse
import sys

from nlp import Pipeline


def imprimir_debug(res) -> None:
    print("\n--- Pipeline ---")
    print(f"Pergunta: {res.pergunta}")
    print(f"Fonte: {res.fonte}" + (f" (reusou #{res.reusada_de})" if res.reusada_de else ""))
    print(f"\nExplicação: {res.explicacao}")
    print("\nSPARQL gerado:")
    print(res.sparql.strip())
    if res.entrada_catalogo:
        print(f"\n📁 Salvo no catálogo como #{res.entrada_catalogo.id}")
    print("\n--- Resposta ---")


def loop_interativo(pipe: Pipeline, debug: bool, forcar_llm: bool) -> None:
    print("Pergunta-Natural - Ontologia de Medicamentos (Text-to-SPARQL via LLM)")
    print("Digite sua pergunta (ou 'sair' para encerrar).\n")
    while True:
        try:
            pergunta = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté logo.")
            return
        if not pergunta:
            continue
        if pergunta.lower() in {"sair", "exit", "quit"}:
            return
        res = pipe.responder(pergunta, forcar_llm=forcar_llm)
        if debug:
            imprimir_debug(res)
        print(res.resposta)
        print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pergunta natural sobre a ontologia (Text-to-SPARQL via LLM)."
    )
    parser.add_argument("pergunta", nargs="*", help="Pergunta (vazio = modo interativo)")
    parser.add_argument("--debug", action="store_true", help="Mostra SPARQL gerado e metadados")
    parser.add_argument(
        "--forcar-llm", action="store_true",
        help="Ignora o catálogo e força nova chamada ao LLM",
    )
    args = parser.parse_args()

    pipe = Pipeline()
    if not pipe.cliente.disponivel:
        print(
            f"ERRO: LLM indisponível ({pipe.cliente.descricao}). "
            "Verifique LLM_PROVIDER e credenciais no .env.",
            file=sys.stderr,
        )
        return 1

    if args.pergunta:
        pergunta = " ".join(args.pergunta)
        res = pipe.responder(pergunta, forcar_llm=args.forcar_llm)
        if args.debug:
            imprimir_debug(res)
        print(res.resposta)
        return 0

    loop_interativo(pipe, args.debug, args.forcar_llm)
    return 0


if __name__ == "__main__":
    sys.exit(main())
