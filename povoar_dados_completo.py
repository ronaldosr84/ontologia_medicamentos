from owlready2 import *

# Carregar ontologia
onto = get_ontology("ontologia_povoada.owx").load()

with onto:
    # Referenciar classes
    Paciente = onto.search_one(iri="*Paciente")
    Medicamento = onto.search_one(iri="*Medicamento")
    PrincipioAtivo = onto.search_one(iri="*Principio_Ativo")

    print("=== CRIANDO MEDICAMENTOS E PRINCÍPIOS ATIVOS ===\n")

    # Definir medicamentos com seus princípios ativos
    medicamentos_dados = [
        ("dipirona", "dipirona"),
        ("paracetamol", "paracetamol"),
        ("amoxicilina", "penicilina"),
        ("aspirina", "acido_acetilsalicilico"),
        ("varfarina", "varfarina"),
        ("enalapril", "enalapril"),
        ("losartana", "losartana"),
        ("omeprazol", "omeprazol"),
        ("metformina", "metformina"),
        ("atorvastatina", "atorvastatina"),
        ("sinvastatina", "sinvastatina"),
        ("ibuprofeno", "ibuprofeno"),
        ("diclofenaco", "diclofenaco"),
        ("fluoxetina", "fluoxetina"),
        ("sertralina", "sertralina"),
    ]

    # Criar ou buscar medicamentos e princípios ativos
    medicamentos_criados = {}
    principios_criados = {}

    for med_nome, pa_nome in medicamentos_dados:
        # Criar/buscar princípio ativo
        pa = onto.search_one(iri=f"*{pa_nome}")
        if not pa:
            pa = PrincipioAtivo(pa_nome)
            print(f"  Criado PA: {pa_nome}")
        principios_criados[pa_nome] = pa

        # Criar/buscar medicamento
        med = onto.search_one(iri=f"*{med_nome}")
        if not med:
            med = Medicamento(med_nome)
            print(f"  Criado Med: {med_nome}")

        # Associar princípio ativo ao medicamento
        if not med.temPrincipioAtivo:
            med.temPrincipioAtivo = []
        if pa not in med.temPrincipioAtivo:
            med.temPrincipioAtivo.append(pa)

        medicamentos_criados[med_nome] = med

    print("\n=== CRIANDO INTERAÇÕES MEDICAMENTOSAS ===\n")

    # Definir interações conhecidas (PA1, PA2)
    interacoes = [
        ("varfarina", "aspirina"),  # Aumenta risco de sangramento
        ("varfarina", "acido_acetilsalicilico"),  # Mesmo caso
        ("enalapril", "losartana"),  # Duplo bloqueio SRAA
        ("atorvastatina", "sinvastatina"),  # Estatinas não devem ser combinadas
        ("fluoxetina", "sertralina"),  # ISRS não devem ser combinados
        ("ibuprofeno", "diclofenaco"),  # AINEs não devem ser combinados
        ("aspirina", "ibuprofeno"),  # Aumenta risco de sangramento
        ("varfarina", "ibuprofeno"),  # Aumenta risco de sangramento
    ]

    for pa1_nome, pa2_nome in interacoes:
        pa1 = principios_criados.get(pa1_nome)
        pa2 = principios_criados.get(pa2_nome)

        if pa1 and pa2:
            # Criar interação bidirecional
            if not pa1.interageCom:
                pa1.interageCom = []
            if pa2 not in pa1.interageCom:
                pa1.interageCom.append(pa2)

            if not pa2.interageCom:
                pa2.interageCom = []
            if pa1 not in pa2.interageCom:
                pa2.interageCom.append(pa1)

            print(f"  Interação: {pa1_nome} <-> {pa2_nome}")

    print("\n=== CRIANDO PACIENTES E CENÁRIOS ===\n")

    # CENÁRIO 1: Maria - Interação medicamentosa
    maria = Paciente("maria_silva")
    maria.usaMedicamento = [
        medicamentos_criados["varfarina"],
        medicamentos_criados["aspirina"]
    ]
    print("✓ Maria Silva:")
    print("  - Usa: Varfarina + Aspirina")
    print("  - Problema: INTERAÇÃO - Risco aumentado de sangramento")

    # CENÁRIO 2: João - Alergia
    joao = Paciente("joao_santos")
    joao.temAlergiaA = [principios_criados["penicilina"]]
    joao.usaMedicamento = [medicamentos_criados["amoxicilina"]]
    print("\n✓ João Santos:")
    print("  - Alérgico a: Penicilina")
    print("  - Usa: Amoxicilina (contém penicilina)")
    print("  - Problema: CONTRAINDICAÇÃO - Uso de medicamento com alergia")

    # CENÁRIO 3: Ana - Múltiplas interações
    ana = Paciente("ana_costa")
    ana.usaMedicamento = [
        medicamentos_criados["enalapril"],
        medicamentos_criados["losartana"],
        medicamentos_criados["ibuprofeno"]
    ]
    print("\n✓ Ana Costa:")
    print("  - Usa: Enalapril + Losartana + Ibuprofeno")
    print("  - Problema: INTERAÇÃO - Duplo bloqueio SRAA")

    # CENÁRIO 4: Carlos - Estatinas combinadas
    carlos = Paciente("carlos_oliveira")
    carlos.usaMedicamento = [
        medicamentos_criados["atorvastatina"],
        medicamentos_criados["sinvastatina"]
    ]
    print("\n✓ Carlos Oliveira:")
    print("  - Usa: Atorvastatina + Sinvastatina")
    print("  - Problema: INTERAÇÃO - Estatinas não devem ser combinadas")

    # CENÁRIO 5: Beatriz - Antidepressivos combinados
    beatriz = Paciente("beatriz_lima")
    beatriz.usaMedicamento = [
        medicamentos_criados["fluoxetina"],
        medicamentos_criados["sertralina"]
    ]
    print("\n✓ Beatriz Lima:")
    print("  - Usa: Fluoxetina + Sertralina")
    print("  - Problema: INTERAÇÃO - ISRS não devem ser combinados (Síndrome Serotoninérgica)")

    # CENÁRIO 6: Pedro - Paciente sem problemas (controle)
    pedro = Paciente("pedro_ferreira")
    pedro.usaMedicamento = [
        medicamentos_criados["metformina"],
        medicamentos_criados["omeprazol"]
    ]
    print("\n✓ Pedro Ferreira:")
    print("  - Usa: Metformina + Omeprazol")
    print("  - Status: SEM PROBLEMAS (controle)")

# Salvar ontologia
print("\n=== SALVANDO ONTOLOGIA ===")
onto.save(file="ontologia_povoada.owx", format="rdfxml")
print("\n✅ Ontologia salva com sucesso!")
print("\nAgora execute:")
print("  python detectar_contraindicacoes.py")
print("  python detectar_interacoes.py")
