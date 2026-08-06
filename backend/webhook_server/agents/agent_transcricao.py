from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
#from RequirementsAI.webhook_server.app_config import llm_model  # Seu modelo Gemini ou outro
# from webhook_server.app_config import llm_model, parser
import google.generativeai as genai
import tomllib
from pathlib import Path

import os

# Prompt do agente de transcrição
persona_message_transcricao = SystemMessage(
    content=(
        "You are an expert in interview transcription.\n"
        "Your task is to listen to the audio and generate an accurate transcription, including timestamps every 30 seconds.\n"
        "Identify different speakers if necessary and provide the transcription in the same language spoken in the audio."
    )
)

# Node 0: Transcribe audio with Gemini API
def transcribe_audio_agent(inputs):
    audio_file_path = inputs["video_entrevista"]
    genai.configure(api_key=inputs["api_key"])
    model_gemini = genai.GenerativeModel("gemini-3-flash-preview")
    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"Arquivo de áudio não encontrado: {audio_file_path}")
    
    try:

        with open(audio_file_path, 'rb') as f:
            audio_data = f.read()

        prompt = """
        Please provide a complete and accurate transcription of this audio.
        Include timestamp markings every 30 seconds, if possible.
        Identify different speakers if there are multiple people speaking.
        """

        response = model_gemini.generate_content([
            {"mime_type": "audio/mp3", "data": audio_data}, prompt
        ])

        print("🎙️ Resultado da transcrição:", response.text)
        print("📦 Estado retornado:", {**inputs, "transcricao": response.text})
        return {**inputs, "transcricao": response.text}

    except Exception as e:
        raise RuntimeError(f"Erro ao transcrever áudio: {str(e)}")
        sys.exit(1)