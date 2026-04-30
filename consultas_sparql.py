from owlready2 import *

onto = get_ontology("ontologia_povoada.owx").load()
g = default_world.as_rdflib_graph()

print("Consultas SPARQL - Ontologia de Medicamentos\n")

print("1. Medicamentos e Princípios Ativos")

query1 = """
PREFIX ont: <http://www.semanticweb.org/ronaldo/ontologies/2026/3/ontologia_medicamentos.owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?medicamento ?principioAtivo
WHERE {
    ?med rdf:type ont:Medicamento .
    ?med ont:temPrincipioAtivo ?pa .
    BIND(REPLACE(STR(?med), ".*#", "") AS ?medicamento)
    BIND(REPLACE(STR(?pa), ".*#", "") AS ?principioAtivo)
}
ORDER BY ?medicamento
"""

resultados1 = g.query(query1)
for row in resultados1:
    print(f"{row.medicamento:<20} {row.principioAtivo}")

print("\n2. Pacientes e Medicamentos em Uso")

query2 = """
PREFIX ont: <http://www.semanticweb.org/ronaldo/ontologies/2026/3/ontologia_medicamentos.owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?paciente ?medicamento
WHERE {
    ?pac rdf:type ont:Paciente .
    ?pac ont:usaMedicamento ?med .
    BIND(REPLACE(STR(?pac), ".*#", "") AS ?paciente)
    BIND(REPLACE(STR(?med), ".*#", "") AS ?medicamento)
}
ORDER BY ?paciente
"""

resultados2 = g.query(query2)
for row in resultados2:
    print(f"{row.paciente:<20} {row.medicamento}")

print("\n3. Alergias de Pacientes")

query3 = """
PREFIX ont: <http://www.semanticweb.org/ronaldo/ontologies/2026/3/ontologia_medicamentos.owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?paciente ?alergia
WHERE {
    ?pac rdf:type ont:Paciente .
    ?pac ont:temAlergiaA ?pa .
    BIND(REPLACE(STR(?pac), ".*#", "") AS ?paciente)
    BIND(REPLACE(STR(?pa), ".*#", "") AS ?alergia)
}
ORDER BY ?paciente
"""

resultados3 = g.query(query3)
for row in resultados3:
    print(f"{row.paciente:<20} alergico a {row.alergia}")

print("\n4. Interacoes entre Principios Ativos")

query4 = """
PREFIX ont: <http://www.semanticweb.org/ronaldo/ontologies/2026/3/ontologia_medicamentos.owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT DISTINCT ?principio1 ?principio2
WHERE {
    ?pa1 ont:interageCom ?pa2 .
    BIND(REPLACE(STR(?pa1), ".*#", "") AS ?principio1)
    BIND(REPLACE(STR(?pa2), ".*#", "") AS ?principio2)
    FILTER(STR(?pa1) < STR(?pa2))
}
ORDER BY ?principio1
"""

resultados4 = g.query(query4)
for row in resultados4:
    print(f"{row.principio1} <-> {row.principio2}")

print("\n5. Medicamentos com Mesmo Principio Ativo")

query5 = """
PREFIX ont: <http://www.semanticweb.org/ronaldo/ontologies/2026/3/ontologia_medicamentos.owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?principioAtivo (GROUP_CONCAT(?medicamento; separator=", ") AS ?medicamentos)
WHERE {
    ?med rdf:type ont:Medicamento .
    ?med ont:temPrincipioAtivo ?pa .
    BIND(REPLACE(STR(?pa), ".*#", "") AS ?principioAtivo)
    BIND(REPLACE(STR(?med), ".*#", "") AS ?medicamento)
}
GROUP BY ?principioAtivo
HAVING (COUNT(?med) > 1)
"""

resultados5 = g.query(query5)
for row in resultados5:
    print(f"{row.principioAtivo}: {row.medicamentos}")

print("\n6. Todos os Principios Ativos")

query6 = """
PREFIX ont: <http://www.semanticweb.org/ronaldo/ontologies/2026/3/ontologia_medicamentos.owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT DISTINCT ?principioAtivo
WHERE {
    ?pa rdf:type ont:Principio_Ativo .
    BIND(REPLACE(STR(?pa), ".*#", "") AS ?principioAtivo)
}
ORDER BY ?principioAtivo
"""

resultados6 = g.query(query6)
count = 0
for row in resultados6:
    print(f"  {row.principioAtivo}")
    count += 1
print(f"Total: {count}")

print("\n7. Estatisticas da Ontologia")
query_classes = """
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT (COUNT(DISTINCT ?class) AS ?total)
WHERE {
    ?class a owl:Class .
}
"""

query_individuos = """
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT (COUNT(DISTINCT ?ind) AS ?total)
WHERE {
    ?ind a owl:NamedIndividual .
}
"""

query_propriedades = """
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT (COUNT(DISTINCT ?prop) AS ?total)
WHERE {
    ?prop a owl:ObjectProperty .
}
"""

total_classes = list(g.query(query_classes))[0][0]
total_individuos = list(g.query(query_individuos))[0][0]
total_propriedades = list(g.query(query_propriedades))[0][0]

print(f"Classes: {total_classes}")
print(f"Individuos: {total_individuos}")
print(f"Object Properties: {total_propriedades}")
