import datetime
from langchain_core.messages import SystemMessage
from langchain.prompts import ChatPromptTemplate
from webhook_server.app_config import get_llm_model, parser
from langchain_core.output_parsers import StrOutputParser
import tomllib
from pathlib import Path

# System message em inglês com orientações completas
persona_message_cdinuc_diagram = SystemMessage(
    content=(
    """
    You are a Use Case Diagram Generator.
    Your task is to read a Markdown table of use cases and generate a **PlantUML** use case diagram.

    Although the table contains the following fields: Code, Name, Actors, Events, Related Requirements, Preconditions, and Classes — consider **only**:
    - Code
    - Name
    - Actors

    **Output Format**:
    - First, start with a PlantUML code block using triple backticks and `plantuml`;
    - After, use `@startuml` to `@enduml` and finish the PlantUML diagram with triple backticks;
    - One `actor` declaration for each actor;
    - One `(Code)` declaration for each use case, optionally using `as "Name"` for clarity;
    - Use `Actor -- (UseCase)` to show relationships;
    - Do **not** add include/extend relationships unless explicitly instructed;
    - If you find inconsistencies or missing data, list them below the diagram under a heading called **Questions and Validations**.

    **Important**: Your entire response must be written in the language of the previous texts.
    """
    ) #**Important**: The entire response must be in the language of the previous texts.
)

# Prompt template
cdinuc_diagram_prompt = ChatPromptTemplate.from_messages([
    persona_message_cdinuc_diagram,
    ("human", 
    """
    You are a Use Case Diagram Generator agent.

    Your task is to read a Markdown table that describes the system's use cases and generate a **Use Case Diagram** using the **PlantUML** syntax.

    The Markdown table will contain the following fields for each use case:
    - **Code**: A unique identifier for the use case (e.g., UC01, UC02);
    - **Name**: The title of the use case (e.g., Cadastrar Cliente);
    - **Actors**: One or more relevant actors (primary or secondary) who participate in the use case;
    - **Events**: A summarized version of the main steps from the normal flow;
    - **Related Requirements**: List of requirement IDs related to the use case;
    - **Preconditions**: Conditions that must be met before the use case starts;
    - **Classes**: Any listed classes .

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
    - Do **not** infer or generate include/extend relationships unless explicitly present in the data.
    - Maintain a clean and consistent structure as in the example below.

    ---

    **Example Output**:
    ### Use Case Diagram (the title must be written in the language of the use cases and class diagram)

    ```plantuml
    @startuml

    actor Cliente
    actor Bibliotecário

    (UC01) as "Cadastrar Cliente"
    (UC02) as "Devolver Livro"

    Cliente -- (UC01)
    Bibliotecário -- (UC02)

    @enduml
    ```

    ---
    **Final Output Format**:
    - One single PlantUML code block;
    - No extra explanations or markdown sections outside the diagram;
    - Do not include additional comments or sections outside the diagram.
    ---

    **Important**: Your entire response must be written in the language of the use cases and class diagram. All use case content, section titles, descriptions, and any additional text must be written in that same language.
    """
    )
])

# Função refinada para o nó
def cdinuc_diagram_node(state):
    print("🔍 Estado recebido no nó de geração de diagrama de casos de uso:", state)

    # Cadeia de execução do agente
    agent_cdinuc_diagram_chain = cdinuc_diagram_prompt | get_llm_model(state["api_key"]) | StrOutputParser()

    resultado = agent_cdinuc_diagram_chain.invoke({"cdinuc_table_revised": state["cdinuc_table_revised"]})

    return {**state, "cdinuc_diagram_revised": resultado}
