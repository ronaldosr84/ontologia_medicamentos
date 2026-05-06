from owlready2 import *

# Carregar ontologia povoada
onto = get_ontology("ontologia_povoada.owx").load()

with onto:
    # Referenciar classes
    Paciente = onto.search_one(iri="*Paciente")
    Medicamento = onto.search_one(iri="*Medicamento")
    PrincipioAtivo = onto.search_one(iri="*Principio_Ativo")

    # Referenciar propriedades
    usaMedicamento = onto.search_one(iri="*usaMedicamento")
    temAlergiaA = onto.search_one(iri="*temAlergiaA")
    interageCom = onto.search_one(iri="*interageCom")
    temPrincipioAtivo = onto.search_one(iri="*temPrincipioAtivo")

    print("Criando pacientes de exemplo...")

    # Criar pacientes
    maria = Paciente("maria_silva")
    joao = Paciente("joao_santos")
    ana = Paciente("ana_costa")

    # Buscar medicamentos e princípios ativos existentes
    print("Buscando medicamentos existentes...")

    # Exemplo 1: Maria usa Dipirona e Paracetamol (podem ter interação com álcool)
    dipirona = onto.search_one(iri="*dipirona")
    paracetamol = onto.search_one(iri="*paracetamol")

    if dipirona and paracetamol:
        maria.usaMedicamento = [dipirona, paracetamol]
        print(f"  Maria usa: Dipirona e Paracetamol")

    # Exemplo 2: João é alérgico a penicilina mas vamos adicionar amoxicilina
    amoxicilina = onto.search_one(iri="*amoxicilina")

    # Buscar ou criar penicilina como princípio ativo
    penicilina_pa = None
    for pa in PrincipioAtivo.instances():
        if "penicilina" in pa.name.lower():
            penicilina_pa = pa
            break

    if not penicilina_pa:
        penicilina_pa = PrincipioAtivo("penicilina")

    if amoxicilina:
        # Associar penicilina como princípio ativo da amoxicilina se ainda não estiver
        if not amoxicilina.temPrincipioAtivo:
            amoxicilina.temPrincipioAtivo = []
        if penicilina_pa not in amoxicilina.temPrincipioAtivo:
            amoxicilina.temPrincipioAtivo.append(penicilina_pa)

        # João é alérgico a penicilina
        joao.temAlergiaA = [penicilina_pa]
        # E está usando amoxicilina (que contém penicilina) - ALERTA!
        joao.usaMedicamento = [amoxicilina]
        print(f"  João é alérgico a penicilina e usa amoxicilina - CONTRAINDICAÇÃO!")

    # Exemplo 3: Ana usa medicamentos que interagem entre si
    # Vamos buscar alguns medicamentos comuns
    atorvastatina = onto.search_one(iri="*atorvastatina")
    sinvastatina = onto.search_one(iri="*sinvastatina")

    if atorvastatina and sinvastatina:
        ana.usaMedicamento = [atorvastatina, sinvastatina]

        # Criar interação entre os princípios ativos
        pa_atorva = atorvastatina.temPrincipioAtivo[0] if atorvastatina.temPrincipioAtivo else None
        pa_sinva = sinvastatina.temPrincipioAtivo[0] if sinvastatina.temPrincipioAtivo else None

        if pa_atorva and pa_sinva:
            # Estatinas não devem ser combinadas
            if not pa_atorva.interageCom:
                pa_atorva.interageCom = []
            if pa_sinva not in pa_atorva.interageCom:
                pa_atorva.interageCom.append(pa_sinva)

            if not pa_sinva.interageCom:
                pa_sinva.interageCom = []
            if pa_atorva not in pa_sinva.interageCom:
                pa_sinva.interageCom.append(pa_atorva)

            print(f"  Ana usa Atorvastatina e Sinvastatina - INTERAÇÃO!")

    # Adicionar mais interações conhecidas
    print("\nAdicionando interações medicamentosas conhecidas...")

    # Warfarina interage com muitos medicamentos
    warfarina = onto.search_one(iri="*varfarina") or onto.search_one(iri="*warfarina")
    aspirina = onto.search_one(iri="*aspirina") or onto.search_one(iri="*acido_acetilsalicilico")

    if warfarina and aspirina:
        pa_warf = warfarina.temPrincipioAtivo[0] if warfarina.temPrincipioAtivo else None
        pa_asp = aspirina.temPrincipioAtivo[0] if aspirina.temPrincipioAtivo else None

        if pa_warf and pa_asp:
            if not pa_warf.interageCom:
                pa_warf.interageCom = []
            if pa_asp not in pa_warf.interageCom:
                pa_warf.interageCom.append(pa_asp)

            if not pa_asp.interageCom:
                pa_asp.interageCom = []
            if pa_warf not in pa_asp.interageCom:
                pa_asp.interageCom.append(pa_warf)

            print(f"  Adicionada interação: Warfarina <-> Aspirina")

# Salvar ontologia com os dados de exemplo
print("\nSalvando ontologia com dados de exemplo...")
onto.save(file="ontologia_povoada.owx", format="rdfxml")
print("Concluído! Execute novamente os scripts de detecção.")
