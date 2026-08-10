import os
import logging
import uuid
from os import path
from hashids import Hashids
from django.conf import settings
from django.http import Http404
from pathlib import Path

from .models import (
    Documento,
    UserAIConfig
)

from webhook_server.webhook_server_functions.miniworld_functions import (
    # expected data: video_entrevista: str
    run_graphMW_with_trace as run_mw
)
from webhook_server.webhook_server_functions.requirements_functions import (
    # expected data: minimundo: str
    run_graphRq_with_trace as run_rq
)
from webhook_server.webhook_server_functions.usecase_functions import (
    # expected data: minimundo: str, report: str
    run_graphUC_with_trace as run_uc
)
from webhook_server.webhook_server_functions.classdiagram_functions import (
    # expected data: minimundo: str, report: str, format_uc: str, report_validateuc: str
    run_graphDC_with_trace as run_dc
)
from webhook_server.webhook_server_functions.interface_functions import (
    # expected data: report: str, cdinuc_description_revised: str, ucincd_revised: str
    run_graphIP_with_trace as run_ip
)
from webhook_server.webhook_server_functions.revision_functions import (
    # expected data: report: str, report_validateuc: str, diagrama_classes_final: str
    run_graphRv_with_trace as run_rev
)
from webhook_server.webhook_server_functions.uccd_functions import (
    # expected data: minimundo: str, report: str
    run_graphUCandCD_with_trace as run_uc_cd
)
# Grafos de UC, CD e Revisão Simplificada juntos
from webhook_server.webhook_server_functions.simplified_uccd_functions import (
    # expected data: minimundo: str, report: str
    run_graphUCandCD_with_trace as run_simplified_uc_cd
)

logger = logging.getLogger(__name__)

hashids = Hashids(settings.HASHIDS_SALT, min_length=8)

def h_encode(id):
    return hashids.encode(id)

def h_decode(h):
    if z := hashids.decode(h):
        return z[0]


class HashIdConverter:
    regex = '[a-zA-Z0-9]{8,}'

    def to_python(self, value):
        return h_decode(value)

    def to_url(self, value):
        return h_encode(value)

def is_empty_or_null(string: str) -> bool:
    '''
    Verify if a string is empty or if its a None
    '''
    return not (string and string.strip())


def persist_uploaded_audio(audio_file, filename: str | None = None) -> str:
    shared_root = Path('/app/shared/uploads') if Path('/app/shared/uploads').exists() else Path(settings.MEDIA_ROOT)
    audio_dir = shared_root / 'tmp_audio'
    audio_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(filename or getattr(audio_file, 'name', 'audio')).name or 'audio'
    destination = audio_dir / f'{uuid.uuid4().hex}_{safe_name}'

    with destination.open('wb+') as target_file:
        for chunk in getattr(audio_file, 'chunks', lambda: [audio_file.read()])():
            target_file.write(chunk)

    return str(destination)


def version_from_another_doc(doc_origin: Documento, doc_old_v: Documento | None = None) -> tuple[int, int]:
    print('from another document')

    v_major = doc_origin.vMajor

    # if the origin and the older versions have the same major, it indicates a regen of a version
    if doc_old_v and doc_old_v.vMajor == v_major:
        v_minor = doc_old_v.vMinor + 1
    # otherwise, the version follows the same of the origin document
    else:
        v_minor = doc_origin.vMinor
    
    return v_major, v_minor

def version_from_audio(doc_old_v: Documento) -> tuple[int, int]:
    print('new major')

    return doc_old_v.vMajor + 1, 0

def update_version(doc_old_v: Documento) -> tuple[int, int]:
    print('update')

    return doc_old_v.vMajor, doc_old_v.vMinor + 1


def mask_sensitive_data(data: dict) -> dict:
    if not isinstance(data, dict):
        return data
    return {
        key: ('***REDACTED***' if key == 'api_key' else value)
        for key, value in data.items()
    }


def get_user_ai_api_key(user):
    """
    Get the user's configured AI API key.
    Returns None if the user has not configured a personal API key.
    Does NOT fall back to environment variables - users must configure their own key.
    """
    user_config = UserAIConfig.objects.filter(user=user).first()
    if user_config and user_config.api_key:
        return user_config.api_key
    return None


