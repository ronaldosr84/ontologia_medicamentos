# Ontologia de Medicamentos

Trabalho prático de Representação de Conhecimento utilizando ontologias OWL e consultas SPARQL para modelagem do domínio de medicamentos.

## Descrição

Este projeto implementa uma ontologia baseada na Ontologia Brasileira de Medicamentos (OBM) para representar conhecimento sobre medicamentos, princípios ativos, pacientes, alergias e interações medicamentosas. O sistema demonstra o uso de mecanismos de inferência e linguagens de consulta em ontologias.

## Estrutura

```
.
├── ontologia_medicamentos.owx       # Ontologia OWL principal (estrutura)
├── ontologia_povoada.owx            # Ontologia com dados populados
├── popular_ontologia.sh             # 🚀 Script principal para popular dados
├── carregar_individuos.py           # Carrega medicamentos do CSV
├── povoar_dados_completo.py         # Adiciona pacientes e cenários de exemplo
├── consultas_sparql.py              # Consultas SPARQL pré-definidas (estatísticas)
├── detectar_interacoes.py           # Detecção de interações medicamentosas
├── detectar_contraindicacoes.py     # Detecção de contraindicações por alergia
├── inferencia_reasoner.py           # Inferência com reasoner OWL
│
├── pergunta_natural.py              # 🧠 CLI Text-to-SPARQL via LLM (NOVO)
├── consultas_sparql_by_llm.py       # Executa o catálogo gerado pelo LLM (NOVO)
├── consultas_sparql_by_llm.json     # Catálogo persistente (criado em uso)
├── nlp/                             # Pipeline de PLN
│   ├── ontologia_loader.py
│   ├── schema_ontologia.py
│   ├── sparql_llm.py
│   ├── catalogo.py
│   ├── llm_cliente.py
│   ├── llm_openai.py
│   └── pipeline.py
│
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

### Interações Medicamentosas Cadastradas

O sistema possui as seguintes interações medicamentosas baseadas em evidências clínicas:

| Princípio Ativo 1 | Princípio Ativo 2 | Tipo de Interação |
|-------------------|-------------------|-------------------|
| Varfarina | Ácido Acetilsalicílico (Aspirina) | Risco de sangramento |
| Varfarina | Ibuprofeno | Risco de sangramento |
| Enalapril | Losartana | Duplo bloqueio SRAA |
| Atorvastatina | Sinvastatina | Toxicidade muscular |
| Fluoxetina | Sertralina | Síndrome serotoninérgica |
| Ibuprofeno | Diclofenaco | Toxicidade GI aumentada |

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

## Como Usar

### 🚀 Início Rápido (Método Recomendado)

Execute o script de população completo que carrega medicamentos do CSV e adiciona dados de exemplo:

```bash
./popular_ontologia.sh
```

Este script executa automaticamente:
1. Carrega medicamentos do arquivo `docs/medicamentos.csv`
2. Adiciona pacientes, alergias e interações de exemplo

**⚠️ Importante:** Sempre use este script para popular a ontologia. Não execute `carregar_individuos.py` diretamente, pois ele apaga os dados de exemplo.

---

### 📋 Scripts de Análise

#### 1. Consultar a ontologia

```bash
python consultas_sparql.py
```

Exibe estatísticas e consultas SPARQL básicas:
- Medicamentos e princípios ativos
- Pacientes e medicamentos em uso
- Alergias cadastradas
- Interações medicamentosas
- Estatísticas gerais da ontologia

#### 2. Detectar interações medicamentosas

```bash
python detectar_interacoes.py
```

Identifica pacientes usando medicamentos cujos princípios ativos interagem entre si, listando:
- Pacientes com interações detectadas
- Pares de medicamentos que interagem
- Lista completa de medicamentos em uso por paciente

#### 3. Detectar contraindicações

```bash
python detectar_contraindicacoes.py
```

Identifica contraindicações por alergia:
- Alergias cadastradas por paciente
- Medicamentos contraindicados (contêm princípios ativos alergênicos)
- **ALERTAS CRÍTICOS**: Pacientes usando medicamentos contraindicados

#### 4. Executar inferência com reasoner

```bash
python inferencia_reasoner.py
```

Usa o reasoner HermiT para classificar automaticamente medicamentos nas classes inferidas (requer Java instalado).

## Casos de Uso

O sistema inclui 6 pacientes com dados de exemplo para demonstrar diferentes cenários clínicos:

### ✅ Exemplo 1: Paciente sem problemas (controle)

**Pedro Ferreira**
- Medicamentos: Metformina + Omeprazol
- ✅ Status: Sem interações ou contraindicações

---

### ⚠️ Exemplo 2: Interação Medicamentosa - Risco de Sangramento

**Maria Silva**
- Medicamentos: Varfarina + Aspirina
- ⚠️ Problema: Ambos são anticoagulantes
- 🚨 Risco: Sangramento grave
- 📋 Recomendação: Evitar uso simultâneo

---

### ⚠️ Exemplo 3: Interação Medicamentosa - Duplo Bloqueio SRAA

**Ana Costa**
- Medicamentos: Enalapril + Losartana + Ibuprofeno
- ⚠️ Problema: IECA + BRA (duplo bloqueio do sistema renina-angiotensina)
- 🚨 Risco: Hipotensão severa, hipercalemia, lesão renal
- 📋 Recomendação: Não combinar IECA com BRA

---

### ⚠️ Exemplo 4: Interação Medicamentosa - Estatinas Combinadas

**Carlos Oliveira**
- Medicamentos: Atorvastatina + Sinvastatina
- ⚠️ Problema: Duas estatinas combinadas
- 🚨 Risco: Miopatia, rabdomiólise (lesão muscular grave)
- 📋 Recomendação: Usar apenas uma estatina

---

### ⚠️ Exemplo 5: Interação Medicamentosa - ISRSs Combinados

**Beatriz Lima**
- Medicamentos: Fluoxetina + Sertralina
- ⚠️ Problema: Dois antidepressivos ISRS combinados
- 🚨 Risco: Síndrome serotoninérgica (pode ser fatal)
- 📋 Recomendação: Nunca combinar ISRSs

---

### 🚨 Exemplo 6: Contraindicação por Alergia

**João Santos**
- Alergia: Penicilina
- Medicamento em uso: Amoxicilina
- 🚨 **ALERTA CRÍTICO**: Amoxicilina contém penicilina
- 🚨 Risco: Reação alérgica grave (anafilaxia)
- 📋 Recomendação: NUNCA prescrever amoxicilina para alérgicos à penicilina

---

## 📊 Resultados Esperados

Ao executar os scripts de detecção, você verá:

### Consultas SPARQL
```
Estatísticas da Ontologia
Classes: 14
Indivíduos: 67
Object Properties: 4
Total de Princípios Ativos: 18
```

### Detecção de Interações
- 4 pacientes com interações medicamentosas detectadas
- 8 pares de medicamentos que interagem (cada interação aparece 2x por ser simétrica)

### Detecção de Contraindicações
- 1 paciente com alergia cadastrada
- 1 alerta crítico de uso de medicamento contraindicado

---

## ✅ Validação dos Resultados

Todas as detecções do sistema são **clinicamente corretas** e representam situações reais que ocorrem em farmácias e hospitais:

- ✅ Todas as interações medicamentosas são reconhecidas pela literatura médica
- ✅ Todas as contraindicações por alergia são validadas clinicamente
- ✅ Os riscos apresentados correspondem a situações reais de risco aos pacientes
- ✅ As recomendações seguem protocolos médicos estabelecidos

## 🧠 Pergunta Natural (Text-to-SPARQL via LLM)

A partir de junho/2026 o projeto inclui um sistema de PLN que aceita perguntas em português e responde a partir da ontologia. O LLM (via OpenAI) traduz cada pergunta em uma consulta SPARQL válida, que é executada contra a ontologia povoada.

```
pergunta (PT)
   ↓ (busca catálogo - reusa se a mesma pergunta já foi feita)
   ↓ LLM gera SPARQL (com o schema da ontologia + few-shot do catálogo)
   ↓ retry automático se a query for sintaticamente inválida
   ↓ executa contra a ontologia
   ↓ salva no catálogo
   resposta
