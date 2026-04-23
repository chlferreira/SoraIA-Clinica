import os
from fastapi import FastAPI, Request, Form
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Configurações Iniciais
load_dotenv()
app = FastAPI()

# Configuração da nova chave de segurança
genai.configure(api_key=os.getenv("CHAVE_MESTRA_SORAIA"))

# 2. DICIONÁRIO DE CONHECIMENTO (O "Cérebro" da Clínica)
# Mude as informações abaixo sempre que a clínica tiver novidades
INFO_CLINICA = {
    "nome": "Consultório Dra. Soraya Queiroz",
    "endereco": "Shopping Tambiá, Piso L2, João Pessoa - PB",
    "horarios": "Segunda a Sexta (08h às 18h) e Sábados (08h às 12h).",
    "convenios": "Atendemos Unimed Odonto, Sulamerica, CLIN, Dental Center, Dental Gold, Odonto System, Hapvida  e consultas particulares.",
    "especialidades": "Ortodontia, Implantes, Clareamento, Estética e Clinica Geral.",
    "estacionamento": "O shopping possui estacionamento próprio com acesso direto ao nosso piso.",
    "instrucoes_transbordo": "Para agendar, preciso que você me diga seu nome completo e o procedimento desejado."
}

# 3. PROMPT DO SISTEMA (Personalidade da SoraIA)
SYSTEM_PROMPT = f"""
Você é a SoraIA, a assistente virtual gentil e eficiente do {INFO_CLINICA['nome']}.
Seu objetivo é realizar uma triagem inicial para agendamentos.

REGRAS DE OURO:
1. Localização: {INFO_CLINICA['endereco']}.
2. Horários: {INFO_CLINICA['horarios']}.
3. Convênios: {INFO_CLINICA['convenios']}.
4. Se o cliente quiser agendar, peça o NOME COMPLETO e o CONVÊNIO/PROCEDIMENTO.
5. Seja sempre educada, use emojis de forma moderada 🦷✨.
6. Nunca invente preços. Diga que a secretária passará os valores exatos após a avaliação.
7. Responda de forma curta e objetiva.
"""

# Configuração do Modelo Gemini
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

# 4. ROTA DO WEBHOOK (Onde o WhatsApp se conecta)
@app.post("/webhook")
async def webhook(Body: str = Form(...)):
    # Recebe a mensagem do paciente
    mensagem_paciente = Body.lower().strip()
    
    # Lógica de Resposta Rápida (FAQ Local - Economiza API)
    resposta_direta = None
    
    if "onde fica" in mensagem_paciente or "endereço" in mensagem_paciente:
        resposta_direta = f"Ficamos localizados no {INFO_CLINICA['endereco']}. 📍"
    elif "horário" in mensagem_paciente or "aberto" in mensagem_paciente:
        resposta_direta = f"Nosso horário de atendimento é: {INFO_CLINICA['horarios']}"
    elif "convênio" in mensagem_paciente or "plano" in mensagem_paciente:
        resposta_direta = f"Atualmente {INFO_CLINICA['convenios']}. Qual seria o seu?"

    # Se não for uma pergunta de FAQ, usa a inteligência do Gemini
    if not resposta_direta:
        try:
            response = model.generate_content(mensagem_paciente)
            resposta_final = response.text
        except Exception as e:
            print(f"Erro no Gemini: {e}")
            resposta_final = "Peço desculpas, tive um probleminha técnico. Pode repetir? 😅"
    else:
        resposta_final = resposta_direta

    # Resposta formatada para o Twilio/WhatsApp
    twiml = MessagingResponse()
    twiml.message(resposta_final)
    
    return Request(status_code=200, content=str(twiml), media_type="application/xml")

# 5. EXECUÇÃO DO SERVIDOR (Ajustado para o Render)
if __name__ == "__main__":
    import uvicorn
    porta = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=porta)