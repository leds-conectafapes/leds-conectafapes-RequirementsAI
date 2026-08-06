import datetime
from langchain_core.messages import SystemMessage
from langchain.prompts import ChatPromptTemplate
from webhook_server.app_config import get_llm_model, parser
from langchain_core.output_parsers import StrOutputParser
import tomllib
from pathlib import Path

# System message em inglês com orientações completas
persona_message_refinamento = SystemMessage(
    content=(
    """You are a requirements refiner.
    Your task is to generate the final version of the 3 requirements tables (FRs, BRs, NFRs) in Markdown format.
    Include final doubts at the end, if any inconsistencies remain.
    
    **Response Format**:
    - Markdown;
    - Three tables: Functional Requirements (FRs), Business Rules (BRs), Non-Functional Requirements (NFRs);
    - A 'Questions and Validations' block at the end, if applicable.

    **IMPORTANT**: Your response must be in the language of the provided domain narrative. All table content, descriptions, and any additional text must be written in that same language.
    """
    )
)

# Prompt template
refinamento_prompt = ChatPromptTemplate.from_messages([
    persona_message_refinamento,
    ("human", 
     """

     Below are the prioritized requirements:

    {requisitos_priorizados}

    **Objective**: Generate a final version of the requirements in 3 tables (FRs, BRs, NFRs), in the following format (example):
    ```
    ## Functional Requirements Table (FRs)
    | ID    | Description                                                    | Priority   | Related Requirements     |
    |-------|----------------------------------------------------------------|------------|--------------------------|
    | FR001 | The system must allow user registration.                      | High       | FR002                    |
    ...
    ```
    and so on for BRs and NFRs.

    **Also include at the end**:
    - Questions or doubts if there are still inconsistencies;
    - Final remarks for the user.

    **Response Format**:  
    - In Markdown;
    - Three tables (FR, BR, NFR);
    - After the tables, include a "Questions and Validations" block if applicable.

    Generate only this. Avoid repetitions.

    **Important**:
    - Your entire response must be written in the language of the provided domain narrative.
    - Do not include any additional commentaries before the presentation of the requirements.
    - The only other content allowed is the "Questions and Validations" section at the end.
    """
    )
])

# Função refinada para o nó
def refine_node(state):    
    print("🔍 Estado recebido no nó de refinamento:", state)

    # Cadeia de execução do agente
    agent_refinamento_chain = refinamento_prompt | get_llm_model(state["api_key"]) | StrOutputParser()

    resultado = agent_refinamento_chain.invoke({"requisitos_priorizados": state["requisitos_priorizados"]})

    return {**state, "report": resultado}