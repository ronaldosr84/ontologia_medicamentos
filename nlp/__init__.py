"""
Módulo de Processamento de Linguagem Natural para a Ontologia de Medicamentos.

Pipeline:
    pergunta (PT) -> NER -> Entity Linking -> Intent -> SPARQL -> resultado
"""

from .pipeline import Pipeline, ResultadoPipeline

__all__ = ["Pipeline", "ResultadoPipeline"]
