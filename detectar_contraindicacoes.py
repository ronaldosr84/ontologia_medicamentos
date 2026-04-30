from owlready2 import *

onto = get_ontology("ontologia_povoada.owx").load()
g = default_world.as_rdflib_graph()

print("Deteccao de Contraindicacoes por Alergia\n")

query_alergias = """
PREFIX ont: <http://www.semanticweb.org/ronaldo/ontologies/2026/3/ontologia_medicamentos.owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?paciente ?principioAtivo
WHERE {
    ?pac rdf:type ont:Paciente .
    ?pac ont:temAlergiaA ?pa .
    BIND(REPLACE(STR(?pac), ".*#", "") AS ?paciente)
    BIND(REPLACE(STR(?pa), ".*#", "") AS ?principioAtivo)
}
ORDER BY ?paciente
"""

resultados_alergias = g.query(query_alergias)
paciente_atual = None

print("Alergias cadastradas:\n")
for row in resultados_alergias:
    if paciente_atual != row.paciente:
        paciente_atual = row.paciente
        print(f"{row.paciente}:")
    print(f"  - alergico a {row.principioAtivo}")

if not list(resultados_alergias):
    print("Nenhuma alergia cadastrada")

print("\n---\n")

query_contraindicados = """
PREFIX ont: <http://www.semanticweb.org/ronaldo/ontologies/2026/3/ontologia_medicamentos.owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?paciente ?medicamento ?principioAtivo
WHERE {
    ?pac rdf:type ont:Paciente .
    ?pac ont:temAlergiaA ?pa .
    ?med rdf:type ont:Medicamento .
    ?med ont:temPrincipioAtivo ?pa .
    BIND(REPLACE(STR(?pac), ".*#", "") AS ?paciente)
    BIND(REPLACE(STR(?med), ".*#", "") AS ?medicamento)
    BIND(REPLACE(STR(?pa), ".*#", "") AS ?principioAtivo)
}
ORDER BY ?paciente ?medicamento
"""

resultados_contraindicados = g.query(query_contraindicados)
paciente_atual = None

print("Medicamentos contraindicados:\n")
for row in resultados_contraindicados:
    if paciente_atual != row.paciente:
        if paciente_atual is not None:
            print()
        paciente_atual = row.paciente
        print(f"{row.paciente}:")
    print(f"  - {row.medicamento} (contem {row.principioAtivo})")

if not list(resultados_contraindicados):
    print("Nenhuma contraindicacao identificada")

print("\n---\n")

query_uso_contraindicado = """
PREFIX ont: <http://www.semanticweb.org/ronaldo/ontologies/2026/3/ontologia_medicamentos.owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?paciente ?medicamento ?principioAtivo
WHERE {
    ?pac rdf:type ont:Paciente .
    ?pac ont:usaMedicamento ?med .
    ?med ont:temPrincipioAtivo ?pa .
    ?pac ont:temAlergiaA ?pa .
    BIND(REPLACE(STR(?pac), ".*#", "") AS ?paciente)
    BIND(REPLACE(STR(?med), ".*#", "") AS ?medicamento)
    BIND(REPLACE(STR(?pa), ".*#", "") AS ?principioAtivo)
}
ORDER BY ?paciente
"""

resultados_uso_contraindicado = g.query(query_uso_contraindicado)

print("ALERTA: Uso de medicamento contraindicado\n")
alerta_encontrado = False

for row in resultados_uso_contraindicado:
    alerta_encontrado = True
    print(f"CRITICO: {row.paciente} esta usando {row.medicamento}")
    print(f"         Paciente e alergico ao principio ativo {row.principioAtivo}")

if not alerta_encontrado:
    print("Nenhum uso inadequado detectado")
