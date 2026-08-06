from langsmith import traceable
from webhook_server.graphs.requirement_graph import graphRq
from fastapi import Request, APIRouter
from fastapi.responses import JSONResponse
import traceback

router = APIRouter()

def preparar_estado_requisitos(data: dict) -> dict:
    minimundo = ""
    requisitos_anteriores = ""
    info_requisitos = ""

    if "minimundo" in data:
        minimundo = data["minimundo"]
    if "requisitos_anteriores" in data:
        requisitos_anteriores = data["requisitos_anteriores"]
    if "info_requisitos" in data:
        info_requisitos = data["info_requisitos"]
    
    return {
        "mensagem_usuario": minimundo,
        "minimundo": minimundo,
        "old_requirements": requisitos_anteriores,
        "requirements_information": info_requisitos,
        "api_key": data["api_key"]
    }

@traceable(name="Run Requirements Table")
def run_graphRq_with_trace(input_data: dict):
    '''
    expected data
    { minimundo: str }
    '''

    final_state = None
    for step in graphRq.stream(input_data):
        print("🧩 Chunk parcial:", step)
        final_state = step
    return final_state

# @router.post("/webhook/requirements")
# async def call_agent_miniworld(request: Request):
#     try:
#         from graphs.requirement_graph import graphRq

#         data = await request.json()
#         estado = preparar_estado_requisitos(data)

#         if not estado["mensagem_usuario"] or estado["mensagem_usuario"] == "":
#             return JSONResponse(status_code=400, content={"error": "Nenhuma mensagem reconhecida."})

#         print(f"🔵 Recebido: {estado['mensagem_usuario']}")

#         try:
#             result = run_graphRq_with_trace(estado)
#             print(f"Resposta gerada!")
#             print("🧾 RESULTADO COMPLETO DO GRAFO:")
#             print(result)

#         except Exception as e:
#             print(f" Erro no invoke: {str(e)}")
#             traceback.print_exc()
#             return JSONResponse(content={"output": f"Erro ao gerar resposta: {str(e)}"})
        
#         if result and isinstance(result, dict):
#             state = next(iter(result.values())) if len(result) == 1 else result
#             report = (
#                 state.get("report")
#                 or "Desculpe, não foi possível gerar uma resposta."
#             )
#         else:
#             report = "Desculpe, não foi possível gerar uma resposta."
        
#         return JSONResponse(content={"report": report})

#     except Exception as e:
#         print(f" Erro geral: {str(e)}")
#         traceback.print_exc()
#         return JSONResponse(status_code=500, content={"error": str(e)})