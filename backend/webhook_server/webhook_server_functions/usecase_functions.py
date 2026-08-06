from langsmith import traceable
from webhook_server.graphs.use_case_graph import graphUC
from fastapi import Request, APIRouter
from fastapi.responses import JSONResponse
import traceback

router = APIRouter()

def preparar_estado_caso_uso(data: dict) -> dict:
    minimundo = ""
    requisitos = ""
    casosdeuso_anteriores = ""
    info_casosdeuso = ""

    if "minimundo" in data:
        minimundo = data["minimundo"]
    if "requisitos" in data:
        requisitos = data["requisitos"]
    if "casosdeuso_anteriores" in data:
        casosdeuso_anteriores = data["casosdeuso_anteriores"]
    if "info_casosdeuso" in data:
        info_casosdeuso = data["info_casosdeuso"]

    return {
        "mensagem_usuario": requisitos,
        "report": requisitos,
        "minimundo": minimundo,
        "old_uc": casosdeuso_anteriores,
        "uc_information": info_casosdeuso,
        "api_key": data["api_key"]
    }

@traceable(name="Run Use Cases")
def run_graphUC_with_trace(input_data: dict):
    '''
    expected data
    { minimundo: str, report: str }
    '''

    final_state = None
    for step in graphUC.stream(input_data):
        print("🧩 Chunk parcial:", step)
        final_state = step
    return final_state

# @router.post("/webhook/use-cases")
# async def call_agent_miniworld(request: Request):
#     try:
#         from graphs.use_case_graph import graphUC

#         data = await request.json()
#         estado = preparar_estado_caso_uso(data)

#         if not estado["mensagem_usuario"] or estado["mensagem_usuario"] == "":
#             return JSONResponse(status_code=400, content={"error": "Nenhuma mensagem reconhecida."})

#         print(f"🔵 Recebido: {estado['mensagem_usuario']}")

#         try:
#             result = run_graphUC_with_trace(estado)
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
#                 state.get("usecases_diagram")
#                 or "Desculpe, não foi possível gerar uma resposta."
#                 )
#             tabela = (
#                 state.get("format_uc")
#                 or ""
#             )
#             descricao = (
#                 state.get("report_validateuc")
#                 or ""
#             )

#         else:
#             diagrama = "Desculpe, não foi possível gerar uma resposta."
#             tabela = ""
#             descricao = ""
        
#         return JSONResponse(content={
#             "diagrama_uc": diagrama,
#             "tabela_uc": tabela,
#             "descricao_uc": descricao
#             })

#     except Exception as e:
#         print(f" Erro geral: {str(e)}")
#         traceback.print_exc()
#         return JSONResponse(status_code=500, content={"error": str(e)})