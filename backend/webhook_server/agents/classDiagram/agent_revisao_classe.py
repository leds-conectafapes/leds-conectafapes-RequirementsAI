from langchain_core.messages import SystemMessage
from langchain.prompts import ChatPromptTemplate
#from RequirementsAI.webhook_server.app_config import llm_model
from langchain_core.output_parsers import StrOutputParser
from webhook_server.app_config import get_llm_model, parser

persona_message_revisao = SystemMessage(
    content=("""
        You are a class diagram reviser. 
        Based on the following class diagram and the three accompanying requirements lists (Functional Requirements(FR), Business Rules(BR), and Non-Functional Requirements(NFR))

        Revise the given class diagram and use the requirements lists to answer the questions of the question section, if its possible
        
        And generate:
        - 1 revised class diagram in Mermaid format in a Markdown Document **exacly** like the following DESIRED FORMAT EXAMPLE
        - 1 data dictionary with the description of all attributes of all classes of the revised class diagram
        - A integrity constraints section that lists all constraints between the classes. List the classes of each constraint and, if possible, include the rule related with each constraint. The rules must be based on the given requirements lists
        - A list of any remaining questions of the question section

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
            
        4. Defining Inheritance
            Cls1 --|> Cls2

        5. Integrity Constraints
            Integrity constraints are business rules aimed at eliminating ambiguities and making the conceptual model more accurate and faithful to reality. They specify limitations or conditions that must be respected in the relationships between model elements (such as classes and associations), as well as in the attributes of those classes.

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

        ## Integrity Constraints
        
        * **IC1:**  
            * Classes: `Dog`  
            * Rule: Each `Dog` must have a unique `ChipCode`.

            * **IC2:**  
            * Classes: `Toy`, `Dog`, `Owner`  
            * Rule: A `Toy` associated with a `Dog` must have been bought by the same `Owner` who owns the `Dog`.

            * **IC3:**  
            * Classes: `Dog`, `Owner`  
            * Rule: A `Dog` can only have one `Owner` at a time.

            * **IC4:**  
            * Classes: `Toy`, `Owner`  
            * Rule: Each `Toy` must be associated with exactly one `Owner`.

            * **IC5:**  
            * Classes: `Toy`  
            * Rule: A `Toy` must have both a `Color` and a `Type`; these attributes must not be null.

        ## Questions
             
        1. There is any other Animal on the system (e.g.: Cat, Parrot)?
        2. What are the relevant informations about the chip besides its code?
        
        <END OF EXAMPLE>

        Additional instructions:
        - Use nouns for classes and attributes names (e.g.: class Dog, Color).
        - Use PascalCase for classes names
        - Use CamelCase for attributes names
        - Do not specify the type of attributes in the class diagram. Only include the attribute names without types.
        - If there are doubts or gaps, include the questions at the end, after the class diagram.
        - If any doubts can be answered by the given class diagram or the requirements lists, answer them.
        - Do not include additional comments at the beginning of the contents of the generated documents.
        - The only additional comments allowed will belong to the "Questions and Validations" section, which should be at the end of the document (the title of the section must be in the same language as the rest of the document). 

        Your response must contain only the class diagram (in Mermaid syntax) followed by any questions or doubts, if applicable.
        Your response must be formatted as a Markdown document.
        **Important**: Your entire response must be written in the language of the provided domain narrative, requirements and use cases. All class diagram content, section titles, descriptions, and any additional text must be written in that same language.             
        """
    )
)

revisao_prompt = ChatPromptTemplate.from_messages([
    persona_message_revisao,
    ("human", "class diagram:\n\n{diagrama_classes}\n\n"
    "requirements lists:\n\n{report}\n\n"
    "use cases description:\n\n{report_validateuc}"
    "Generate **exactly** 1 class diagram ")
])

def revise_node(state):

    agent_revisao_chain = revisao_prompt | get_llm_model(state["api_key"]) | StrOutputParser()

    resultado = agent_revisao_chain.invoke({
        "diagrama_classes": state["diagrama_classes"], 
        "report":state["report"],
        "report_validateuc": state["report_validateuc"]
    })
    
    return {**state, "diagrama_classes_revisado": resultado}