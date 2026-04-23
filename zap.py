import os
from fastapi import FastAPI, Request, Form, Response
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Configurações Iniciais
load_dotenv()
app = FastAPI()

# Configuração da chave de segurança (CHAVE_MESTRA_SORAIA)
genai.configure(api_key=os.getenv("CHAVE_MESTRA_SORAIA"))

# 2. DICIONÁRIO DE CONHECIMENTO
INFO_CLINICA = {
    "nome": "Consultório Dra. Soraya Queiroz",
    "endereco": "Shopping Tambiá, Piso E3 sala 310/311 , João Pessoa - PB",
    "horarios": "Segunda a Sexta (08h às 18h) e Sábados (08h às 12h). manhã 08h as 11h, tarde 13h as 17h e noite 17h as 18:30h.",
    "convenios": "Atendemos Unimed Odonto, Sulamerica, CLIN, Dental Center, Dental Gold, Odonto System, Hapvida e consultas particulares.",
    "especialidades": "Ortodontia, Implantes, Clareamento, Estética e Clinica Geral.",
    "estacionamento": "O shopping possui estacionamento próprio com acesso direto ao nosso piso.",
    "instrucoes_transbordo": "Para agendar, preciso que você me diga seu nome completo e o procedimento desejado."
}

# 3. PROMPT DO SISTEMA
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
8. se estiver fora do horário de atendimento enviei uma resposta agradavel e exlicativa 
"""

# Configuração do Modelo Gemini (Ajustado com o nome exato retornado pelo Scanner)
model = genai.GenerativeModel(
    model_name="models/gemini-flash-latest",
    system_instruction=SYSTEM_PROMPT
)

# 4. ROTA DO WEBHOOK
@app.post("/webhook")
async def webhook(Body: str = Form(...)):
    # Recebe a mensagem do paciente
    mensagem_paciente = Body.lower().strip()
    
    # Lógica de Resposta Rápida (FAQ Local)
    resposta_direta = None
    
    if "onde fica" in mensagem_paciente or "endereço" in mensagem_paciente:
        resposta_direta = f"Ficamos localizados no {INFO_CLINICA['endereco']}. 📍"
    elif "horário" in mensagem_paciente or "aberto" in mensagem_paciente:
        resposta_direta = f"Nosso horário de atendimento é: {INFO_CLINICA['horarios']}"
    elif "convênio" in mensagem_paciente or "plano" in mensagem_paciente:
        resposta_direta = f"Atualmente {INFO_CLINICA['convenios']}. Qual seria o seu?"

    # Se não for FAQ, usa o Gemini
    if not resposta_direta:
        try:
            response = model.generate_content(mensagem_paciente)
            resposta_final = response.text
        except Exception as e:
            print(f"Erro no Gemini: {e}")
            resposta_final = "Peço desculpas, tive um probleminha técnico. Pode repetir? 😅"
    else:
        resposta_final = resposta_direta

    # Usamos Response com 'content' e 'media_type'
    twiml = MessagingResponse()
    twiml.message(resposta_final)
    
    return Response(content=str(twiml), media_type="application/xml")

# 5. EXECUÇÃO
if __name__ == "__main__":
    import uvicorn
    porta = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=porta)