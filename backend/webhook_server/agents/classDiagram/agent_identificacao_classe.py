from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from langchain.prompts import ChatPromptTemplate
#from RequirementsAI.webhook_server.app_config import llm_model
from webhook_server.app_config import get_llm_model, parser
import datetime
from langchain_core.output_parsers import StrOutputParser

persona_message_ident_class = SystemMessage(
    content=(
        "You are a highly experienced Class Engineering Specialist. "
        "Your tasks involve: carefully analyzing domain narratives, "
        "identifying classes, indentifying it's attributes and relations "
        "and detecting missing information or inconsistencies. "
        "Your output must be clear, structured, and actionable."
    )
)

identificacao_prompt = ChatPromptTemplate.from_messages([
    persona_message_ident_class,
    ("human", """
    You are an expert in object-oriented analysis and class modeling.

    Task:
    1. Read and analyze the Domain Narrative, Use Cases Description and the Old Class Diagram below.
        - The Old Class Diagram may be empty, if so, ignore it and treat your output as the draft of the first version for the Class Diagram.
        - If the Old Class Diagram exists, follow its instructions using its information, alongside with the information of the Domain Narrative and of the Use Case Description.
    
    2. Identify and extract:
        - Classes (CLS): A class describes a set of objects (an object is an entity that embodies an abstraction relevant to the context of an application) with the same structure (attributes and relations) and the same semantics.
        - Attributes (ATTR): An attribute is a property, characteristic, or data associated with a class. It describes relevant aspects of that class in the context of the domain of the model.
        - Relations (REL): A relationship is an association between two entities that expresses how they interact in the context of the domain of the model.
     
    3. Deliver:
        - A structured preliminary draft listing CLS and, for each CLS, their ATTR and REL.
        - A list of any identified gaps, ambiguities, or inconsistencies.
        - Questions for the user to clarify unclear or missing points.

    Instructions:
    - If you identify missing or conflicting information, **explicitly list** the issues and suggest specific questions to ask the user.
    - If the user cannot provide the necessary answers, **propose well-founded assumptions** and document them clearly.
    - Avoid representing derived values as attributes. Instead, model the original source data from which these values can be computed.
    - Avoid creating empty classes that have no attributes or associations of their own, even if they inherit them from other classes.
    - Do not specify types for attributes; only list the attribute names.
    - Do not include additional comments at the beginning of the contents of the generated documents.
    - Present your final response in the following format:

    ---
    
    <DESIRED FORMAT EXAMPLE:>

    **Classes (CLS):**
    - CLS1: [description]
    -- ATTR1: [description]
    -- ATTR2: [description]
    [...]
    -- REL1: [description]
    -- REL2: [description]
    [...]
    - CLS2: [description]
    -- ATTR1: [description]
    -- ATTR2: [description]
    [...]
    -- REL1: [description]
    -- REL2: [description]
    [...]

    **Identified Gaps and Inconsistencies:**
    - [List the issues found]

    **Questions for the User:**
    - [List of questions]
    
    <END OF EXAMPLE>
    
    ---

    Domain Narrative:
    {minimundo}
     
    Use Cases Description:
    {report_validateuc}
    
    Class Diagram Instruction:
    {cd_instruction} 
    
    Old Class Diagram (may be empty):
    {old_cd}

    Remember: if there is missing or conflicting information, ask the user.
    If the user has no answers, make well-founded assumptions and inform what decisions were made.
    **Important**: Your entire response must be written in the language of the provided domain narrative, requirements and use cases. All class diagram content, section titles, descriptions, and any additional text must be written in that same language.             

     """)
])

def identify_node(state):
    """
    Steps 1 and 2:
    1. Carefully read the domain narrative to identify
       Classes (CLS), Attributes (ATTR) and Relations (REL).
    2. Generate an initial understanding of the classes and their attributes and relations.
    """
    print("🔎 Estado recebido no nó de identificacao:", state)

    agent_identificacao_chain = identificacao_prompt | get_llm_model(state["api_key"]) | StrOutputParser()

    resultado = agent_identificacao_chain.invoke({
        "minimundo": state["minimundo"],
        "report_validateuc": state["report_validateuc"],
        "cd_instruction": "",
        "old_cd": ""
        })

    return {**state, "rascunho_classes": resultado}