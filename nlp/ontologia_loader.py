"""
Carrega a ontologia povoada e expõe um léxico de indivíduos para NER/linking.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from owlready2 import get_ontology, default_world

ONTOLOGIA_PATH = Path(__file__).resolve().parent.parent / "ontologia_povoada.owx"
ONT_PREFIX = "http://www.semanticweb.org/ronaldo/ontologies/2026/3/ontologia_medicamentos.owl#"


@dataclass
class Lexicon:
    """Mapeia nome canônico -> URI completa, agrupado por classe."""
    medicamentos: Dict[str, str] = field(default_factory=dict)
    principios_ativos: Dict[str, str] = field(default_factory=dict)
    pacientes: Dict[str, str] = field(default_factory=dict)

    def todos_medicamentos(self) -> List[str]:
        return list(self.medicamentos.keys())

    def todos_principios(self) -> List[str]:
        return list(self.principios_ativos.keys())

    def todos_pacientes(self) -> List[str]:
        return list(self.pacientes.keys())


def carregar_ontologia():
    """Carrega a ontologia povoada e devolve (onto, rdflib_graph)."""
    onto = get_ontology(str(ONTOLOGIA_PATH)).load()
    grafo = default_world.as_rdflib_graph()
    return onto, grafo


def construir_lexicon(onto) -> Lexicon:
    """Extrai todos os indivíduos da ontologia para um léxico simples."""
    lex = Lexicon()

    Medicamento = onto.search_one(iri="*Medicamento")
    PrincipioAtivo = onto.search_one(iri="*Principio_Ativo")
    Paciente = onto.search_one(iri="*Paciente")

    if Medicamento:
        for ind in Medicamento.instances():
            nome = ind.name
            lex.medicamentos[nome] = ind.iri

    if PrincipioAtivo:
        for ind in PrincipioAtivo.instances():
            nome = ind.name
            lex.principios_ativos[nome] = ind.iri

    if Paciente:
        for ind in Paciente.instances():
            nome = ind.name
            lex.pacientes[nome] = ind.iri

    return lex
