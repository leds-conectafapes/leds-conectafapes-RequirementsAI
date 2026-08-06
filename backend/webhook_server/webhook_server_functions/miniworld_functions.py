from langsmith import traceable
from webhook_server.graphs.miniworld_graph import graphMW
from fastapi import Request, APIRouter
from fastapi.responses import JSONResponse
import traceback

router = APIRouter()

# Preparar Estado
def preparar_estado_minimundo(data: dict) -> dict:
    caminho_video = ""
    old_mw = ""
    mw_instruction = ""

    if "chatInput" in data:
        caminho_video = data["chatInput"]

    if "old_mw" in data:
        old_mw = data["old_mw"]
        if "mw_instruction" in data:
            mw_instruction = data["mw_instruction"]

    return {
        "mensagem_usuario": caminho_video,
        "video_entrevista": caminho_video,
        "old_mw": old_mw,
        "mw_instruction": mw_instruction,
        "api_key": data["api_key"]
    }

# Execução
@traceable(name="Run Miniworld")
def run_graphMW_with_trace(input_data: dict):
    '''
    expected data
    { video_entrevista: str }
    '''
    
    final_state = None
    for step in graphMW.stream(input_data):
        print("🧩 Chunk parcial:", step)
        final_state = step
    return final_state

# @router.post("/webhook/miniworld")
# async def call_agent_miniworld(request: Request):
#     try:
#         from graphs.miniworld_graph import graphMW 

#         data = await request.json()
#         estado = preparar_estado_minimundo(data)

#         if not estado["mensagem_usuario"] or estado["mensagem_usuario"] == "":
#             return JSONResponse(status_code=400, content={"error": "Nenhuma mensagem reconhecida."})

#         print(f"🔵 Recebido: {estado['mensagem_usuario']}")

#         try:
#             result = run_graphMW_with_trace(estado)
#             print(f"Resposta gerada!")
#             print("🧾 RESULTADO COMPLETO DO GRAFO:")
#             print(result)

#         except Exception as e:
#             print(f" Erro no invoke: {str(e)}")
#             traceback.print_exc()
#             return JSONResponse(content={"output": f"Erro ao gerar resposta: {str(e)}"})
        
#         if result and isinstance(result, dict):
#             state = next(iter(result.values())) if len(result) == 1 else result
#             minimundo = (
#                 state.get("minimundo")
#                 or "Desculpe, não foi possível gerar uma resposta."
#             )
#         else:
#             minimundo = "Desculpe, não foi possível gerar uma resposta."
        
#         return JSONResponse(content={"minimundo": minimundo})

#     except Exception as e:
#         print(f" Erro geral: {str(e)}")
#         traceback.print_exc()
#         return JSONResponse(status_code=500, content={"error": str(e)})