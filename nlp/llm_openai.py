"""
Implementação OpenAI do cliente LLM.

Este módulo é commitado no repositório. É a implementação padrão.
"""
from __future__ import annotations

import os
from typing import Optional


class ClienteOpenAI:
    """Cliente OpenAI com a interface .completar(prompt) usada pelo pipeline."""

    def __init__(self, modelo: Optional[str] = None):
        self.modelo = modelo or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self._client = self._init()

    @staticmethod
    def _init():
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None
        try:
            from openai import OpenAI
        except ImportError:
            print("[aviso] pacote 'openai' não instalado.")
            return None
        return OpenAI(api_key=api_key)

    @property
    def disponivel(self) -> bool:
        return self._client is not None

    @property
    def descricao(self) -> str:
        return f"openai/{self.modelo}"

    def completar(self, prompt: str, max_tokens: int = 800) -> Optional[str]:
        if self._client is None:
            return None
        resp = self._client.chat.completions.create(
            model=self.modelo,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content