def send_to_llm(data: dict) -> str | tuple:
    result = None
    path = data.get('audio_path')
    redacted_data = mask_sensitive_data(data)

    logger.info('send_to_llm called', extra={'data': redacted_data})

    if not data.get('api_key'):
        logger.error('Missing api_key in send_to_llm payload', extra={'data': redacted_data})
        raise ValueError('Usuário não configurou uma chave de API de IA. Por favor, configure uma chave na página de configuração antes de gerar documentos.')

    match (data.get('TipoDocumento')):
        case 'MINIMUNDO':
            logger.info('MINIMUNDO - início', extra={'data': redacted_data})

            try:
                if not path:
                    logger.error("MINIMUNDO sem audio_path", extra={"data": data})
                    return None

                logger.info("Chamando run_mw", extra={"path": path})

                mw_data = run_mw({'video_entrevista': path, 'api_key': data.get('api_key')})

                logger.info("Retorno run_mw", extra={"mw_data": mw_data})

                if not mw_data:
                    logger.error("run_mw retornou vazio ou None")
                    return None

                if not isinstance(mw_data, dict):
                    logger.error("run_mw não retornou dict", extra={"tipo": type(mw_data)})
                    return None

                state = next(iter(mw_data.values())) if len(mw_data) == 1 else mw_data

                logger.info("Estado extraído", extra={"state": state})

                result = state.get('minimundo')

                logger.info("Resultado minimundo", extra={"result": result})

                if not result:
                    logger.error("Campo 'minimundo' não encontrado ou vazio", extra={"state": state})
                    return None

            except Exception as e:
                logger.exception("Erro no case MINIMUNDO")
                return None
            
        case 'REQUISITOS':
            try:
                print('Requisitos')
                print(data)

                documentos_origem = data.get('DocumentoOrigem')
            
                if documentos_origem:                        
                    # Se tiver só um documento de origem, garantir que seja tratado como lista
                    if isinstance(documentos_origem, str):
                        documentos_origem = [documentos_origem]
                    elif not documentos_origem:
                        documentos_origem = []
                    print('Documentos de origem:', documentos_origem)

                    originMw = ''
                    for docId in documentos_origem:
                        doc = Documento.objects.get(pk=docId)
                        if doc.TipoDocumento == 'MINIMUNDO':
                            originMw = doc.arquivo
                    
                    oldRq = ''
                    if data.get('DocumentoAnterior'):
                        doc = Documento.objects.get(pk=data.get('DocumentoAnterior'))
                        if doc.TipoDocumento == 'REQUISITOS':
                            oldRq = doc.arquivo

                    rq_data = run_rq({ 'minimundo': originMw, 'old_requirements':oldRq, 'api_key': data.get('api_key') })
                    if rq_data and isinstance(rq_data, dict):
                        state = next(iter(rq_data.values())) if len(rq_data) == 1 else rq_data
                        result = state.get('report')
            except:
                result = None

        # Atualizar Caso de Uso com base no upload de um novo Diagrama de Classes
        case 'CASO_USO':
            try:
                if data.get('DocumentoOrigem'):
                    originRq = ''
                    thisUc = data.get('arquivo')
                    
                    if data.get('parUC_CD'):
                        doc = Documento.objects.get(pk=data.get('parUC_CD'))
                        originCd = doc.arquivo

                    for docId in data.get('DocumentoOrigem'):
                        doc = Documento.objects.get(pk=docId)
                        if doc.TipoDocumento == 'REQUISITOS':
                            originRq = doc.arquivo

                    uc_data = run_rev({
                                'diagrama_classes_final': originCd,
                                'report': originRq,
                                'report_validateuc': thisUc,
                                'api_key': data.get('api_key')
                            })

                    if uc_data and isinstance(uc_data, dict):
                        state = next(iter(uc_data.values())) if len(uc_data) == 1 else uc_data
                        descricao_uc = state.get("cdinuc_description_revised")
                        tabela_uc = state.get("cdinuc_table_revised")
                        diagrama_uc = state.get("cdinuc_diagram_revised")

                        result = (diagrama_uc, tabela_uc, descricao_uc)
            except:
                result = None
            
        case 'DIAGRAMA_CLASSE':

            '''
            expected data
            { minimundo: str, report: str, format_uc: str, report_validateuc: str }
            '''
            try:
                if data.get('DocumentoOrigem'):
                    originMw = ''
                    originRq = ''
                    originUcTable = ''
                    originUcDescr = ''

                    for docId in data.get('DocumentoOrigem'):
                        doc = Documento.objects.get(pk=docId)
                        if doc.TipoDocumento == 'MINIMUNDO':
                            originMw = doc.arquivo
                        elif doc.TipoDocumento == 'REQUISITOS':
                            originRq = doc.arquivo

                        if data.get('parUC_CD'):
                            doc = Documento.objects.get(pk=data.get('parUC_CD'))
                            partes = doc.arquivo.split('<!-- -->')

                            print(f"Quantidade de partes do UC: {len(partes)}")

                            if len(partes) >= 3:
                                _, originUcTable, originUcDescr, _ = partes
                            else:
                                logger.error("Formato inesperado do arquivo", extra={
                                    "arquivo": doc.arquivo
                                })


                    cd_data = run_dc({
                        'minimundo': originMw,
                        'report': originRq,
                        'format_uc': originUcTable,
                        'report_validateuc': originUcDescr,
                        'api_key': data.get('api_key')
                    })
                    if cd_data and isinstance(cd_data, dict):
                        state = next(iter(cd_data.values())) if len(cd_data) == 1 else cd_data
                        result = state.get("diagrama_classes_final")
            except:
                result = None

        case 'PROTOTIPO_INTERFACE':
            '''
            expected data
            { report: str, cdinuc_description_revised: str, ucincd_revised: str }
            '''
            try:
                if data.get('DocumentoOrigem'):
                    originRq = ''
                    originUcDescr = ''
                    originCd = ''

                    for docId in data.get('DocumentoOrigem'):
                        doc = Documento.objects.get(pk=docId)
                        if doc.TipoDocumento == 'REQUISITOS':
                            originRq = doc.arquivo
                        elif doc.TipoDocumento == 'CASO_USO':
                            _, _, originUcDescr = doc.arquivo.split('\n<!-- -->\n')
                        elif doc.TipoDocumento == 'DIAGRAMA_CLASSE':
                            originCd = doc.arquivo

                ip_data = run_ip({ 'report': originRq, 'cdinuc_description_revised': originUcDescr, 'ucincd_revised': originCd, 'api_key': data.get('api_key')})
                if ip_data and isinstance(ip_data, dict):
                    state = next(iter(ip_data.values())) if len(ip_data) == 1 else ip_data
                    prototipo_interface = state.get("interface_prototype")
                    descricao_interface = state.get("interface_description")

                    result = (prototipo_interface, descricao_interface)
            except:
                result = None

        case 'CASO_USO_E_DIAGRAMA_CLASSE':
            
            try:
                if data.get('DocumentoOrigem'):
                    originMw = ''
                    originRq = ''

                    for docId in data.get('DocumentoOrigem'):
                        doc = Documento.objects.get(pk=docId)
                        if doc.TipoDocumento == 'MINIMUNDO':
                            originMw = doc.arquivo
                        elif doc.TipoDocumento == 'REQUISITOS':
                            originRq = doc.arquivo

                    uccd_data = run_simplified_uc_cd({ 'minimundo': originMw, 'report': originRq, 'api_key': data.get('api_key') })

                    if uccd_data and isinstance(uccd_data, dict):
                        state = next(iter(uccd_data.values())) if len(uccd_data) == 1 else uccd_data
                        descricao_uc = state.get("cdinuc_description_revised")
                        tabela_uc = state.get("cdinuc_table_revised")
                        diagrama_uc = state.get("usecases_diagram")
                        diagrama_classes = state.get("diagrama_classes_revisado")

                        result = {
                            "caso_uso": (diagrama_uc, tabela_uc, descricao_uc),
                            "diagrama_classe": diagrama_classes
                        }

                    # # 1. Gera CASO DE USO
                    # uc_data = run_uc({ 'minimundo': originMw, 'report': originRq })

                    # if uc_data and isinstance(uc_data, dict):
                    #     state_uc = next(iter(uc_data.values())) if len(uc_data) == 1 else uc_data
                        
                    #     diagrama_uc = state_uc.get("usecases_diagram")
                    #     tabela_uc = state_uc.get("format_uc")
                    #     descricao_uc = state_uc.get("report_validateuc")

                    #     # 2. Gera DIAGRAMA DE CLASSE usando resultado do UC
                    #     cd_data = run_dc({
                    #         'minimundo': originMw,
                    #         'report': originRq,
                    #         'format_uc': tabela_uc,
                    #         'report_validateuc': descricao_uc
                    #     })

                    #     if cd_data and isinstance(cd_data, dict):
                    #         state_cd = next(iter(cd_data.values())) if len(cd_data) == 1 else cd_data
                    #         diagrama_classes = state_cd.get("diagrama_classes_final")

                    #         # 3. Gera revisão usando resultado do CD e do UC
                    #         rev_data = run_rev({
                    #             'diagrama_classes_final': diagrama_classes,
                    #             'report': originRq,
                    #             'report_validateuc': descricao_uc
                    #         })

                    #         if isinstance(rev_data, dict):
                    #             state_rev = next(iter(rev_data.values())) if len(rev_data) == 1 else cd_data
                    #             descricao_uc_revisada = state_rev.get("cdinuc_description_revised")
                    #             tabela_uc_revisada = state_rev.get("cdinuc_table_revised")
                    #             diagrama_uc_revisado = state_rev.get("cdinuc_diagram_revised")
                    #             diagrama_classes_revisado = state_rev.get("ucincd_revised")

                    #             result = {
                    #                 "caso_uso": (diagrama_uc_revisado, tabela_uc_revisada, descricao_uc_revisada),
                    #                 "diagrama_classe": diagrama_classes_revisado
                    #             }
            except Exception as e:
                print(e)
                result = None

    return result