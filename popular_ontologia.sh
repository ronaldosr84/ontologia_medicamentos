#!/bin/bash
# Script para popular a ontologia com dados completos

echo "=== PIPELINE DE POPULAÇÃO DA ONTOLOGIA ==="
echo ""

# Passo 1: Carregar medicamentos do CSV
echo "Passo 1: Carregando medicamentos do CSV..."
python carregar_individuos.py
if [ $? -eq 0 ]; then
    echo "✓ Medicamentos carregados com sucesso"
else
    echo "✗ Erro ao carregar medicamentos"
    exit 1
fi

echo ""

# Passo 2: Adicionar dados de exemplo (pacientes, alergias, interações)
echo "Passo 2: Adicionando dados de exemplo..."
python povoar_dados_completo.py
if [ $? -eq 0 ]; then
    echo "✓ Dados de exemplo adicionados com sucesso"
else
    echo "✗ Erro ao adicionar dados de exemplo"
    exit 1
fi

echo ""
echo "=== POPULAÇÃO CONCLUÍDA ==="
echo ""
echo "Agora você pode executar:"
echo "  python consultas_sparql.py"
echo "  python detectar_interacoes.py"
echo "  python detectar_contraindicacoes.py"
