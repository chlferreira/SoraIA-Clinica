import os
from fastapi import FastAPI, Form, Response
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai

# 1. Configuração de Ambiente
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Nova Instrução de Sistema refinada para os períodos e convênios
INSTRUCAO = """Você é a SoraIA, assistente da Clínica Soraya Queiroz (Shopping Tambiá).
Sua missão é realizar a triagem inicial para agendamento.

REGRAS DE ATENDIMENTO:
1. Horários: Não use horas exatas. Ofereça apenas os períodos: MANHÃ, TARDE ou NOITE.
2. Convênios: Pergunte obrigatoriamente se o atendimento é PARTICULAR ou por PLANO DE SAÚDE.
3. Se for PLANO, pergunte qual é o nome do plano (Aceitamos: Unimed Odonto, CLIN, Sulamerica, Dental Center, Dental Gold, Hapvida, Odonto System).
4. Dados Necessários: Você deve coletar Nome Completo, Telefone, Período preferido e Tipo de Atendimento (Particular ou Plano).
5. Tom de Voz: Profissional, acolhedor e direto.

FLUXO FINAL:
- Quando você tiver TODAS as informações acima, agradeça e diga que "A equipe de atendimento entrará em contato em breve para confirmar o horário".
- Não tente agendar o minuto exato, deixe isso para os humanos após a triagem."""

# 2. Inicializa o modelo (Usando o 2.5-flash que seu scanner confirmou)
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=INSTRUCAO,
    generation_config={"temperature": 0.3}
)

chats_ativos = {}

app = FastAPI(title="SoraIA Pro")

@app.post("/webhook")
async def twilio_webhook(From: str = Form(...), Body: str = Form(...)):
    telefone_paciente = From.replace("whatsapp:", "")
    texto_paciente = Body
    
    if telefone_paciente not in chats_ativos:
        chats_ativos[telefone_paciente] = model.start_chat(history=[])
    
    try:
        resposta = chats_ativos[telefone_paciente].send_message(texto_paciente)
        texto_resposta = resposta.text
        
        # LÓGICA DE NOTIFICAÇÃO (Simulação de entrega para atendentes)
        # Como engenheiro, você pode expandir isso para salvar em um banco ou enviar um e-mail
        if "entrará em contato em breve" in texto_resposta.lower():
            print(f"\n--- NOTIFICAÇÃO PARA ATENDENTES ---")
            print(f"Paciente: {telefone_paciente} finalizou a triagem.")
            print(f"Resumo da Conversa: {chats_ativos[telefone_paciente].history[-2:]}")
            print(f"------------------------------------\n")

    except Exception as e:
        print(f"Erro no Gemini: {e}")
        texto_resposta = "Desculpe, tive um problema técnico. Poderia repetir?"
    
    twiml_response = MessagingResponse()
    twiml_response.message(texto_resposta)
    
    return Response(content=str(twiml_response), media_type="application/xml")

if __name__ == "__main__":
    import uvicorn
    import os
    # O Render exige que leiamos a porta da variável de ambiente PORT
    porta = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=porta)