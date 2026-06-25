from owlready2 import *


"""Visão geral do pipeline
PDF da bula
    ↓
Extração de texto (pdfplumber)
    ↓
Identificação de seções relevantes (regex)
    ↓
Extração de entidades (spaCy + regras)
    ↓
Estruturação em JSON
    ↓
Inserção na ontologia (Owlready2)"""


arquivo = "./bulas/bula_1781111790931.pdf"

"""Passo 1 — Extrair texto do PDF"""
import pdfplumber
import re

def extrair_texto_bula(caminho_pdf):
    texto_completo = ""
    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                texto_completo += texto + "\n"
    return texto_completo

texto = extrair_texto_bula(arquivo)
#print(texto[:500])  # visualizar início

"""Passo 2 — Identificar as seções relevantes
Bulas seguem uma estrutura padronizada pela RDC 47/2009 da ANVISA. As seções que interessam têm títulos previsíveis:"""

SECOES_ALVO = {
    "interacoes": [
        r"INTERA[CÇ][OÕ]ES? MEDICAMENTOSAS?",
        r"INTERA[CÇ][OÕ]ES? COM OUTROS MEDICAMENTOS",
    ],
    "contraindicacoes": [
        r"CONTRAINDICA[CÇ][OÕ]ES?",
        r"QUANDO N[AÃ]O DEVO USAR",  # bulas para pacientes
    ],
    "composicao": [
        r"COMPOSI[CÇ][AÃ]O",
        r"PRINC[IÍ]PIO ATIVO",
    ]
}


def extrair_secao(texto, padroes_inicio, proxima_secao=None):
    """Extrai o texto entre a seção alvo e a próxima seção."""
    for padrao in padroes_inicio:
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            inicio = match.start()
            # tenta encontrar onde a seção termina
            if proxima_secao:
                fim_match = re.search(proxima_secao, texto[inicio+1:], re.IGNORECASE)
                fim = inicio + fim_match.start() if fim_match else len(texto)
            else:
                fim = inicio + 3000  # fallback: pega os próximos 3000 chars
            return texto[inicio:fim].strip()
    return ""

secao_interacoes = extrair_secao(
    texto,
    SECOES_ALVO["interacoes"],
    proxima_secao=r"\n[A-Z][INTERA[CÇ]A[OÕ]? MEDICAMENTO-SUBSTÂNCIA\s]{5,}\n"  # próximo título em maiúsculas
)

#print("Seção de Interações:", secao_interacoes)  # visualizar início

"""Passo 3 — Extrair entidades com spaCy + regras
Para português e domínio médico, a abordagem mais prática para iniciantes 
é combinar o modelo de linguagem do spaCy com regras baseadas em padrões conhecidos."""

import spacy
from spacy.matcher import PhraseMatcher

nlp = spacy.load("pt_core_news_sm")

# Lista de medicamentos/princípios ativos conhecidos
# (você pode importar da sua ontologia existente)
MEDICAMENTOS_CONHECIDOS = [
    "varfarina", "amoxicilina", "ácido acetilsalicílico",
    "enalapril", "losartana", "atorvastatina", "sinvastatina",
    "fluoxetina", "sertralina", "penicilina", "metformina"
    "etilestranol", "amiodarona", "amitriptilina/nortriptilina", "azapropazona", "aztreonam",
    "benzafibrato", "cefamandol", "cloranfenicol", "hidrato de coral", "cimetidina", "ciprofloxacino", "clofibrato",
    "cotrimoxazol", "danazol", "destropropoxifeno", "destrotiroxina", "dipiridamol", "eritromicina", "neomicina", "feprazona",
    "fluconazol", "glucagon", "metronidazol", "miconazol", "oxifenilbutazona", "fenformina", "fenilbutazona", "feniramidol"
]

matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
padroes = [nlp.make_doc(m) for m in MEDICAMENTOS_CONHECIDOS]
matcher.add("MEDICAMENTO", padroes)

def extrair_medicamentos(texto_secao):
    doc = nlp(texto_secao)
    matches = matcher(doc)
    encontrados = []
    for match_id, start, end in matches:
        span = doc[start:end]
        encontrados.append(span.text)
    return list(set(encontrados))  # remove duplicatas

medicamentos_interacao = extrair_medicamentos(secao_interacoes)
#print("Medicamentos em interações:", medicamentos_interacao)

