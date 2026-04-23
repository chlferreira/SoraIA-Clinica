import os
from fastapi import FastAPI, Request, Form, Response
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Configurações Iniciais
load_dotenv()
app = FastAPI()

# Configuração da chave de segurança
genai.configure(api_key=os.getenv("CHAVE_MESTRA_SORAIA"))

# 2. DICIONÁRIO DE CONHECIMENTO
INFO_CLINICA = {
    "nome": "Consultório Dra. Soraya Queiroz",
    "endereco": "Shopping Tambiá, Piso E3 sala 310/311 , João Pessoa - PB",
    "horarios": "Segunda a Sexta (08h às 18h) e Sábados (08h às 12h). manhã 08h as 11h, tarde 13h as 17h e noite 17h as 18:30h.",
    "convenios": "Atendemos Unimed Odonto, Sulamerica, CLIN, Dental Center, Dental Gold, Odonto System, Hapvida e consultas particulares.",
    "especialidades": "Ortodontia(manutenção de aparelhos), Próteses, Implantes, Odontopediatria, Periodontia(tratamento de gengivas), Clareamento, Facetas e Clinica Geral(restauração, limpeza e extração).",
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
4. O processo de agendamento exige 3 informações: NOME COMPLETO, CONVÊNIO/PARTICULAR e PROCEDIMENTO. Pergunte uma coisa de cada vez e SÓ PEÇA o que o paciente ainda não informou.
5. Seja sempre educada, use emojis de forma moderada 🦷✨.
6. Nunca invente preços. Diga que a secretária passará os valores exatos após a avaliação.
7. Responda de forma curta e objetiva. Mantenha o contexto da conversa.
8. Se a mensagem do paciente estiver fora do horário de atendimento, envie uma resposta amigável explicando nossos horários.
"""

model = genai.GenerativeModel(
    model_name="models/gemini-flash-latest",
    system_instruction=SYSTEM_PROMPT
)

# DICIONÁRIO DE MEMÓRIA (Guarda o histórico de cada número de WhatsApp)
sessoes_chat = {}

# 4. ROTA DO WEBHOOK
# Adicionamos o 'From' para identificar quem está mandando a mensagem
@app.post("/webhook")
async def webhook(Body: str = Form(...), From: str = Form(...)):
    mensagem_paciente = Body.lower().strip()
    
    # COMANDO SECRETO DE DESENVOLVEDOR PARA LIMPAR A MEMÓRIA
    if mensagem_paciente == "reiniciar teste":
        if From in sessoes_chat:
            del sessoes_chat[From] # Apaga o seu histórico
        
        twiml = MessagingResponse()
        twiml.message("🔄 Memória apagada! Pode mandar um 'Oi' e serei uma nova SoraIA para você.")
        return Response(content=str(twiml), media_type="application/xml")
    
    # Lógica de Resposta Rápida (FAQ Local)
    resposta_direta = None
    if "onde fica" in mensagem_paciente or "endereço" in mensagem_paciente:
        resposta_direta = f"Ficamos localizados no {INFO_CLINICA['endereco']}. 📍"
    elif "horário" in mensagem_paciente or "aberto" in mensagem_paciente:
        resposta_direta = f"Nosso horário de atendimento é: {INFO_CLINICA['horarios']}"
    elif "convênio" in mensagem_paciente or "plano" in mensagem_paciente:
        resposta_direta = f"Atualmente {INFO_CLINICA['convenios']}. Qual seria o seu?"

    # Se não for FAQ, usa o Gemini com Memória de Sessão
    if not resposta_direta:
        try:
            # Se for a primeira vez que o número fala, cria um novo chat vazio
            if From not in sessoes_chat:
                sessoes_chat[From] = model.start_chat(history=[])
            
            # Puxa o histórico desse paciente específico
            chat = sessoes_chat[From]
            
            # Envia a mensagem continuando a conversa
            response = chat.send_message(mensagem_paciente)
            resposta_final = response.text
            
        except Exception as e:
            print(f"Erro no Gemini: {e}")
            resposta_final = "Peço desculpas, tive um probleminha técnico. Pode repetir? 😅"
    else:
        resposta_final = resposta_direta

    # Usamos Response com 'content' e 'media_type'
    twiml = MessagingResponse()
    twiml.message(resposta_final)
    
    return Response(content=str(twiml), media_type="text/xml")

# 5. EXECUÇÃO
if __name__ == "__main__":
    import uvicorn
    porta = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=porta)