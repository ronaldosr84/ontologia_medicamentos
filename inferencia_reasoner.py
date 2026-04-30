from owlready2 import *
import time

onto = get_ontology("ontologia_povoada.owx").load()

print("Inferencia com Reasoner OWL\n")

print("Classes definidas:")
for cls in onto.classes():
    print(f"  {cls.name}")

MedicamentoContraindicadoPorAlergia = onto.search_one(iri="*MedicamentoContraindicadoPorAlergia")
MedicamentosComRiscoDeInteracao = onto.search_one(iri="*MedicamentosComRiscoDeInteracao")

print("\nANTES DO REASONER:")
print(f"  MedicamentoContraindicadoPorAlergia: {len(list(MedicamentoContraindicadoPorAlergia.instances()))} instancias")
print(f"  MedicamentosComRiscoDeInteracao: {len(list(MedicamentosComRiscoDeInteracao.instances()))} instancias")

print("\nExecutando reasoner HermiT...")
start_time = time.time()

try:
    with onto:
        sync_reasoner_hermit(infer_property_values=True)
    elapsed = time.time() - start_time
    print(f"Concluido em {elapsed:.2f}s")
except Exception as e:
    print(f"Erro: {e}")

print("\nDEPOIS DO REASONER:")

instancias_contraindicado = list(MedicamentoContraindicadoPorAlergia.instances())
print(f"\nMedicamentoContraindicadoPorAlergia ({len(instancias_contraindicado)} instancias):")
for inst in instancias_contraindicado:
    print(f"  {inst.name}")
    if hasattr(inst, 'temPrincipioAtivo'):
        for pa in inst.temPrincipioAtivo:
            print(f"    - contem {pa.name}")

instancias_interacao = list(MedicamentosComRiscoDeInteracao.instances())
print(f"\nMedicamentosComRiscoDeInteracao ({len(instancias_interacao)} instancias):")
for inst in instancias_interacao:
    print(f"  {inst.name}")
    if hasattr(inst, 'temPrincipioAtivo'):
        for pa in inst.temPrincipioAtivo:
            if hasattr(pa, 'interageCom'):
                for pa_int in pa.interageCom:
                    print(f"    - {pa.name} interage com {pa_int.name}")

print("\n---")
print("\nRegras de inferencia utilizadas:")
print("""
1. MedicamentoContraindicadoPorAlergia
   Medicamento que contem principio ativo ao qual algum paciente e alergico

2. MedicamentosComRiscoDeInteracao
   Medicamento cujo principio ativo interage com outro principio ativo
""")
