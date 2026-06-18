"""
Catálogo de consultas SPARQL geradas pelo LLM.

Persistido em consultas_sparql_by_llm.json. Cada entrada tem:
    - pergunta: texto original em PT
    - sparql: query gerada
    - explicacao: descrição em PT do que a query faz
    - timestamp: ISO 8601
    - reusada_de: id (se reaproveitou de uma similar)
"""
from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from rapidfuzz import fuzz

CATALOGO_PATH = Path(__file__).resolve().parent.parent / "consultas_sparql_by_llm.json"
LIMIAR_REUSO = 95  # 0-100; bem alto para evitar reusos falsos quando só muda a entidade

# Stopwords que não devem afetar a comparação semântica
_STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "de", "da", "do", "das", "dos",
    "e", "ou", "que", "qual", "quais", "com", "para", "por", "em",
    "ao", "no", "na", "ha", "tem", "existe", "esta", "esto",
    "qual", "quais", "como", "onde", "quando", "porque",
}


@dataclass
class EntradaCatalogo:
    id: int
    pergunta: str
    sparql: str
    explicacao: str
    timestamp: str
    reusada_de: Optional[int] = None


@dataclass
class Catalogo:
    entradas: List[EntradaCatalogo] = field(default_factory=list)

    @classmethod
    def carregar(cls) -> "Catalogo":
        if not CATALOGO_PATH.exists():
            return cls()
        with open(CATALOGO_PATH, encoding="utf-8") as f:
            dados = json.load(f)
        cat = cls()
        for d in dados.get("entradas", []):
            cat.entradas.append(EntradaCatalogo(**d))
        return cat

    def salvar(self) -> None:
        payload = {
            "_descricao": "Catálogo de consultas SPARQL geradas pelo LLM. Cada entrada é registrada quando o usuário faz uma pergunta nova.",
            "total": len(self.entradas),
            "entradas": [asdict(e) for e in self.entradas],
        }
        with open(CATALOGO_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def proximo_id(self) -> int:
        return (max((e.id for e in self.entradas), default=0)) + 1

    def buscar_similar(self, pergunta: str, limiar: int = LIMIAR_REUSO) -> Optional[EntradaCatalogo]:
        """Procura no catálogo uma pergunta semanticamente similar.

        Para evitar falsos-positivos (ex: confundir 'amoxicilina' com 'penicilina'),
        exige tanto similaridade textual alta QUANTO que os tokens-chave (não-stopword)
        coincidam entre as duas perguntas.
        """
        if not self.entradas:
            return None
        norm_alvo = _normalizar(pergunta)
        tokens_alvo = _tokens_chave(norm_alvo)
        melhor: Optional[EntradaCatalogo] = None
        melhor_score = 0
        for e in self.entradas:
            norm_e = _normalizar(e.pergunta)
            tokens_e = _tokens_chave(norm_e)
            # Tokens-chave precisam ser idênticos para considerar reuso seguro
            if tokens_alvo != tokens_e:
                continue
            score = fuzz.token_set_ratio(norm_alvo, norm_e)
            if score > melhor_score:
                melhor_score = score
                melhor = e
        if melhor and melhor_score >= limiar:
            return melhor
        return None

    def adicionar(
        self,
        pergunta: str,
        sparql: str,
        explicacao: str,
        reusada_de: Optional[int] = None,
    ) -> EntradaCatalogo:
        entrada = EntradaCatalogo(
            id=self.proximo_id(),
            pergunta=pergunta,
            sparql=sparql,
            explicacao=explicacao,
            timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            reusada_de=reusada_de,
        )
        self.entradas.append(entrada)
        self.salvar()
        return entrada

    def exemplos_few_shot(self, n: int = 3) -> List[EntradaCatalogo]:
        """Devolve as N últimas entradas para usar como few-shot no prompt."""
        return self.entradas[-n:]


def _normalizar(t: str) -> str:
    t = t.lower().strip()
    t = unicodedata.normalize("NFKD", t)
    return "".join(c for c in t if not unicodedata.combining(c))


def _tokens_chave(t: str) -> frozenset:
    """Tokens não-stopword da pergunta normalizada, sem pontuação."""
    import re as _re
    palavras = _re.findall(r"[a-z0-9]+", t)
    return frozenset(p for p in palavras if p not in _STOPWORDS)
