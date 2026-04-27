from owlready2 import *
import pandas as pd

# Carregar ontologia existente
onto = get_ontology("ontologia_medicamentos.owx").load()

# Carregar dataset
df = pd.read_csv("./docs/medicamentos.csv")

with onto:
    # Referenciar classes existentes
    Medicamento = onto.search_one(iri="*Medicamento")
    PrincipioAtivo = onto.search_one(iri="*Principio_Ativo")
    
    # Referenciar propriedade
    temPrincipioAtivo = onto.search_one(iri="*temPrincipioAtivo")

    # Criar indivíduos
    for index, row in df.iterrows():
        nome_med = row["medicamento"].strip().lower().replace(" ", "_")
        nome_pa = row["PrincipioAtivo"].strip().lower().replace(" ", "_")
        
        # Criar ou reutilizar princípio ativo
        pa = onto.search_one(iri="*" + nome_pa)
        if not pa:
            pa = PrincipioAtivo(nome_pa)
        
        # Criar medicamento
        med = onto.search_one(iri="*" + nome_med)
        if not med:    
            med = Medicamento(nome_med)
        
        # Relacionar
        med.temPrincipioAtivo.append(pa)

# Salvar ontologia atualizada
onto.save(file="ontologia_povoada.owx", format="rdfxml")