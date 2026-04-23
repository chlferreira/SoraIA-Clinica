import os
import sys
from dotenv import load_dotenv

# Forçamos o caminho do venv apenas por segurança, já que o Windows se confundiu antes
sys.path.append(os.path.join(os.getcwd(), "venv", "Lib", "site-packages"))

try:
    from google import genai
except ImportError:
    print("Erro: Biblioteca 'google-genai' não encontrada. Rode: pip install google-genai")
    sys.exit()

# 1. Carrega as configurações do arquivo .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Erro: GEMINI_API_KEY não encontrada no arquivo .env")
    sys.exit()

# 2. Inicializa o cliente com a versão estável da API (v1)
# Isso resolve o erro 404 de 'v1beta'
client = genai.Client(
    api_key=api_key,
    http_options={'api_version': 'v1'}
)

# 3. Instruções de Comportamento (System Instruction)
INSTRUCAO = """Você é a SoraIA, assistente virtual da Clínica Soraya Queiroz, em João Pessoa.
- Localização: Shopping Tambiá.
- Convênios: Unimed Odonto, CLIN, Sulamerica.
- Objetivo: Ser cordial e focar em agendar consultas.
- Urgência: Se o paciente relatar DOR ou EMERGÊNCIA, peça para aguardar um momento pois um humano fará um encaixe imediato."""

def rodar_bot():
    print("\n" + "="*45)
    print("   SoraIA Ativa - Clínica Soraya Queiroz")
    print("   (Digite 'sair' para encerrar o chat)")
    print("="*45 + "\n")
    
    try:
        # Criamos o chat usando o modelo Flash (mais estável para plano gratuito)
        # O nome do modelo vai sem o prefixo 'models/'
        chat = client.chats.create(
            model="gemini-1.5-flash",
            config={"system_instruction": INSTRUCAO}
        )

        while True:
            user_input = input("Paciente: ")
            
            if user_input.lower() in ["sair", "parar", "tchau"]:
                print("\nSoraIA: Estarei aqui quando precisar. Tenha um ótimo dia!")
                break

            try:
                # Enviando a mensagem para o Gemini
                response = chat.send_message(user_input)
                
                if response.text:
                    print(f"\nSoraIA: {response.text}\n")
                else:
                    print("\nSoraIA: Desculpe, não consegui processar isso. Pode repetir?\n")
                    
            except Exception as e:
                # Tratamento para erro de cota (429) ou outros
                if "429" in str(e):
                    print("\n[ERRO] Cota excedida. Aguarde 30 segundos e tente novamente.\n")
                else:
                    print(f"\n[ERRO NA RESPOSTA]: {e}\n")

    except Exception as e:
        print(f"\n[ERRO AO INICIAR CHAT]: {e}")
        print("Dica: Verifique se sua chave API no .env está correta e ativa.")

if __name__ == "__main__":
    rodar_bot()