"""
Cliente LLM. Carrega chave do .env e devolve uma instância de ClienteOpenAI.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

from .llm_openai import ClienteOpenAI

MODELO_PADRAO = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def ClienteLLM(modelo: Optional[str] = None):
    """Devolve um cliente OpenAI configurado a partir do .env."""
    return ClienteOpenAI(modelo)
