import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Mantenha o nome esperado: llm_model
# llm_model = ChatGoogleGenerativeAI(
#     model="gemini-3-flash-preview",
#     temperature=0,
#     api_key=GEMINI_API_KEY
# )

def get_llm_model(api_key: str):
  return ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        temperature=0,
        api_key=api_key
    )

# Mantenha o nome esperado: parser
parser = StrOutputParser()
