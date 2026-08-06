from langsmith import traceable
from webhook_server.graphs.revision_graph import graphRv
from fastapi import Request, APIRouter
from fastapi.responses import JSONResponse
import traceback

router = APIRouter()

def preparar_estado_revisao(data: dict) -> dict:
    requisitos = ""
    descricao_uc = ""
    diagrama_classes = ""
    if "requisitos" in data:
        requisitos = data["requisitos"]
    if "descricao_caso_uso" in data:
        descricao_uc = data["descricao_caso_uso"]
    if "diagrama_classes" in data:
        diagrama_classes = data["diagrama_classes"]

    return {
        "mensagem_usuario": diagrama_classes,
        "report": requisitos,
        "report_validateuc": descricao_uc,
        "diagrama_classes_final": diagrama_classes,
        "api_key": data["api_key"]
    }

@traceable(name="Run Revision")
def run_graphRv_with_trace(input_data: dict):
    final_state = None
    for step in graphRv.stream(input_data):
        print("🧩 Chunk parcial:", step)
        final_state = step
    return final_state

@router.post("/webhook/revision")
async def call_agent_miniworld(request: Request):
    try:
        from graphs.revision_graph import graphRv

        data = await request.json()
        estado = preparar_estado_revisao(data)

        if not estado["mensagem_usuario"] or estado["mensagem_usuario"] == "":
            return JSONResponse(status_code=400, content={"error": "Nenhuma mensagem reconhecida."})

        print(f"🔵 Recebido: {estado['mensagem_usuario']}")

        try:
            result = run_graphRv_with_trace(estado)
            print(f"Resposta gerada!")
            print("🧾 RESULTADO COMPLETO DO GRAFO:")
            print(result)

        except Exception as e:
            print(f" Erro no invoke: {str(e)}")
            traceback.print_exc()
            return JSONResponse(content={"output": f"Erro ao gerar resposta: {str(e)}"})
        
        if result and isinstance(result, dict):
            state = next(iter(result.values())) if len(result) == 1 else result
            descricao_uc = (
                state.get("cdinuc_description_revised")
                or "Desculpe, não foi possível gerar uma resposta."
            )
            tabela_uc = (
                state.get("cdinuc_table_revised")
                or "Desculpe, não foi possível gerar uma resposta."
            )
            diagrama_uc = (
                state.get("cdinuc_diagram_revised")
                or "Desculpe, não foi possível gerar uma resposta."
            )
            diagrama_classes = (
                state.get("ucincd_revised")
                or "Desculpe, não foi possível gerar uma resposta."
            )
        else:
            descricao_uc = "Desculpe, não foi possível gerar uma resposta."
            tabela_uc = "Teste de erro."
            diagrama_uc = "Teste de erro 2"
            diagrama_classes = "Teste de erro 3"
        
        return JSONResponse(content={
            "descricao_uc": descricao_uc,
            "tabela_uc": tabela_uc,
            "diagrama_uc": diagrama_uc,
            "diagrama_classes": diagrama_classes
            })

    except Exception as e:
        print(f" Erro geral: {str(e)}")
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})