```

### Componentes

| Módulo | Função |
|---|---|
| `nlp/schema_ontologia.py` | Extrai classes + propriedades + amostras de indivíduos para servir de grounding |
| `nlp/sparql_llm.py` | Monta o prompt (regras + schema + few-shot) e chama o LLM |
| `nlp/catalogo.py` | Persiste perguntas e queries em `consultas_sparql_by_llm.json`, faz reuso por tokens-chave |
| `nlp/llm_cliente.py` | Factory que escolhe provedor LLM via `LLM_PROVIDER` |
| `nlp/llm_openai.py` | Implementação OpenAI |
| `nlp/pipeline.py` | Orquestra todo o fluxo |
| `pergunta_natural.py` | CLI interativo |
| `consultas_sparql_by_llm.py` | Executa todas as consultas registradas no catálogo |

### Como usar

```bash
# 1. Criar venv e instalar dependências
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Configurar a chave da API
cp .env.example .env
# Edite .env e cole sua OPENAI_API_KEY

# 3. Fazer perguntas em linguagem natural
python pergunta_natural.py "Quais medicamentos contêm amoxicilina?"
python pergunta_natural.py "Com o que a varfarina interage?"
python pergunta_natural.py "Existe interação entre dipirona e ibuprofeno?"

# Modo interativo (REPL)
python pergunta_natural.py

