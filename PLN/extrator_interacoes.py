#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bula_interacoes.py

Extrai interações medicamentosas de bulas ANVISA (PDFs) usando PLN.
Diretórios fixos hardcoded. Execute com: python bula_interacoes.py
"""

import os
import sys
import re
import json
import csv
import html
import shutil
import subprocess
import logging
import tempfile
import time
import glob
import textwrap
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional, Set, Any
from functools import lru_cache
import urllib.request
import urllib.error

# Hardcoded directories
INPUT_DIR = "./bulas/"
OUTPUT_DIR = "./out/"
DATA_DIR = "./data/"

LOG_FILE = os.path.join(OUTPUT_DIR, "bula_interacoes.log")
REPORT_FILE = os.path.join(OUTPUT_DIR, "relatorio.html")

# NLTK resources
NLTK_RESOURCES = ["punkt", "stopwords"]
SPACY_MODEL = "pt_core_news_lg"
SPACY_MODEL_SHORT = "pt_core_news_lg"

# Fallback words to include in phrase matcher if a known list file is absent
DEFAULT_INTERACTION_KEYWORDS = [
    "interação", "interações", "interagir", "interage",
    "contraindicação", "contraindicações", "contraindicado",
    "precaução", "precauções", "advertência", "advertências",
    "efeito colateral", "efeitos colaterais", "reação adversa", "reações adversas",
    "aumenta", "diminui", "inibe", "induz", "potencializa", "antagoniza",
    "warfarina", "digoxina", "ciclosporina", "fenitoína", "carbamazepina",
    "rifampicina", "cimetidina", "ketoconazol", "fluconazol", "itraconazol",
    "amiodarona", "simvastatina", "atorvastatina", "metotrexato", "lítio",
    "litio", "dicumarol", "varfarina", "aspirina", "acenocumarol",
    "alopurinol", "glicose", "insulina", "antiácidos", "antiacidos",
    "anticoncepcional", "anticoncepcionais", "anticoagulante", "anticoagulantes",
    "antidepressivo", "antidepressivos", "antibiótico", "antibioticos",
    "antifúngico", "antifungicos", "anti-hipertensivo", "anti-hipertensivos",
    "bloqueador", "beta", "bloqueadores", "iec", "inibidor", "inibidores",
    "enzima", "cyp", "cyp3a4", "cyp2c9", "cyp2d6", "p-gp", "pgp",
    " serotoninina", "dopamina", "norepinefrina", "gaba", "glutamato",
    "absorção", "absorcao", "biodisponibilidade", "meia-vida", "meia vida",
    "clearance", "volume de distribuição", "proteína plasmática",
    "monitoramento", "monitorar", "ajuste de dose", "reduzir dose", "aumentar dose",
    "evitar uso concomitante", "não recomendado", "nao recomendado",
    "suspender", "descontinuar", "intervalo", "separação", "separacao",
]

# Known drug list file (one per line, fallback used if not present)
KNOWN_DRUGS_FILE = os.path.join(DATA_DIR, "medicamentos.txt")

# Interaction classification cues
SEVERITY_CUES = {
    "contraindicada": ["contraindicada", "contraindicado", "não usar", "nao usar", "proibido"],
    "grave": ["grave", "graves", "severa", "severo", "fatal", "risco de vida", "morte"],
    "moderada": ["moderada", "moderado", "cuidado", "atenção", "atencao", "precaução", "precaucao"],
    "leve": ["leve", "leves", "mínima", "minima", "pequena", "pouco significativo"],
    "monitorar": ["monitorar", "monitoramento", "vigilância", "vigilancia", "observar"],
    "ajustar": ["ajuste", "ajustar", "reduzir", "aumentar", "modificar dose", "alterar dose"],
}

INTERACTION_TYPE_CUES = {
    "farmacocinética": ["absorção", "absorcao", "biodisponibilidade", "metabolismo", "clearance", "meia-vida", "meia vida", "cyp", "cyp3a4", "cyp2c9", "cyp2d6", "p-gp", "pgp"],
    "farmacodinâmica": ["efeito", "efeitos", "potencializa", "antagoniza", "sinergismo", "sinergica", "aditivo", "agonista", "antagonista", "receptor"],
    "alimentar": ["alimento", "alimentos", "comida", "refeição", "refeicao", "suco", "groselha", "toranja", "toranjas", "cafeína", "alcool", "álcool", "álcool etílico"],
    "organização": ["organização", "organizacao", "procedimento", "procedimentos", "instrucional"],
}


class SetupError(Exception):
    pass


class HealthCheckError(Exception):
    pass


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def configure_logging() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8", mode="w"),
            logging.StreamHandler(sys.stdout),
        ],
    )


# ---------------------------------------------------------------------------
# Auto setup
# ---------------------------------------------------------------------------

def run_command(cmd: List[str], capture: bool = True) -> Tuple[int, str, str]:
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            check=False,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
        )
        return result.returncode, result.stdout or "", result.stderr or ""
    except Exception as exc:
        return -1, "", str(exc)


def ensure_python_package(package: str, pip_name: Optional[str] = None) -> None:
    pip_name = pip_name or package
    try:
        __import__(package)
        logging.info("[setup] pacote %s já disponível", pip_name)
    except ImportError:
        logging.warning("[setup] instalando %s via pip", pip_name)
        rc, out, err = run_command([sys.executable, "-m", "pip", "install", "--quiet", pip_name])
        if rc != 0:
            raise SetupError(f"Falha ao instalar {pip_name}: {err}\n{out}")
        __import__(package)
        logging.info("[setup] pacote %s instalado com sucesso", pip_name)


def ensure_spacy_model() -> None:
    try:
        import spacy
        spacy.load(SPACY_MODEL)
        logging.info("[setup] modelo spaCy %s já disponível", SPACY_MODEL)
    except Exception:
        logging.warning("[setup] baixando modelo spaCy %s", SPACY_MODEL)
        rc, out, err = run_command([sys.executable, "-m", "spacy", "download", SPACY_MODEL])
        if rc != 0:
            # Fallback: try installing via pip wheel
            pip_rc, pip_out, pip_err = run_command([
                sys.executable, "-m", "pip", "install", "--quiet",
                f"https://github.com/explosion/spacy-models/releases/download/{SPACY_MODEL_SHORT}-3.7.0/{SPACY_MODEL_SHORT}-3.7.0-py3-none-any.whl"
            ])
            if pip_rc != 0:
                raise SetupError(f"Falha ao baixar modelo spaCy {SPACY_MODEL}: {err}\n{pip_err}")
        import spacy
        spacy.load(SPACY_MODEL)
        logging.info("[setup] modelo spaCy %s baixado com sucesso", SPACY_MODEL)


def ensure_nltk_data() -> None:
    import nltk
    nltk_data_dirs = nltk.data.path
    if not nltk_data_dirs:
        nltk_data_dir = os.path.expanduser("~/nltk_data")
        os.makedirs(nltk_data_dir, exist_ok=True)
    else:
        nltk_data_dir = nltk_data_dirs[0]
    for resource in NLTK_RESOURCES:
        try:
            nltk.data.find(f"tokenizers/{resource}" if resource == "punkt" else f"corpora/{resource}")
            logging.info("[setup] NLTK resource %s já disponível", resource)
        except LookupError:
            logging.warning("[setup] baixando NLTK resource %s", resource)
            try:
                nltk.download(resource, quiet=True)
            except Exception as exc:
                raise SetupError(f"Falha ao baixar NLTK resource {resource}: {exc}")


def auto_setup() -> None:
    logging.info("[setup] iniciando setup automático")
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    ensure_python_package("pip")
    ensure_python_package("spacy")
    ensure_python_package("nltk")
    ensure_python_package("PyPDF2", "PyPDF2")
    ensure_python_package("pandas")

    ensure_nltk_data()
    ensure_spacy_model()

    logging.info("[setup] setup automático concluído")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def health_check() -> Dict[str, Any]:
    logging.info("[healthcheck] iniciando verificações")
    checks = {}
    checks["input_dir"] = os.path.isdir(INPUT_DIR)
    checks["output_dir"] = os.path.isdir(OUTPUT_DIR) or os.makedirs(OUTPUT_DIR, exist_ok=True) or True
    checks["data_dir"] = os.path.isdir(DATA_DIR) or os.makedirs(DATA_DIR, exist_ok=True) or True
    checks["pdfs"] = bool(glob.glob(os.path.join(INPUT_DIR, "*.pdf")))

    try:
        import spacy
        nlp = spacy.load(SPACY_MODEL)
        checks["spacy_model"] = True
        del nlp
    except Exception as exc:
        checks["spacy_model"] = False
        logging.error("[healthcheck] spaCy model unavailable: %s", exc)

    try:
        import nltk
        nltk.data.find("tokenizers/punkt")
        nltk.data.find("corpora/stopwords")
        checks["nltk"] = True
    except Exception as exc:
        checks["nltk"] = False
        logging.error("[healthcheck] NLTK data unavailable: %s", exc)

    try:
        import PyPDF2
        checks["pypdf2"] = True
    except Exception as exc:
        checks["pypdf2"] = False
        logging.error("[healthcheck] PyPDF2 unavailable: %s", exc)

    try:
        import pandas
        checks["pandas"] = True
    except Exception as exc:
        checks["pandas"] = False
        logging.error("[healthcheck] pandas unavailable: %s", exc)

    all_ok = all(checks.values())
    if not all_ok:
        failed = [k for k, v in checks.items() if not v]
        logging.error("[healthcheck] falhas: %s", failed)
        raise HealthCheckError(f"Health check falhou: {failed}")
    logging.info("[healthcheck] todas as verificações OK")
    return checks


# ---------------------------------------------------------------------------
# PDF extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_path: str, max_retries: int = 3) -> str:
    import PyPDF2
    logging.info("[pdf] extraindo texto de %s", pdf_path)
    last_error = ""
    for attempt in range(1, max_retries + 1):
        try:
            text = ""
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    try:
                        page_text = page.extract_text() or ""
                    except Exception as exc:
                        page_text = ""
                        logging.warning("[pdf] erro ao extrair página: %s", exc)
                    text += page_text + "\n"
            if text.strip():
                logging.info("[pdf] extração OK de %s (%d bytes)", pdf_path, len(text))
                return text
            last_error = "texto vazio"
        except Exception as exc:
            last_error = str(exc)
            logging.warning("[pdf] tentativa %d/%d falhou para %s: %s", attempt, max_retries, pdf_path, exc)
        if attempt < max_retries:
            backoff = 2 ** attempt
            logging.info("[pdf] retry com backoff de %ds", backoff)
            time.sleep(backoff)
    raise RuntimeError(f"Não foi possível extrair texto de {pdf_path}: {last_error}")


# ---------------------------------------------------------------------------
# NLP pipeline
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_nlp_model() -> Any:
    import spacy
    logging.info("[nlp] carregando modelo spaCy %s", SPACY_MODEL)
    nlp = spacy.load(SPACY_MODEL)
    return nlp


@lru_cache(maxsize=1)
def get_known_drugs() -> Set[str]:
    drugs: Set[str] = set()
    if os.path.exists(KNOWN_DRUGS_FILE):
        try:
            with open(KNOWN_DRUGS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        drugs.add(line.lower())
        except Exception as exc:
            logging.warning("[data] erro ao ler %s: %s", KNOWN_DRUGS_FILE, exc)
    else:
        logging.warning("[data] arquivo de medicamentos não encontrado: %s", KNOWN_DRUGS_FILE)
    # Fallback drug-like terms
    fallback = [
        "warfarina", "varfarina", "dicumarol", "acenocumarol", "fenprocumona",
        "digoxina", "digitoxina", "ciclosporina", "tacrolimo", "sirolimo",
        "fenitoína", "fenitoina", "carbamazepina", "lamotrigina", "valproato",
        "rifampicina", "rifabutina", "isoniazida", "claritromicina", "eritromicina",
        "cimetidina", "ranitidina", "omeprazol", "pantoprazol", "lansoprazol",
        "ketoconazol", "fluconazol", "itraconazol", "voriconazol", "posaconazol",
        "amiodarona", "verapamil", "diltiazem", "atorvastatina", "simvastatina",
        "rosuvastatina", "pravastatina", "metotrexato", "lítio", "litio",
        "alopurinol", "probenecida", "colchicina", "prednisona", "prednisolona",
        "metformina", "glibenclamida", "gliclazida", "glipizida", "insulina",
        "aspirina", "ácido acetilsalicílico", "acido acetilsalicilico",
        "ibuprofeno", "naproxeno", "diclofenaco", "paracetamol", "dipirona",
        "tramadol", "morfina", "fentanil", "codeína", "codeina",
        "diazepam", "lorazepam", "midazolam", "clonazepam", "alprazolam",
        "fluoxetina", "sertralina", "paroxetina", "citalopram", "escitalopram",
        "venlafaxina", "desvenlafaxina", "duloxetina", "amitriptilina", "nortriptilina",
        "risperidona", "olanzapina", "quetiapina", "aripiprazol", "haloperidol",
        "clozapina", "lítio", "carbamazepina", "valproato de sódio", "valproato de sodio",
        "sinvastatina", "fluindiona", "fenobarbital", "topiramato", "gabapentina",
        "pregabalina", "levetiracetam", "oxcarbazepina", "eslicarbazepina",
        "sildenafila", "tadalafila", "vardenafila",
    ]
    for d in fallback:
        drugs.add(d.lower())
    return drugs


@lru_cache(maxsize=1)
def get_interaction_patterns() -> List[str]:
    """Return a list of normalized lowercased phrases for PhraseMatcher."""
    patterns = [p.lower() for p in DEFAULT_INTERACTION_KEYWORDS]
    # include known drug names (they act as interaction anchors too)
    patterns.extend([p.lower() for p in get_known_drugs()])
    return list(set(patterns))


@dataclass
class Interaction:
    source_file: str
    section: str
    sentence: str
    entities: List[str]
    severity: str
    interaction_type: str
    confidence: float
    start_char: int
    end_char: int


def normalize_text(text: str) -> str:
    # Replace multiple whitespace, fix common OCR issues, lower-case
    text = re.sub(r"\s+", " ", text)
    text = text.replace("\x0c", " ")
    text = text.strip()
    return text


def split_into_sections(text: str) -> List[Tuple[str, str]]:
    # Heuristic section split based on common bula section headers and numbering.
    section_headers = [
        "interações medicamentosas", "interacoes medicamentosas",
        "interação medicamentosa", "interacoes medicamentosa",
        "contraindicações", "contraindicacoes", "contraindicação", "contraindicacao",
        "precauções", "precaucoes", "precaução", "precaucao",
        "advertências", "advertencias", "advertência", "advertencia",
        "reações adversas", "reacoes adversas", "efeitos colaterais",
        "posologia", "modo de usar", "características farmacológicas",
        "caracteristicas farmacologicas", "farmococinética", "farmacocinetica",
        "superdosagem", "conservação", "conservacao", "informações",
        "informacoes", "composição", "composicao", "indicações", "indicacoes",
    ]
    # Create a regex splitting on headers (case-insensitive, optional numbering)
    header_pattern = r"(?:\n|\r|^)\s*(?:\d+(?:\.\d+)*\s*)?(" + "|".join(re.escape(h) for h in section_headers) + r")\s*[:\-\.]?\s*"
    parts = re.split(header_pattern, text, flags=re.IGNORECASE)
    sections = []
    current_header = "início"
    if parts:
        # First part before any header
        sections.append((current_header, parts[0].strip()))
    for i in range(1, len(parts), 2):
        header = parts[i].strip().lower() if i < len(parts) else "sem título"
        body = parts[i + 1].strip() if (i + 1) < len(parts) else ""
        sections.append((header, body))
    return sections


def classify_severity(sentence: str) -> str:
    lower = sentence.lower()
    for severity, cues in SEVERITY_CUES.items():
        if any(cue in lower for cue in cues):
            return severity
    return "não classificada"


def classify_interaction_type(sentence: str) -> str:
    lower = sentence.lower()
    for itype, cues in INTERACTION_TYPE_CUES.items():
        if any(cue in lower for cue in cues):
            return itype
    return "não classificada"


def interaction_confidence(sentence: str, entities: List[str]) -> float:
    score = 0.0
    lower = sentence.lower()
    keywords = ["interação", "interações", "interage", "interagir", "interferir", "interfere"]
    if any(k in lower for k in keywords):
        score += 0.3
    if len(entities) >= 2:
        score += 0.3
    if classify_severity(sentence) != "não classificada":
        score += 0.2
    if classify_interaction_type(sentence) != "não classificada":
        score += 0.2
    return min(1.0, max(0.0, score))


def extract_interactions_from_text(text: str, source_file: str) -> List[Interaction]:
    import spacy
    import nltk
    from nltk.tokenize import sent_tokenize

    nlp = get_nlp_model()
    known_drugs = get_known_drugs()
    patterns = get_interaction_patterns()

    # Build matcher
    matcher = spacy.matcher.Matcher(nlp.vocab)
    phrase_matcher = spacy.matcher.PhraseMatcher(nlp.vocab, attr="LOWER")
    phrase_docs = [nlp.make_doc(p) for p in patterns if p.strip()]
    phrase_matcher.add("INTERACTION_PHRASE", phrase_docs)

    # Drug token matcher (known drug names, approximate)
    drug_pattern = [[{"LOWER": token.lower()}] for token in known_drugs if len(token.split()) == 1 and token.isalpha()]
    if drug_pattern:
        matcher.add("DRUG_SINGLE", drug_pattern)
    multi_drug_patterns = [
        [{"LOWER": token.lower()} for token in name.split()]
        for name in known_drugs if len(name.split()) > 1
    ]
    if multi_drug_patterns:
        matcher.add("DRUG_MULTI", multi_drug_patterns)

    # Matcher for interaction-ish verbs
    interaction_verb_pattern = [
        [{"LOWER": {"IN": ["aumenta", "diminui", "inibe", "induz", "potencializa", "antagoniza", "altera", "reduz", "eleva"]}}]
    ]
    matcher.add("INTERACTION_VERB", interaction_verb_pattern)

    sections = split_into_sections(text)
    interactions: List[Interaction] = []
    seen: Set[Tuple[str, int, int]] = set()

    for section_header, section_body in sections:
        if not section_body.strip():
            continue
        sentences = sent_tokenize(section_body, language="portuguese")
        for sentence in sentences:
            if len(sentence) < 10:
                continue
            doc = nlp(sentence)

            # Phrase matcher
            phrase_matches = phrase_matcher(doc)
            # Matcher (drugs + verbs)
            token_matches = matcher(doc)
            # NER entities (drugs / substances / diseases)
            ner_entities = [ent for ent in doc.ents if ent.label_ in ("CHEMICAL", "DRUG", "SUBSTANCE", "ORG", "PRODUCT")]

            # Collect drug-like entities from matcher + NER + substring
            matched_drugs: Set[str] = set()
            for match_id, start, end in phrase_matches:
                span = doc[start:end]
                if span.text.lower() in known_drugs or span.text.lower() in patterns:
                    matched_drugs.add(span.text.strip())
            for match_id, start, end in token_matches:
                span = doc[start:end]
                matched_drugs.add(span.text.strip())
            for ent in ner_entities:
                matched_drugs.add(ent.text.strip())
            # substring matching for known drugs (helps with OCR/abbreviations)
            lower_sentence = sentence.lower()
            for drug in known_drugs:
                if drug in lower_sentence and len(drug) > 3:
                    matched_drugs.add(drug)

            # Keep only those that are likely drugs or interaction terms with sufficient context
            if not matched_drugs:
                continue

            # Filter: require at least one interaction keyword or two drug-like entities
            has_interaction_keyword = any(
                kw in lower_sentence
                for kw in ["interação", "interações", "interage", "interagir", "interferir", "interfere",
                           "contraindicação", "contraindicações", "contraindicado", "contraindicada",
                           "precaução", "precauções", "advertência", "advertências", "efeito colateral",
                           "efeitos colaterais", "aumenta", "diminui", "inibe", "induz", "potencializa",
                           "antagoniza", "não recomendado", "nao recomendado", "evitar", "monitorar"]
            )
            drug_entities = [m for m in matched_drugs if m.lower() in known_drugs]
            if not has_interaction_keyword and len(drug_entities) < 2:
                continue

            sorted_entities = sorted(matched_drugs)
            severity = classify_severity(sentence)
            itype = classify_interaction_type(sentence)
            confidence = interaction_confidence(sentence, sorted_entities)

            key = (sentence.strip(), 0, len(sentence))
            if key in seen:
                continue
            seen.add(key)

            interactions.append(Interaction(
                source_file=source_file,
                section=section_header,
                sentence=sentence.strip(),
                entities=sorted_entities,
                severity=severity,
                interaction_type=itype,
                confidence=confidence,
                start_char=0,
                end_char=len(sentence),
            ))

    return interactions


# ---------------------------------------------------------------------------
# Export formats
# ---------------------------------------------------------------------------

def export_json(interactions: List[Interaction], filename: str) -> None:
    data = [asdict(i) for i in interactions]
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logging.info("[export] JSON salvo em %s (%d registros)", filename, len(data))


def export_csv(interactions: List[Interaction], filename: str) -> None:
    if not interactions:
        with open(filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["source_file", "section", "sentence", "entities", "severity", "interaction_type", "confidence", "start_char", "end_char"])
        return
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=asdict(interactions[0]).keys())
        writer.writeheader()
        for i in interactions:
            row = asdict(i)
            row["entities"] = "|".join(row["entities"])
            writer.writerow(row)
    logging.info("[export] CSV salvo em %s (%d registros)", filename, len(interactions))


def export_rdf(interactions: List[Interaction], filename: str) -> None:
    # Simple Turtle-like RDF serialization
    lines = []
    lines.append("@prefix ex: <http://example.org/bula/> .")
    lines.append("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .")
    lines.append("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .")
    lines.append("")
    for idx, i in enumerate(interactions, 1):
        uri = f"ex:interaction_{idx}"
        lines.append(f"{uri} a ex:DrugInteraction ;")
        lines.append(f"    ex:sourceFile {json.dumps(i.source_file)} ;")
        lines.append(f"    ex:section {json.dumps(i.section)} ;")
        lines.append(f"    ex:sentence {json.dumps(i.sentence)} ;")
        lines.append(f"    ex:severity {json.dumps(i.severity)} ;")
        lines.append(f"    ex:interactionType {json.dumps(i.interaction_type)} ;")
        lines.append(f"    ex:confidence \"{i.confidence}\"^^xsd:float ;")
        for ent in i.entities:
            lines.append(f"    ex:entity {json.dumps(ent)} ;")
        lines.append("    .")
        lines.append("")
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logging.info("[export] RDF salvo em %s (%d registros)", filename, len(interactions))


def export_html(interactions: List[Interaction], filename: str) -> None:
    html_rows = []
    for i in interactions:
        html_rows.append(
            "<<tr>"
            f"<<td>{html.escape(i.source_file)}</td>"
            f"<<td>{html.escape(i.section)}</td>"
            f"<<td>{html.escape(i.sentence)}</td>"
            f"<<td>{html.escape(' | '.join(i.entities))}</td>"
            f"<<td>{html.escape(i.severity)}</td>"
            f"<<td>{html.escape(i.interaction_type)}</td>"
            f"<<td>{i.confidence:.2f}</td>"
            "</tr>"
        )
    body = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Interações Medicamentosas Extraídas</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 2em; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; vertical-align: top; }}
th {{ background-color: #f2f2f2; }}
tr:nth-child(even) {{ background-color: #fafafa; }}
</style>
</head>
<body>
<h1>Interações Medicamentosas Extraídas</h1>
<p>Total de interações: {len(interactions)}</p>
<table>
<<thead>
<tr><th>Arquivo</th><th>Seção</th><th>Sentença</th><th>Entidades</th><th>Severidade</th><th>Tipo</th><th>Confiança</th></tr>
</thead>
<tbody>
{''.join(html_rows)}
</tbody>
</table>
</body>
</html>"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(body)
    logging.info("[export] HTML salvo em %s (%d registros)", filename, len(interactions))


def generate_report(interactions: List[Interaction], filenames: Dict[str, str], health: Dict[str, Any]) -> None:
    total = len(interactions)
    by_severity: Dict[str, int] = {}
    by_type: Dict[str, int] = {}
    by_file: Dict[str, int] = {}
    for i in interactions:
        by_severity[i.severity] = by_severity.get(i.severity, 0) + 1
        by_type[i.interaction_type] = by_type.get(i.interaction_type, 0) + 1
        by_file[i.source_file] = by_file.get(i.source_file, 0) + 1

    severity_rows = "\n".join(
        f"<<tr><td>{html.escape(k)}</td><td>{v}</td></tr>"
        for k, v in sorted(by_severity.items(), key=lambda x: -x[1])
    )
    type_rows = "\n".join(
        f"<<tr><td>{html.escape(k)}</td><td>{v}</td></tr>"
        for k, v in sorted(by_type.items(), key=lambda x: -x[1])
    )
    file_rows = "\n".join(
        f"<<tr><td>{html.escape(k)}</td><td>{v}</td></tr>"
        for k, v in sorted(by_file.items(), key=lambda x: -x[1])
    )

    health_rows = "\n".join(
        f"<<tr><td>{html.escape(k)}</td><td>{'OK' if v else 'Falha'}</td></tr>"
        for k, v in health.items()
    )

    body = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Relatório de Extração de Interações</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 2em; color: #333; }}
h1, h2 {{ color: #2c3e50; }}
table {{ border-collapse: collapse; margin-bottom: 1.5em; min-width: 40%; }}
th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
th {{ background-color: #f2f2f2; }}
.ok {{ color: green; }}
.fail {{ color: red; }}
</style>
</head>
<body>
<h1>Relatório de Extração de Interações Medicamentosas</h1>
<p>Data/Hora: {datetime.now().isoformat()}</p>
<p>Total de interações extraídas: <strong>{total}</strong></p>

<h2>Health Check</h2>
<table>
<<thead><tr><th>Item</th><th>Status</th></tr></thead>
<tbody>{health_rows}</tbody>
</table>

<h2>Arquivos de Saída</h2>
<ul>
<li><a href="{os.path.basename(filenames.get('json', ''))}">JSON</a></li>
<li><a href="{os.path.basename(filenames.get('csv', ''))}">CSV</a></li>
<li><a href="{os.path.basename(filenames.get('rdf', ''))}">RDF/Turtle</a></li>
<li><a href="{os.path.basename(filenames.get('html', ''))}">HTML</a></li>
</ul>

<h2>Distribuição por Severidade</h2>
<table>
<<thead><tr><th>Severidade</th><th>Quantidade</th></tr></thead>
<tbody>{severity_rows}</tbody>
</table>

<h2>Distribuição por Tipo</h2>
<table>
<<thead><tr><th>Tipo</th><th>Quantidade</th></tr></thead>
<tbody>{type_rows}</tbody>
</table>

<h2>Interações por Arquivo</h2>
<table>
<<thead><tr><th>Arquivo</th><th>Quantidade</th></tr></thead>
<tbody>{file_rows}</tbody>
</table>
</body>
</html>"""
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(body)
    logging.info("[report] relatório salvo em %s", REPORT_FILE)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main() -> None:
    configure_logging()
    try:
        auto_setup()
        health = health_check()

        pdf_files = sorted(glob.glob(os.path.join(INPUT_DIR, "*.pdf")))
        if not pdf_files:
            logging.warning("[pipeline] nenhum PDF encontrado em %s", INPUT_DIR)
            # Still produce empty outputs
        else:
            logging.info("[pipeline] encontrados %d PDFs em %s", len(pdf_files), INPUT_DIR)

        all_interactions: List[Interaction] = []
        for pdf_path in pdf_files:
            try:
                text = extract_text_from_pdf(pdf_path)
                text = normalize_text(text)
                interactions = extract_interactions_from_text(text, source_file=os.path.basename(pdf_path))
                all_interactions.extend(interactions)
            except Exception as exc:
                logging.error("[pipeline] erro ao processar %s: %s", pdf_path, exc)
                continue

        # Deduplicate by sentence + file
        seen = set()
        dedup_interactions: List[Interaction] = []
        for i in all_interactions:
            key = (i.source_file, i.sentence.strip().lower())
            if key in seen:
                continue
            seen.add(key)
            dedup_interactions.append(i)

        filenames = {
            "json": os.path.join(OUTPUT_DIR, "interacoes.json"),
            "csv": os.path.join(OUTPUT_DIR, "interacoes.csv"),
            "rdf": os.path.join(OUTPUT_DIR, "interacoes.ttl"),
            "html": os.path.join(OUTPUT_DIR, "interacoes.html"),
        }
        export_json(dedup_interactions, filenames["json"])
        export_csv(dedup_interactions, filenames["csv"])
        export_rdf(dedup_interactions, filenames["rdf"])
        export_html(dedup_interactions, filenames["html"])
        generate_report(dedup_interactions, filenames, health)

        logging.info("[pipeline] concluído. %d interações extraídas.", len(dedup_interactions))
    except Exception as exc:
        logging.exception("[pipeline] erro fatal: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()