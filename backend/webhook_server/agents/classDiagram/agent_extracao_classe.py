from langchain_core.messages import SystemMessage
from langchain.prompts import ChatPromptTemplate
#from RequirementsAI.webhook_server.app_config import llm_model
from langchain_core.output_parsers import StrOutputParser
from webhook_server.app_config import get_llm_model, parser

persona_message_extracao = SystemMessage(
    content=("""
        You are an expert in object-oriented analysis and class modeling.
        Based on the following class draft (listing classes (CLS), their attributes (ATTR), and relationships (REL)):
        
        Generate:
        - 1 class diagram in Mermaid format in a Markdown Document **exacly** like the following DESIRED FORMAT EXAMPLE
        - 1 data dictionary with the description of all attributes of all classes
        - Put both the Identified Gaps and Inconsistencies and the Questions for the User sections in the Questions section, if they exist
             
        1. Defining Classes and Attributes
            class Cls1{
                +Attr1
                +Attr2
                [...]
            }
            
            class Cls2{
                +Attr1
                +ListOfAttr
                [...]
            }
             
        2. Defining Relations
            Cls1 --> Cls2
        
        3. Defining Relations With Cardinality
            a. OneToOne
                Cls1 "1" --> "1" Cls2
            b. OneToMany
                Cls1 "1" --> "*" Cls2
            c. ManyToOne
                Cls1 "*" --> "1" Cls2
            d. ManyToMany
                Cls1 "*" --> "*" Cls2
            
        3. Defining Inheritance
            Cls1 --|> Cls2

        <DESIRED FORMAT EXAMPLE:>

        ## Class Diagram
        
        ```mermaid
        classDiagram
            class Animal{
                Name
            }
            
            class Dog{
                ChipCode
            }
            
            class Toy{
                Color
                Type
            }
            
            Dog --|> Animal
            Dog "1" --> "*" Toy : has
        ```
        ## Data dictionary

        ### Animal
        | Attribute | Description |
        |-----------|-------------|
        | Name | Name of the Animal |
        
        ### Dog
        | Attribute | Description |
        |-----------|-------------|
        | ChipCode | Unique code that identify the Dog |
        
        ### Toy
        | Attribute | Description |
        |-----------|-------------|
        | Color | Color of the Toy |
        | Type | Type of the Toy (e.g.: Throwing, Chewing) |
        
        ## Questions
             
        1. There is any other Animal on the system (e.g.: Cat, Parrot)?
        2. What is the format of the toy color (e.g.: Color Name, RGB, Hex)
        
        <END OF EXAMPLE>

        Additional instructions:
        - Use nouns for classes and attributes names (e.g.: class Dog, Color).
        - Use PascalCase for classes names
        - Use CamelCase for attributes names
        - Do not specify the type of attributes in the class diagram. Only include the attribute names without types.
        - If there are doubts or gaps, include the questions at the end in a "Questions and Validations" section, after the class diagram.
        - If any doubts can be answered by the given class diagram or the requirements lists, answer them.
        - Do not include additional comments at the beginning of the contents of the generated documents, besides the "Questions and Validations" section.

        Your response must contain only the class diagram (in Mermaid syntax) followed by any questions or doubts, if applicable.
        Your response must be formatted as a Markdown document.
        **Important**: Your entire response must be written in the language of the provided domain narrative, requirements and use cases. All class diagram content, section titles, descriptions, and any additional text must be written in that same language.             
        """
        
    )
)

extracao_prompt = ChatPromptTemplate.from_messages([
    persona_message_extracao,
    ("human", "draft of classes:\n\n{rascunho_classes}\n\nGenerate **exactly** 1 class diagram ") #Generate **exactly** 3 tables in Markdown format
])


def extract_node(state):

    agent_extracao_chain = extracao_prompt | get_llm_model(state["api_key"]) | StrOutputParser()

    resultado = agent_extracao_chain.invoke({"rascunho_classes": state["rascunho_classes"]})
    return {**state, "diagrama_classes": resultado}