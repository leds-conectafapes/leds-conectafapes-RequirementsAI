from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from langchain.prompts import ChatPromptTemplate
#from RequirementsAI.webhook_server.app_config import llm_model
from webhook_server.app_config import get_llm_model, parser
import datetime
from langchain_core.output_parsers import StrOutputParser
import tomllib
from pathlib import Path

# Prompt do agente de geração de minimundo
persona_message_minimundo = SystemMessage(
    content=(
    "You are a requirements engineer specializing in transforming transcripts into mini-worlds.\n"
    "Your mission is to create a clear and accurate domain narrative based on the provided transcript, in the audio language."
    )
)

minimundo_prompt = ChatPromptTemplate.from_messages([
    persona_message_minimundo,
    ("human", """
    You are a requirements engineering expert.

    Your goal is to create a relevant domain narrative based on the transcription and using an old version of the domain narrative below the transcription.
    **Important:**
    - If the old domain narrative is empty, treat your output as the first version of the domain narrative.
    - If the old domain narrative exists, follow its instructions using its informations and the informations of the given transcription

    Transcription:
    {transcricao}
    
    Old Domain Narrative Instruction:
    {mw_instruction}
    
    Old Domain Narrative (may be empty):
    {old_mw}
    
    Instructions:
    - The domain narrative based on the transcription should be clear, concise, and reflect the user's needs.
    - The domain narrative based on the transcription should contain relevant information for requirements analysis.
    - The domain narrative based on the transcription should be structured to facilitate the identification of functional and non-functional requirements.
    - The domain narrative based on the transcription should include details about the context, users, and expected system functionalities.
    - The domain narrative based on the transcription should be written in natural language, avoiding technical jargon.
    - The domain narrative based on the transcription should be logically organized, with distinct sections for different aspects of the system.
    - The domain narrative based on the transcription should be reviewed to ensure clarity and accuracy.
    - The domain narrative based on the transcription should be presented in a way that facilitates reading and understanding.
    - The domain narrative based on the transcription should be written in the audio language.
    - Do not include any additional commentaries at the beginning of the domain narrative.
    - If you identify any inconsistencies or missing information in the transcription, explicitly list them at the end of the domain narrative in a section called 'Questions and Validations' and suggest specific questions to ask the user for clarification.
    """)
])

# agent_minimundo_chain = minimundo_prompt | llm_model | StrOutputParser()

def generate_minimundo_node(state):
    """
    Step 0:
    - Transcription of the domain narrative.
    """

    agent_minimundo_chain = minimundo_prompt | get_llm_model(state["api_key"]) | StrOutputParser()

    resultado = agent_minimundo_chain.invoke({"transcricao": state["transcricao"], "mw_instruction": "", "old_mw":""})
    print("📚 Minimundo gerado:", resultado)

    return {**state, "minimundo": resultado}