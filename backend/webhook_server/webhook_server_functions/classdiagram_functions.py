from langsmith import traceable
from webhook_server.graphs.class_diagram_graph import graphDC
from fastapi import Request, APIRouter
from fastapi.responses import JSONResponse
import traceback

router = APIRouter()

def preparar_estado_diagrama_classe(data: dict) -> dict:
    minimundo = ""
    requisitos = ""
    tabela_uc = ""
    descricao_uc = ""
    old_cd = ""
    cd_instruction = ""

    if "minimundo" in data:
        minimundo = data["minimundo"]
    if "requisitos" in data:
        requisitos = data["requisitos"]
    if "tabela_caso_uso" in data:
        tabela_uc = data["tabela_caso_uso"]
    if "descricao_caso_uso" in data:
        descricao_uc = data["descricao_caso_uso"]

    if "old_cd" in data:
        old_cd = data["old_cd"]
        if "cd_instruction" in data:
            cd_instruction = data["cd_instruction"]

    return {
        "mensagem_usuario": tabela_uc,
        "minimundo": minimundo,
        "report": requisitos,
        "format_uc": tabela_uc,
        "report_validateuc": descricao_uc,
        "old_cd": old_cd,
        "cd_instruction": cd_instruction,
        "api_key": data["api_key"]
    }

@traceable(name="Run Class Diagram")
def run_graphDC_with_trace(input_data: dict):
    '''
    expected data
    { minimundo: str, report: str, format_uc: str, report_validateuc: str }
    '''

    final_state = None
    for step in graphDC.stream(input_data):
        print("🧩 Chunk parcial:", step)
        final_state = step
    return final_state

# @router.post("/webhook/class-diagrams")
# async def call_agent_miniworld(request: Request):
#     try:
#         from graphs.class_diagram_graph import graphDC

#         data = await request.json()
#         estado = preparar_estado_diagrama_classe(data)

#         if not estado["mensagem_usuario"] or estado["mensagem_usuario"] == "":
#             return JSONResponse(status_code=400, content={"error": "Nenhuma mensagem reconhecida."})

#         print(f"🔵 Recebido: {estado['mensagem_usuario']}")

#         try:
#             result = run_graphDC_with_trace(estado)
#             print(f"Resposta gerada!")
#             print("🧾 RESULTADO COMPLETO DO GRAFO:")
#             print(result)

#         except Exception as e:
#             print(f" Erro no invoke: {str(e)}")
#             traceback.print_exc()
#             return JSONResponse(content={"output": f"Erro ao gerar resposta: {str(e)}"})
        
#         if result and isinstance(result, dict):
#             state = next(iter(result.values())) if len(result) == 1 else result
#             diagrama = (
#                 state.get("diagrama_classes_final")
#                 or "Desculpe, não foi possível gerar uma resposta."
#             )
#         else:
#             diagrama = "Desculpe, não foi possível gerar uma resposta."
        
#         return JSONResponse(content={"diagrama_cd": diagrama})

#     except Exception as e:
#         print(f" Erro geral: {str(e)}")
#         traceback.print_exc()
#         return JSONResponse(status_code=500, content={"error": str(e)})