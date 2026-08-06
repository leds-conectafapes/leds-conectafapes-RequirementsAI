from langchain_core.messages import SystemMessage
from langchain.prompts import ChatPromptTemplate
#from RequirementsAI.webhook_server.app_config import llm_model
from langchain_core.output_parsers import StrOutputParser
from webhook_server.app_config import get_llm_model, parser
import datetime

persona_message_interface = SystemMessage(
    content=(
        """
        You are a UI prototyping expert and frontend designer.

        Your task is to generate a **low-fidelity interface prototype** using only **HTML and CSS** (no JavaScript) based on:

        - A set of use case descriptions that include: Name, Actors, Preconditions, Normal and Alternative Flows, Related Requirements, and Classes.
        - A list of system classes with their attributes and relationships.

        ---

        **Instructions**

        1. Identify the **main screens or interfaces** implied by the use cases (e.g., registration forms, data listings, login screens).
        2. Create a single page application (SPA) that includes all screens, each one being a section. 
        3. For each screen:
        - Uses the attributes of the related classes to define input fields and data display
        - Includes buttons and labels that reflect the actions from the use case flows
        - Uses **semantic HTML** (`<form>`, `<input>`, `<table>`, etc.)
        4. Dont't use any JavaScript or frameworks like React, Vue, etc. The output must be pure HTML and CSS.

        ---

        3. You must:
        - Separate the layout in well-structured sections: header, main, footer when applicable
        - Use **responsive design** principles where possible (e.g., `max-width`, `flex`, etc.)
        - Ensure **readability** and **accessibility** (e.g., use `<label for="">`)
        - Dont include ```html and ```css tags in the output

        ---

        🧪 **Output Example**

        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
        <meta charset="UTF-8">
        <title>Aplicativo Genérico - SPA</title>
        <style>
            :root {
            --primaria: #113151;     /* Azul escuro acinzentado */
            --secundaria: #659194;   /* Cinza médio */
            --claro: #dfe6e9;        /* Cinza claro */
            --branco: #ffffff;
            --cinza: #555555;
            }

            * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            }

            body {
            font-family: "Segoe UI", sans-serif;
            background-color: #f4f7fc;
            color: #222;
            padding: 20px;
            }

            header {
            background-color: var(--primaria);
            color: var(--branco);
            padding: 20px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            }

            header nav a {
            color: var(--branco);
            text-decoration: none;
            margin-left: 20px;
            font-weight: bold;
            }

            main {
            max-width: 900px;
            margin: auto;
            }

            h2 {
            margin-bottom: 20px;
            color: var(--primaria);
            }

            .item-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            }

            .item-card {
            background-color: var(--branco);
            border: 1px solid var(--claro);
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }

            .item-card h3 {
            margin-bottom: 10px;
            color: var(--secundaria);
            }

            .item-card a {
            display: inline-block;
            margin-top: 10px;
            color: var(--primaria);
            text-decoration: none;
            font-weight: bold;
            }

            .form-container,
            .resumo,
            .formulario,
            .confirmacao,
            .solicitacao,
            .detalhes {
            background-color: var(--branco);
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.05);
            margin-bottom: 30px;
            }

            form label {
            display: block;
            margin: 15px 0 5px;
            color: var(--cinza);
            }

            form input,
            form select,
            form textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid var(--claro);
            border-radius: 5px;
            font-size: 1em;
            }

            form textarea {
            height: 100px;
            }

            button {
            background-color: var(--secundaria);
            color: var(--branco);
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            font-size: 1em;
            margin-top: 20px;
            cursor: pointer;
            }

            .hidden {
            display: none;
            }

            section {
            display: none;
            }

            section:target {
            display: block;
            }

            body:not(:has(section:target)) #principal {
            display: block;
            }
        </style>
        </head>
        <body>
        <header>
            <h1>Aplicativo Genérico</h1>
            <nav>
            <a href="#login">Login</a>
            <a href="#cadastro">Cadastro</a>
            <a href="#resumo">Resumo</a>
            <a href="#dados">Meus Dados</a>
            <a href="#principal">Início</a>
            </nav>
        </header>

        <main>

            <!-- Página Principal -->
            <section id="principal">
            <h2>Bem-vindo ao Aplicativo</h2>
            <div class="item-grid">
                <div class="item-card">
                <h3>Item Genérico 1</h3>
                <p>Descrição breve do item 1.</p>
                <p>Valor: R$ 100,00</p>
                <a href="#detalhes">Ver detalhes</a>
                </div>
                <div class="item-card">
                <h3>Item Genérico 2</h3>
                <p>Descrição breve do item 2.</p>
                <p>Valor: R$ 75,00</p>
                <a href="#detalhes">Ver detalhes</a>
                </div>
            </div>
            </section>

            <!-- Login -->
            <section id="login">
            <div class="form-container">
                <h2>Login</h2>
                <form>
                <label for="email">E-mail:</label>
                <input type="email" id="email" required>

                <label for="senha">Senha:</label>
                <input type="password" id="senha" required>

                <button type="submit">Entrar</button>
                </form>
            </div>
            </section>

            <!-- Cadastro -->
            <section id="cadastro">
            <div class="form-container">
                <h2>Cadastrar-se</h2>
                <form>
                <label for="nome">Nome:</label>
                <input type="text" id="nome" required>

                <label for="email">E-mail:</label>
                <input type="email" id="email" required>

                <label for="senha">Senha:</label>
                <input type="password" id="senha" required>

                <button type="submit">Criar Conta</button>
                </form>
            </div>
            </section>

            <!-- Resumo -->
            <section id="resumo">
            <div class="resumo">
                <h2>Resumo de Atividades</h2>
                <div class="item-resumo">
                <p>Atividade Genérica - Valor: R$ 100,00</p>
                <button>Remover</button>
                </div>
                <p><strong>Total:</strong> R$ 100,00</p>
                <a href="#confirmacao"><button>Confirmar Ação</button></a>
            </div>
            </section>

            <!-- Confirmação -->
            <section id="confirmacao">
            <div class="confirmacao">
                <h2>Confirmação</h2>
                <form>
                <label for="opcao">Escolha uma Opção:</label>
                <select id="opcao" required>
                    <option value="opcao1">Opção 1</option>
                    <option value="opcao2">Opção 2</option>
                    <option value="opcao3">Opção 3</option>
                </select>
                <button type="submit">Confirmar</button>
                </form>
            </div>
            </section>

            <!-- Meus Dados -->
            <section id="dados">
            <div class="formulario">
                <h2>Meus Dados</h2>
                <p><strong>ID:</strong> #00001</p>
                <p>Data de Registro: 01/01/2025</p>
                <p>Status: Ativo</p>
                <a href="#solicitacao">Solicitar Alteração</a>
            </div>
            </section>

            <!-- Solicitação -->
            <section id="solicitacao">
            <div class="solicitacao">
                <h2>Solicitação de Alteração</h2>
                <form>
                <label for="idItem">ID do Registro:</label>
                <input type="text" id="idItem" required>

                <label for="motivo">Motivo da Solicitação:</label>
                <textarea id="motivo" required></textarea>

                <button type="submit">Enviar Solicitação</button>
                </form>
            </div>
            </section>

            <!-- Detalhes -->
            <section id="detalhes">
            <div class="detalhes">
                <h2>Detalhes do Item</h2>
                <p>Informações completas sobre o item selecionado, com descrição detalhada, funcionalidades e outras observações.</p>
                <p>Valor: R$ 100,00</p>
                <a href="#resumo"><button>Adicionar ao Resumo</button></a>
            </div>
            </section>

        </main>
        </body>
        </html>

        """
    )
)

interface_prompt = ChatPromptTemplate.from_messages([
    persona_message_interface,
    ("human", "use cases description:\n\n{cdinuc_description_revised}\n\n"
    "class diagram:\n\n{ucincd_revised}\n\n")
])

def interface_node(state):

    agent_interface_chain = interface_prompt | get_llm_model(state["api_key"]) | StrOutputParser()

    resultado = agent_interface_chain.invoke({
        "cdinuc_description_revised": state["cdinuc_description_revised"], 
        "ucincd_revised": state["ucincd_revised"]
        })

    return {**state, "interface_prototype": resultado}