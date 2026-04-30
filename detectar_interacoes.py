from owlready2 import *

onto = get_ontology("ontologia_povoada.owx").load()
g = default_world.as_rdflib_graph()

print("Deteccao de Interacoes Medicamentosas\n")

query_interacoes = """
PREFIX ont: <http://www.semanticweb.org/ronaldo/ontologies/2026/3/ontologia_medicamentos.owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT DISTINCT ?paciente ?med1 ?med2 ?pa1 ?pa2
WHERE {
    ?pac rdf:type ont:Paciente .
    ?pac ont:usaMedicamento ?medicamento1 .
    ?medicamento1 ont:temPrincipioAtivo ?principio1 .
    ?pac ont:usaMedicamento ?medicamento2 .
    ?medicamento2 ont:temPrincipioAtivo ?principio2 .
    ?principio1 ont:interageCom ?principio2 .
    FILTER(?medicamento1 != ?medicamento2)
    BIND(REPLACE(STR(?pac), ".*#", "") AS ?paciente)
    BIND(REPLACE(STR(?medicamento1), ".*#", "") AS ?med1)
    BIND(REPLACE(STR(?medicamento2), ".*#", "") AS ?med2)
    BIND(REPLACE(STR(?principio1), ".*#", "") AS ?pa1)
    BIND(REPLACE(STR(?principio2), ".*#", "") AS ?pa2)
}
ORDER BY ?paciente
"""

resultados = g.query(query_interacoes)
paciente_atual = None

for row in resultados:
    if paciente_atual != row.paciente:
        if paciente_atual is not None:
            print()
        paciente_atual = row.paciente
        print(f"Paciente: {row.paciente}")

    print(f"  Interacao: {row.med1} ({row.pa1}) <-> {row.med2} ({row.pa2})")

if not list(resultados):
    print("Nenhuma interacao detectada")

print("\n---\n")

query_uso = """
PREFIX ont: <http://www.semanticweb.org/ronaldo/ontologies/2026/3/ontologia_medicamentos.owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?paciente ?medicamento ?principioAtivo
WHERE {
    ?pac rdf:type ont:Paciente .
    ?pac ont:usaMedicamento ?med .
    ?med ont:temPrincipioAtivo ?pa .
    BIND(REPLACE(STR(?pac), ".*#", "") AS ?paciente)
    BIND(REPLACE(STR(?med), ".*#", "") AS ?medicamento)
    BIND(REPLACE(STR(?pa), ".*#", "") AS ?principioAtivo)
}
ORDER BY ?paciente ?medicamento
"""

resultados_uso = g.query(query_uso)
paciente_atual = None

print("Medicamentos em uso:\n")
for row in resultados_uso:
    if paciente_atual != row.paciente:
        if paciente_atual is not None:
            print()
        paciente_atual = row.paciente
        print(f"{row.paciente}:")
    print(f"  - {row.medicamento} ({row.principioAtivo})")
