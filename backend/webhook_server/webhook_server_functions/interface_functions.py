from langsmith import traceable
from webhook_server.graphs.interface_graph import graphIP
from fastapi import Request, APIRouter
from fastapi.responses import JSONResponse
import traceback

router = APIRouter()

def preparar_estado_prototipo_interface(data: dict) -> dict:
    descricao_uc = ""
    diagrama_classes = ""
    if "descricao_caso_uso" in data:
        descricao_uc = data["descricao_caso_uso"]
    if "diagrama_classes" in data:
        diagrama_classes = data["diagrama_classes"]

    return {
        "mensagem_usuario": descricao_uc,
        "cdinuc_description_revised": descricao_uc,
        "ucincd_revised": diagrama_classes,
        "api_key": data["api_key"]
    }

@traceable(name="Run Interface Prototype")
def run_graphIP_with_trace(input_data: dict):
    '''
    expected data
    { report: str, cdinuc_description_revised: str, ucincd_revised: str }
    '''

    final_state = None
    for step in graphIP.stream(input_data):
        print("🧩 Chunk parcial:", step)
        final_state = step
    return final_state

# @router.post("/webhook/interface-prototype")
# async def call_agent_miniworld(request: Request):
#     try:
#         from graphs.interface_graph import graphIP

#         data = await request.json()
#         estado = preparar_estado_prototipo_interface(data)

#         if not estado["mensagem_usuario"] or estado["mensagem_usuario"] == "":
#             return JSONResponse(status_code=400, content={"error": "Nenhuma mensagem reconhecida."})

#         print(f"🔵 Recebido: {estado['mensagem_usuario']}")

#         try:
#             result = run_graphIP_with_trace(estado)
#             print(f"Resposta gerada!")
#             print("🧾 RESULTADO COMPLETO DO GRAFO:")
#             print(result)

#         except Exception as e:
#             print(f" Erro no invoke: {str(e)}")
#             traceback.print_exc()
#             return JSONResponse(content={"output": f"Erro ao gerar resposta: {str(e)}"})
        
#         if result and isinstance(result, dict):
#             state = next(iter(result.values())) if len(result) == 1 else result
#             prototipo_interface = (
#                 state.get("interface_prototype")
#                 or "Desculpe, não foi possível gerar uma resposta."
#             )
#             descricao_interface = (
#                 state.get("interface_description")
#                 or "Desculpe, não foi possível gerar uma resposta."
#             )
#         else:
#             prototipo_interface = "Desculpe, não foi possível gerar uma resposta."
#             descricao_interface = "Desculpe, não foi possível gerar uma resposta."
        
#         return JSONResponse(content={
#             "prototipo_interface": prototipo_interface,
#             "descricao_interface": descricao_interface
#             })

#     except Exception as e:
#         print(f" Erro geral: {str(e)}")
#         traceback.print_exc()
#         return JSONResponse(status_code=500, content={"error": str(e)})