"""Passo 4 — Detectar contexto de risco
Só saber que um medicamento aparece na seção não basta — 
é preciso entender o tipo de risco mencionado. Padrões textuais ajudam muito aqui:"""

PADROES_RISCO = {
    "sangramento":    r"sangramento|hemorra|anticoagul",
    "toxicidade":     r"toxicidade|toxicidade muscular|miopatia|rabdomi",
    "hipertensão":    r"hipertens|press.o arterial",
    "hipotensão":     r"hipotens|queda de press",
    "alergia":        r"al[eé]rg|anafilax|hipersensibilidade",
    "serotonina":     r"serotonin",
}

def classificar_risco(texto_trecho):
    riscos = []
    for tipo, padrao in PADROES_RISCO.items():
        if re.search(padrao, texto_trecho, re.IGNORECASE):
            riscos.append(tipo)
    return riscos if riscos else ["não classificado"]

"""Passo 5 — Estruturar em JSON e alimentar a ontologia"""

import json

def processar_bula(caminho_pdf, nome_medicamento):
    texto = extrair_texto_bula(caminho_pdf)
    
    secao_int  = extrair_secao(texto, SECOES_ALVO["interacoes"])
    secao_cont = extrair_secao(texto, SECOES_ALVO["contraindicacoes"])

    resultado = {
        "medicamento": nome_medicamento,
        "interacoes": {
            "medicamentos_envolvidos": extrair_medicamentos(secao_int),
            "riscos": classificar_risco(secao_int),
            "texto_bruto": secao_int[:500]
        },
        "contraindicacoes": {
            "alergenos": extrair_medicamentos(secao_cont),
            "riscos": classificar_risco(secao_cont),
            "texto_bruto": secao_cont[:500]
        }
    }
    return resultado

# Executar e salvar
dados = processar_bula(arquivo, "MAREVAN")
with open("extracao_MAREVAN.json", "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=2)
    
    
# Carregar ontologia existente
onto = get_ontology("ontologia_medicamentos.owx").load()

with onto:
    # Referenciar classes
    Paciente = onto.search_one(iri="*Paciente")
    Medicamento = onto.search_one(iri="*Medicamento")
    PrincipioAtivo = onto.search_one(iri="*Principio_Ativo")

    # Referenciar propriedades
    usaMedicamento = onto.search_one(iri="*usaMedicamento")
    temAlergiaA = onto.search_one(iri="*temAlergiaA")
    interageCom = onto.search_one(iri="*interageCom")
    temPrincipioAtivo = onto.search_one(iri="*temPrincipioAtivo")
    
    # Criar ou reutilizar princípio ativo
    nome_pa = "varfarina"    
    pa = onto.search_one(iri="*" + nome_pa)
    if not pa:
       pa = PrincipioAtivo(nome_pa)
        
    # Criar medicamento
    nome_med = "marevan"
    med = onto.search_one(iri="*" + nome_med)
    if not med:    
        med = Medicamento(nome_med)
        
    # Relacionar
    med.temPrincipioAtivo.append(pa)
    
    #Ler os principios ativos do JSON extraído e inclui-los na ontologia
    with open("extracao_MAREVAN.json", "r", encoding="utf-8") as f:   
        df = json.load(f)
        interacoes = dados.get("interacoes", {})
        print("\n[ INTERAÇÕES MEDICAMENTOSAS ]")
        print("-" * 60)
        medicamentos_envolvidos = interacoes.get("medicamentos_envolvidos", [])    
        print("Medicamentos envolvidos:")
        print(medicamentos_envolvidos)
    
        PrincipioAtivo = onto.search_one(iri="*Principio_Ativo")
    
        for row in medicamentos_envolvidos:
            nome_pa = row.strip().lower().replace(" ", "_")
            # Criar ou reutilizar princípio ativo
            pa = onto.search_one(iri="*" + nome_pa)
            if not pa:
                pa = PrincipioAtivo(nome_pa)
            # Relacionar
            interageCom = onto.search_one(iri="*interageCom")
            pa1 = onto.search_one(iri="*" + "varfarina")
            pa.interageCom.append(pa1)  # Exemplo de relacionamento, ajuste conforme necessário

    # Salvar ontologia atualizada
    onto.save(file="ontologia_povoada.owx", format="rdfxml")
