from langchain_core.messages import SystemMessage
from langchain.prompts import ChatPromptTemplate
from webhook_server.app_config import get_llm_model, parser
from langchain_core.output_parsers import StrOutputParser

# System message em inglês com orientações completas
persona_message_validateuc = SystemMessage(
    content=(
    """
    You are a Use Case Validation Agent.  
    Your task is to review and correct use case descriptions using the refined requirements and the domain description.

    **Response Format**:
    - Plain text;
    - For each use case: Name, Actors, Preconditions, Normal Flow of Events, Alternative / Exception Flows, Related Requirements, and Classes;
    - A "Questions and Validations" block at the end, with doubts, assumptions, or inconsistencies.
    - Do not include additional comments in the contents of the generated documents, except in the "Questions and Validations" section at the end.

    **Important**: Your entire response must be written in the language of the provided domain narrative and requirements. All use case content, section titles, descriptions, and any additional text must be written in that same language.
    """
    ) #**Important**: The entire response must be in the language of the previous texts.
)

# Prompt template
validateuc_prompt = ChatPromptTemplate.from_messages([
    persona_message_validateuc,
    ("human", 
    """
    You are a **Use Case Validation Agent**.  
    Your task is to review and validate a list of use cases, ensuring consistency, correctness, and alignment with the refined requirements and the project’s domain description.

    You will receive:  
    - A list of use cases, each with: Name, Actors, Preconditions, Normal Flow of Events, Alternative / Exception Flows, Related Requirements, and Classes (which may be empty): {ident_events};  
    - A refined version of the system's requirements: {report};  
    - A domain description (minimundo) that explains the context of the system: {minimundo}.

    ---

    **Your Objective**:  
    - Carefully analyze each use case and verify if:  
    1. The **flow of events** aligns with the system’s goals and logic;  
    2. The **actors** make sense considering the system boundary and the description of the domain;  
    3. The **preconditions** are meaningful and necessary;  
    4. The **related requirements** listed are appropriate and relevant;  
    5. There are no **missing or redundant cases**;  
    6. No essential behavior described in the refined requirements or minimundo was left unmodeled.  

    If you find inconsistencies, fix them directly in the use case descriptions. If the information is ambiguous or insufficient, flag it in the "Questions and Validations" section at the end.

    ---

    **Output Format**:  
    - **Markdown** document;  
    - Return the complete revised list of use cases with all fields (not including Classes, leave it empty);
    - Format your list as the example below  
    - Add a final section titled **Questions and Validations** with any doubts, inconsistencies, or assumptions made.

    <DESIRED OUTPUT EXAMPLE>
    ## Use Cases Description
    - **Name:** User Login  
    - **Actors:**  
        - User  
        - System  
    - **Preconditions:**  
        - The user must be registered  
    - **Normal Flow of Events:**  
        - User navigates to the login page  
        - Enters email and password  
        - Clicks "Login"  
        - System validates credentials  
        - User is redirected to the homepage  
    - **Alternative / Exception Flows:**  
        - Invalid credentials → System displays an error message  
        - Missing fields → System prompts for required input  
    - **Related Requirements:**  
        - RF01  
    - **Classes:**    

    ## Questions and Validations

    1. What are the different types of users that need access to the system, and do they require different authentication mechanisms (e.g., two-factor authentication, SSO)?
    2. If a user enters incorrect credentials three times in a row, should the system temporarily lock the account or display a security warning?

    <END OF EXAMPLE>

    **Important**: Your entire response must be written in the language of the provided domain narrative and requirements. All use case content, section titles, descriptions, and any additional text must be written in that same language.
    """
    )
])

# Função refinada para o nó
def validateuc_node(state):
    # Cadeia de execução do agente
    agent_validateuc_chain = validateuc_prompt | get_llm_model(state["api_key"]) | StrOutputParser()

    resultado = agent_validateuc_chain.invoke({
        "report": state["report"], 
        "minimundo": state["minimundo"],
        "ident_events": state["ident_events"]})

    return {**state, "report_validateuc": resultado}
