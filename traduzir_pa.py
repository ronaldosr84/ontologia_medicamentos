import requests
import pandas as pd
from deep_translator import GoogleTranslator

def buscar_rxnorm(nome_en):
    url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={nome_en}"
    r = requests.get(url).json()
    
    ids = r.get("idGroup", {}).get("rxnormId", [])
    return ids[0] if ids else None

def obter_nome_oficial(rx_id):
    url = f"https://rxnav.nlm.nih.gov/REST/rxcui/{rx_id}/properties.json"
    r = requests.get(url).json()
    
    return r["properties"]["name"]

def mapear_pt_en(nome_pt):
    nome_en = GoogleTranslator(source='pt', target='en').translate(nome_pt)
    
    rx_id = buscar_rxnorm(nome_en)
    
    if rx_id:
        nome_oficial = obter_nome_oficial(rx_id)
        return nome_pt, nome_oficial
    
    return nome_pt, None

# teste
df = pd.read_csv("./docs/medicamentos.csv")


#lista = ["ibuprofeno", "varfarina", "dipirona"]

for _, row in df.iterrows():
    pt, en = mapear_pt_en(row["PrincipioAtivo"])
    row.add("PrincipioAtivo_EN", en)
    print(f"{pt} → {en}")
    
df.to_csv("./docs/medicamentos_com_en.csv", index=False)