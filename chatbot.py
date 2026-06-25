#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chatbot_simples.py
Tutorial de chatbots em Python com 3 variações:
    1. Chatbot de regras (if/elif) - sem dependências externas
    2. Chatbot com regex - reconhecimento de padrões flexíveis
    3. Chatbot com NLTK - processamento básico de linguagem natural

Execute o script e escolha a variação desejada no menu principal.
Para sair de qualquer chatbot, digite "sair".
"""

import re
import sys


# ============================================================================
# VARIAÇÃO 1: CHATBOT DE REGRAS (if/elif)
# ============================================================================
# O chatbot mais simples possível: compara a entrada do usuário com palavras
# pré-definidas usando comandos if/elif. Não requer bibliotecas externas.
# ============================================================================

class ChatbotRegras:
    """Chatbot baseado em regras fixas usando if/elif."""

    def __init__(self):
        self.nome = "BotMedicamentos"

    def responder(self, mensagem: str) -> str:
        """
        Gera uma resposta com base em regras de texto exato ou substrings.

        Args:
            mensagem: Texto digitado pelo usuário.

        Returns:
            Resposta adequada ou mensagem padrão de não entendimento.
        """
        # Normaliza a mensagem para comparação em minúsculas
        texto = mensagem.strip().lower()

        if not texto:
            return "Você não digitou nada. Pode repetir?"

        if texto in ("oi", "olá", "ola", "eae", "bom dia", "boa tarde", "boa noite"):
            return "Olá! Como posso ajudar você hoje?"

        elif "nome" in texto:
            return f"Meu nome é {self.nome}. E o seu?"

        elif "tempo" in texto or "clima" in texto:
            return "Não tenho acesso à previsão do tempo, mas espero que esteja agradável!"

        elif "hora" in texto or "horas" in texto:
            from datetime import datetime
            agora = datetime.now().strftime("%H:%M")
            return f"Agora são {agora}."

        elif "ajuda" in texto or "help" in texto:
            return "Posso conversar sobre: cumprimentos, nome, clima, hora e despedida."

        elif texto in ("tchau", "adeus", "até logo", "ate logo", "xau", "valeu"):
            return "Até logo! Volte sempre."

        else:
            return "Desculpe, não entendi. Tente perguntar sobre nome, clima, hora ou ajuda."

    def iniciar(self):
        """Inicia o loop de conversa do chatbot de regras."""
        print("=" * 50)
        print(f"Bem-vindo ao {self.nome}!")
        print("Vou te ajudar a descobrir informações sobre medicamentos e interações.")
        print("Por favor, digite o seu nome para começarmos.")
        print("Digite 'sair' a qualquer momento para encerrar.")
        print("=" * 50)

        entrada = input("\nNome: ").strip()
        
        while(not entrada):
            print(f"{self.nome}: Você não digitou nada. Por favor, digite seu nome. ou sair para encerrar.")
            entrada = input("\nNome: ").strip()
            if(entrada.lower() == "sair"):
                print(f"{self.nome}: Até logo!")
                sys.exit(0)
        
        print(f"{self.nome}: Seja-bem vindo, {entrada}! Localizei você na minha base de dados.")
        
        print(f"{self.nome}: Atualmente você toma os medicamentos: Dipirona, Paracetamol e Amoxicilina.")
        
        print(f"{self.nome}: Como posso te ajudar hoje?")
        
        entrada = input(f"\n{entrada}: ").strip()
        

        


        """while True:
            try:
                entrada = input("\nVocê: ").strip()

                if entrada.lower() == "sair":
                    print(f"{self.nome}: Até logo!")
                    break

                resposta = self.responder(entrada)
                print(f"{self.nome}: {resposta}")

            except KeyboardInterrupt:
                print(f"\n{self.nome}: Conversa interrompida. Até logo!")
                break
            except Exception as erro:
                print(f"{self.nome}: Ocorreu um erro inesperado: {erro}")"""


# ============================================================================
# VARIAÇÃO 2: CHATBOT COM REGEX
# ============================================================================
# Utiliza expressões regulares para identificar padrões mais flexíveis na
# entrada do usuário, permitindo variações de escrita e frases mais naturais.
# ============================================================================

class ChatbotRegex:
    """Chatbot que utiliza expressões regulares para reconhecer padrões."""

    def __init__(self):
        self.nome = "BotRegex"
        # Lista de padrões (regex, resposta). Procure padrões da mais específica
        # para a mais genérica para evitar correspondências incorretas.
        self.padroes = [
            (r"\b(oi|olá|ola|eae|bom dia|boa tarde|boa noite)\b", "Olá! Em que posso ajudar?"),
            (r"\b(quem é você|qual seu nome|seu nome|como se chama)\b", f"Meu nome é {self.nome}, seu assistente virtual."),
            (r"\b(temperatura|clima|tempo)\b", "Não tenho acesso ao tempo, mas espero que esteja bom!"),
            (r"\b(que horas são|horas|hora)\b", self._responder_hora),
            (r"\b(ajuda|help|socorro)\b", "Pergunte sobre mim, clima, hora ou diga tchau."),
            (r"\b(obrigado|obrigada|valeu|agradecido)\b", "Por nada! Estou aqui para ajudar."),
            (r"\b(tchau|adeus|até logo|ate logo|xau|falou)\b", "Até logo! Cuide-se."),
        ]

    def _responder_hora(self, _) -> str:
        """Retorna a hora atual formatada."""
        from datetime import datetime
        agora = datetime.now().strftime("%H:%M")
        return f"São {agora}."

    def responder(self, mensagem: str) -> str:
        """
        Procura padrões de regex na mensagem e retorna a resposta associada.

        Args:
            mensagem: Texto digitado pelo usuário.

        Returns:
            Resposta correspondente ao primeiro padrão encontrado.
        """
        texto = mensagem.strip().lower()

        if not texto:
            return "Você não digitou nada. Pode repetir?"

        for padrao, resposta in self.padroes:
            if re.search(padrao, texto):
                # Se a resposta for uma função, chama-a com a correspondência
                if callable(resposta):
                    return resposta(None)
                return resposta

        return "Não entendi bem. Tente perguntar de outra forma sobre clima, hora ou meu nome."

    def iniciar(self):
        """Inicia o loop de conversa do chatbot com regex."""
        print("=" * 50)
        print(f"Bem-vindo ao {self.nome}!")
        print("Digite 'sair' a qualquer momento para encerrar.")
        print("=" * 50)

        while True:
            try:
                entrada = input("\nVocê: ").strip()

                if entrada.lower() == "sair":
                    print(f"{self.nome}: Até logo!")
                    break

                resposta = self.responder(entrada)
                print(f"{self.nome}: {resposta}")

            except KeyboardInterrupt:
                print(f"\n{self.nome}: Conversa interrompida. Até logo!")
                break
            except Exception as erro:
                print(f"{self.nome}: Ocorreu um erro inesperado: {erro}")


# ============================================================================
# VARIAÇÃO 3: CHATBOT COM NLTK
# ============================================================================
# Utiliza a biblioteca NLTK para tokenização básica e remoção de stopwords,
# permitindo identificar a intenção do usuário mesmo em frases mais longas.
# Requer instalação: pip install nltk
# ============================================================================

class ChatbotNLTK:
    """Chatbot com processamento básico de linguagem natural usando NLTK."""

    def __init__(self):
        self.nome = "BotNLTK"
        self._carregar_nltk()

        # Mapeamento de intenções para palavras-chave representativas
        self.intencoes = {
            "saudacao": ["oi", "olá", "ola", "eae", "bom", "dia", "tarde", "noite"],
            "nome": ["nome", "chama", "quem", "você"],
            "clima": ["tempo", "clima", "temperatura", "chuva", "sol"],
            "hora": ["hora", "horas", "que horas"],
            "ajuda": ["ajuda", "help", "socorro", "ajudar"],
            "despedida": ["tchau", "adeus", "xau", "logo", "falou"],
            "agradecimento": ["obrigado", "obrigada", "valeu", "agradecido"],
        }

        # Respostas para cada intenção
        self.respostas = {
            "saudacao": "Olá! Como posso ajudar?",
            "nome": f"Eu sou o {self.nome}, seu assistente de conversação.",
            "clima": "Infelizmente não acesso dados meteorológicos. Espero que esteja bom!",
            "hora": self._responder_hora,
            "ajuda": "Posso conversar sobre saudações, meu nome, clima, hora e despedida.",
            "despedida": "Até logo! Foi um prazer conversar.",
            "agradecimento": "De nada! Sempre que precisar, estou por aqui.",
        }

    def _carregar_nltk(self):
        """
        Tenta importar e baixar os recursos necessários do NLTK.
        Levanta um erro informativo caso a biblioteca não esteja instalada.
        """
        try:
            import nltk
            # Recursos necessários para tokenização e stopwords
            nltk.download("punkt", quiet=True)
            nltk.download("stopwords", quiet=True)

            from nltk.corpus import stopwords
            from nltk.tokenize import word_tokenize

            self.tokenize = word_tokenize
            self.stopwords = set(stopwords.words("portuguese"))
        except ImportError:
            raise ImportError(
                "A biblioteca NLTK não está instalada. "
                "Instale com: pip install nltk"
            )
        except Exception as erro:
            raise RuntimeError(f"Erro ao carregar recursos do NLTK: {erro}")

    def _responder_hora(self) -> str:
        """Retorna a hora atual formatada."""
        from datetime import datetime
        agora = datetime.now().strftime("%H:%M")
        return f"Agora são {agora}."

    def _extrair_intencao(self, mensagem: str) -> str:
        """
        Tokeniza a mensagem, remove stopwords e identifica a intenção do usuário.

        Args:
            mensagem: Texto digitado pelo usuário.

        Returns:
            Nome da intenção detectada ou "desconhecida".
        """
        # Tokeniza e normaliza para minúsculas
        tokens = self.tokenize(mensagem.lower())

        # Remove stopwords e pontuações, mantendo apenas palavras alfabéticas
        tokens_limpios = [
            token for token in tokens
            if token.isalpha() and token not in self.stopwords
        ]

        # Conta quantas palavras-chave de cada intenção aparecem na mensagem
        pontuacao = {}
        for intencao, palavras_chave in self.intencoes.items():
            pontuacao[intencao] = sum(1 for palavra in palavras_chave if palavra in tokens_limpios)

        # Seleciona a intenção com maior pontuação
        if pontuacao and max(pontuacao.values()) > 0:
            return max(pontuacao, key=pontuacao.get)

        return "desconhecida"

    def responder(self, mensagem: str) -> str:
        """
        Processa a mensagem e retorna uma resposta natural.

        Args:
            mensagem: Texto digitado pelo usuário.

        Returns:
            Resposta apropriada à intenção identificada.
        """
        texto = mensagem.strip()

        if not texto:
            return "Você não digitou nada. Pode repetir?"

        intencao = self._extrair_intencao(texto)

        if intencao == "desconhecida":
            return "Não entendi muito bem. Tente perguntar sobre clima, hora ou meu nome."

        resposta = self.respostas[intencao]
        if callable(resposta):
            return resposta()
        return resposta

    def iniciar(self):
        """Inicia o loop de conversa do chatbot com NLTK."""
        print("=" * 50)
        print(f"Bem-vindo ao {self.nome}!")
        print("Digite 'sair' a qualquer momento para encerrar.")
        print("=" * 50)

        while True:
            try:
                entrada = input("\nVocê: ").strip()

                if entrada.lower() == "sair":
                    print(f"{self.nome}: Até logo!")
                    break

                resposta = self.responder(entrada)
                print(f"{self.nome}: {resposta}")

            except KeyboardInterrupt:
                print(f"\n{self.nome}: Conversa interrompida. Até logo!")
                break
            except Exception as erro:
                print(f"{self.nome}: Ocorreu um erro inesperado: {erro}")


# ============================================================================
# MENU PRINCIPAL
# ============================================================================

def exibir_menu():
    """Exibe o menu de seleção de chatbots."""
    print("\n" + "=" * 50)
    print("TUTORIAL DE CHATBOTS SIMPLES EM PYTHON")
    print("=" * 50)
    print("Escolha uma variação:")
    print("  1 - Chatbot de Regras (if/elif)")
    print("  2 - Chatbot com Regex")
    print("  3 - Chatbot com NLTK")
    print("  0 - Sair do programa")
    print("=" * 50)


def main():
    """
    Função principal que apresenta o menu e executa a variação escolhida.
    """
    while True:
        exibir_menu()
        try:
            opcao = input("Digite o número da opção desejada: ").strip()

            if opcao == "0":
                print("Programa encerrado. Até logo!")
                break
            elif opcao == "1":
                chatbot = ChatbotRegras()
                chatbot.iniciar()
            elif opcao == "2":
                chatbot = ChatbotRegex()
                chatbot.iniciar()
            elif opcao == "3":
                try:
                    chatbot = ChatbotNLTK()
                    chatbot.iniciar()
                except ImportError as erro:
                    print(f"\nErro: {erro}")
                    print("Deseja instalar? Execute: pip install nltk\n")
                except Exception as erro:
                    print(f"\nErro ao iniciar chatbot NLTK: {erro}\n")
            else:
                print("Opção inválida. Por favor, escolha 1, 2, 3 ou 0.")

        except KeyboardInterrupt:
            print("\nPrograma interrompido pelo usuário. Até logo!")
            break
        except Exception as erro:
            print(f"Ocorreu um erro inesperado no menu: {erro}")


if __name__ == "__main__":
    main()