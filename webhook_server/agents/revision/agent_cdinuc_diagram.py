import datetime
from langchain_core.messages import SystemMessage
from langchain.prompts import ChatPromptTemplate
from app_config import llm_model, parser
from langchain_core.output_parsers import StrOutputParser
import tomllib
from pathlib import Path

# System message em inglês com orientações completas
persona_message_cdinuc_diagram = SystemMessage(
    content=(
    """
    You are a Use Case Diagram Generator agent.

    Your task is to read a Markdown table that describes the system's use cases and generate a **Use Case Diagram** using the **PlantUML** syntax.

    The Markdown table will contain the following fields for each use case:
    - **Code**: Unique code to each use case (e.g., UC01, UC02...);  
    - **Name**: The title of the use case;  
    - **Events**: The IDs of the events associated with the use case;
    - **Actors**: All relevant actors (primary and secondary);  
    - **Related Requirements**: The IDs of the requirements associated with the use case;  
    - **Classes**: Classes related to the use case.

    **Important**: Although all fields are provided in the input, your task must consider **only** the following:
    - `Code`
    - `Name`
    - `Actors`

    **Input**:
    - Markdown table with the use cases: {cdinuc_table_revised}

    ---

    **Output Instructions**:
    - Generate a **PlantUML** diagram using the `@startuml` and `@enduml` tags.
    - Represent each actor using the `actor` keyword.
    - Represent each use case using its `Code` in parentheses (e.g., `(UC01)`).
    - Connect each actor to their respective use cases using `ActorName --> (UseCaseCode)`.
    - Maintain a clean and consistent structure as in the example below.

    ---

    **Example Output**:
    @startuml

    actor Cliente
    actor Bibliotecário

    (UC01) as "Cadastrar Cliente"
    (UC02) as "Devolver Livro"

    Cliente --> (UC01)
    Bibliotecário --> (UC02)

    @enduml

    ---
    **Final Output Format**:
    - One single PlantUML code block;
    - No extra explanations or markdown sections outside the diagram;
    - If you find inconsistencies or missing information, list them after the diagram under a heading titled **Perguntas**.
    ---

    **Important**: Your entire response must be written in **Portuguese**.

    """
    ) 
)

# Prompt template
cdinuc_diagram_prompt = ChatPromptTemplate.from_messages([
    persona_message_cdinuc_diagram,
    ("human", 
    """
    Use cases table:\n\n{cdinuc_table_revised}
    """
    )
])

# Cadeia de execução do agente
agent_cdinuc_diagram_chain = cdinuc_diagram_prompt | llm_model | StrOutputParser()

# Função refinada para o nó
def cdinuc_diagram_node(state):
    print("🔍 Estado recebido no nó de geração de diagrama de casos de uso:", state)
    resultado = agent_cdinuc_diagram_chain.invoke({"cdinuc_table_revised": state["cdinuc_table_revised"]})

    return {**state, "cdinuc_diagram_revised": resultado}
