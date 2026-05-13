from owlready2 import *
import pandas as pd
import requests
import time

# -----------------------------
# CONFIGURAÇÕES
# -----------------------------
ONTO_PATH = "./ontologia_povoada.owx"
CSV_PATH = "./docs/medicamentos.csv"
OUTPUT_PATH = "./ontologia_integrada_RxNorm.owx"

# -----------------------------
# FUNÇÃO: buscar RxNorm (RxCUI)
# -----------------------------
def buscar_rxnorm(nome):
    try:
        url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={nome}"
        r = requests.get(url).json()
        ids = r.get("idGroup", {}).get("rxnormId", [])
        
        if ids:
            return ids[0]
        return None
    except Exception as e:
        print(f"Erro ao buscar RxNorm para {nome}: {e}")
        return None

# -----------------------------
# CARREGAR ONTOLOGIA
# -----------------------------
onto = get_ontology(ONTO_PATH).load()

# -----------------------------
# REFERÊNCIAS
# -----------------------------
with onto:
    Medicamento = onto.search_one(iri="*Medicamento")
    PrincipioAtivo = onto.search_one(iri="*PrincipioAtivo")
    temPrincipioAtivo = onto.search_one(iri="*temPrincipioAtivo")

# -----------------------------
# CARREGAR CSV
# -----------------------------
df = pd.read_csv(CSV_PATH)

# -----------------------------
# PROCESSAMENTO
# -----------------------------
with onto:
    for _, row in df.iterrows():
        nome_med = row["medicamento"].strip()
        nome_pa = row["PrincipioAtivo"].strip()

        # Normalização
        med_id = nome_med.lower().replace(" ", "_")
        pa_id = nome_pa.lower().replace(" ", "_")

        # -------------------------
        # PRINCÍPIO ATIVO
        # -------------------------
        pa = onto.search_one(iri="*" + pa_id)
        if not pa:
            pa = PrincipioAtivo(pa_id)
            pa.label = [nome_pa]

        # -------------------------
        # MEDICAMENTO
        # -------------------------
        med = onto.search_one(iri="*" + med_id)
        if not med:
            med = Medicamento(med_id)
            med.label = [nome_med]

        # Relacionar
        med.temPrincipioAtivo.append(pa)

        # -------------------------
        # BUSCAR RxNorm
        # -------------------------
        rx_id = buscar_rxnorm(nome_pa)

        if rx_id:
            rx_uri = f"http://rxnorm.nlm.nih.gov/id/{rx_id}"

            try:
                # Criar entidade externa
                external = Thing(rx_uri)

                # Mapear
                pa.equivalent_to.append(external)

                print(f"[OK] {nome_pa} → RxNorm:{rx_id}")
            except Exception as e:
                print(f"[ERRO] Mapping {nome_pa}: {e}")
        else:
            print(f"[WARN] RxNorm não encontrado para {nome_pa}")

        # Evitar sobrecarga na API
        time.sleep(0.2)

# -----------------------------
# SALVAR
# -----------------------------
onto.save(file=OUTPUT_PATH, format="rdfxml")

print(f"\nOntologia salva em: {OUTPUT_PATH}")