# Com debug — mostra SPARQL gerado, fonte (catálogo ou LLM), explicação
python pergunta_natural.py --debug "Quais medicamentos contêm amoxicilina?"

# Forçar nova geração ignorando o catálogo
python pergunta_natural.py --forcar-llm "..."
```

### Executar o catálogo de consultas

Depois que algumas perguntas foram feitas, o catálogo (`consultas_sparql_by_llm.json`) contém as queries SPARQL geradas. O script `consultas_sparql_by_llm.py` executa todas elas na ontologia atual:

```bash
# Listar perguntas armazenadas
python consultas_sparql_by_llm.py --listar

# Executar todas (limita a 10 resultados por query)
python consultas_sparql_by_llm.py

# Executar apenas a entrada #2
python consultas_sparql_by_llm.py --id 2

# Sem limite de resultados
python consultas_sparql_by_llm.py --limite 0
```

Esse script é o equivalente "via LLM" do `consultas_sparql.py`: enquanto aquele executa um conjunto fixo de consultas pré-definidas (estatísticas, relacionamentos básicos), este executa as queries que o LLM vai gerando conforme o uso. Os dois são complementares.

### Catálogo

Toda pergunta é salva em `consultas_sparql_by_llm.json` com:
- A query SPARQL gerada
- Uma explicação em PT do que ela faz
- Timestamp
- Se foi reuso de uma entrada anterior (`reusada_de`)

O reuso só ocorre quando os tokens-chave da pergunta (não-stopwords) são idênticos a uma entrada existente — isso evita que perguntas como "medicamentos com amoxicilina" e "medicamentos com penicilina" reusem incorretamente a mesma query.

As últimas entradas do catálogo são enviadas como few-shot examples nas próximas chamadas ao LLM, melhorando consistência ao longo do tempo.

### Exemplos de perguntas que funcionam

```
"Quais medicamentos contêm amoxicilina?"           → lista de 37 apresentações
"Com o que a varfarina interage?"                   → ibuprofeno
"Existe interação entre dipirona e ibuprofeno?"    → Não (dipirona não está na ontologia)
"tem algum remédio com dipirona aí?"                → Não
"Qual o princípio ativo da amoxicilina?"           → amoxicilina
```

---

## Tecnologias

- **OWL 2** - Web Ontology Language para modelagem
- **SPARQL** - Linguagem de consulta para RDF/OWL
- **Owlready2** - Biblioteca Python para manipulação de ontologias
- **HermiT** - Reasoner OWL para inferências
- **Claude API (Anthropic)** ou **OpenAI** - LLM para NER de fallback e classificação de intent (atualmente OpenAI)
- **rapidfuzz** - Fuzzy match para entity linking

## Referências

- Ontologia Brasileira de Medicamentos (OBM)
- W3C OWL 2 Web Ontology Language
- SPARQL 1.1 Query Language
