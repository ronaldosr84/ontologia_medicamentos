# Ontologia de Medicamentos

Trabalho prático de Representação de Conhecimento utilizando ontologias OWL e consultas SPARQL para modelagem do domínio de medicamentos.

## Descrição

Este projeto implementa uma ontologia baseada na Ontologia Brasileira de Medicamentos (OBM) para representar conhecimento sobre medicamentos, princípios ativos, pacientes, alergias e interações medicamentosas. O sistema demonstra o uso de mecanismos de inferência e linguagens de consulta em ontologias.

## Estrutura

```
.
├── ontologia_medicamentos.owx       # Ontologia OWL principal
├── ontologia_povoada.owx            # Ontologia com dados populados
├── carregar_individuos.py           # Script para povoar ontologia
├── consultas_sparql.py              # Consultas básicas SPARQL
├── detectar_interacoes.py           # Detecção de interações medicamentosas
├── detectar_contraindicacoes.py     # Detecção de contraindicações por alergia
├── inferencia_reasoner.py           # Inferência com reasoner OWL
└── docs/
    ├── medicamentos.csv             # Dataset de medicamentos
    └── Modelo_de_Dados_OBM2024.pdf  # Documentação OBM
```

## Ontologia

### Classes Principais

- `Medicamento` - Representa medicamentos
- `Principio_Ativo` - Substâncias ativas dos medicamentos
- `Paciente` - Indivíduos que usam medicamentos
- `Apresentacao` - Formas de apresentação dos medicamentos

### Classes Inferidas

- `MedicamentoContraindicadoPorAlergia` - Medicamentos que contêm princípios ativos aos quais algum paciente é alérgico
- `MedicamentosComRiscoDeInteracao` - Medicamentos cujos princípios ativos interagem entre si

### Propriedades

- `temPrincipioAtivo` - Relaciona medicamento ao seu princípio ativo
- `usaMedicamento` - Relaciona paciente aos medicamentos em uso
- `temAlergiaA` - Relaciona paciente aos princípios ativos aos quais é alérgico
- `interageCom` - Relaciona princípios ativos que interagem (propriedade simétrica)

## Requisitos

Python 3.8 ou superior.

### Instalação

```bash
pip install -r requirements.txt
```

Ou instalar manualmente:

```bash
pip install owlready2 rdflib pandas
```

Para o reasoner OWL é necessário ter Java instalado.

## Uso

### 1. Povoar a ontologia com dados

```bash
python carregar_individuos.py
```

Carrega dados do arquivo `docs/medicamentos.csv` e popula a ontologia.

### 2. Executar consultas SPARQL

```bash
python consultas_sparql.py
```

Demonstra consultas básicas: listar medicamentos, princípios ativos, pacientes, alergias e interações.

### 3. Detectar interações medicamentosas

```bash
python detectar_interacoes.py
```

Identifica pacientes usando medicamentos cujos princípios ativos interagem entre si.

### 4. Detectar contraindicações

```bash
python detectar_contraindicacoes.py
```

Identifica medicamentos contraindicados para pacientes com base em suas alergias.

### 5. Executar inferência com reasoner

```bash
python inferencia_reasoner.py
```

Usa o reasoner HermiT para classificar automaticamente medicamentos nas classes inferidas.

## Casos de Uso

### Exemplo 1: Interação Medicamentosa

O sistema detecta que um paciente usando Alivium (ibuprofeno) e Marivan (varfarina) está em risco, pois esses princípios ativos interagem.

### Exemplo 2: Contraindicação por Alergia

Se um paciente é alérgico a bromoprida, o sistema identifica que Digesan é contraindicado, pois contém esse princípio ativo.

### Exemplo 3: Inferência Automática

O reasoner classifica automaticamente medicamentos:
- Digesan é inferido como `MedicamentoContraindicadoPorAlergia` porque um paciente é alérgico a bromoprida
- Alivium é inferido como `MedicamentosComRiscoDeInteracao` porque ibuprofeno interage com varfarina

## Tecnologias

- **OWL 2** - Web Ontology Language para modelagem
- **SPARQL** - Linguagem de consulta para RDF/OWL
- **Owlready2** - Biblioteca Python para manipulação de ontologias
- **HermiT** - Reasoner OWL para inferências

## Referências

- Ontologia Brasileira de Medicamentos (OBM)
- W3C OWL 2 Web Ontology Language
- SPARQL 1.1 Query Language
