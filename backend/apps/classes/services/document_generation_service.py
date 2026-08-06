import os
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from django.core.files import File

from ..models import Documento
from ..serializers import (DocumentoWriteSerializer)

from ..utils import (
    get_user_ai_api_key,
    is_empty_or_null,
    send_to_llm,
    version_from_another_doc,
    update_version)


class DocumentoGenerationService:

    # payload: {
    #     "documento_data": Dados do documento passados na requisição,
    #     "audio_path": "Caminho do arquivo de áudio do upload" (opcional, somente se houver upload),
    #     "arquivoAudio_name": "Nome do áudio a ser reusado" (opcional, para novos minimundos sem upload de áudio)
    # }
    @staticmethod
    def generate_documento(payload, user_id, job=None):
        User = get_user_model()
        user = User.objects.get(id=user_id)

        data_documento = payload.get("documento_data")
        audio_path = payload.get("audio_path")

        # Attach per-user or fallback AI key for downstream generation
        data_documento['api_key'] = get_user_ai_api_key(user)

        # Utilizado dentro de send_to_llm
        if audio_path:
            data_documento['audio_path'] = audio_path

        # Só tem valor caso seja um novo MINIMUNDO sem upload de áudio, 
        # mas com DocumentoAnterior, onde é conveniente reutilizar o áudio
        arquivoAudio_name = payload.get("arquivoAudio_name")

        documentos_origem = data_documento.get('DocumentoOrigem')
        documento_anterior = data_documento.get('DocumentoAnterior')

        # Força sempre lista no data, e nunca string
        data_documento['DocumentoOrigem'] = documentos_origem

        # Se for CASO_USO/DIAGRAMA_CLASSE, enviar para um método separado
        if data_documento.get('TipoDocumento') in ['CASO_USO_E_DIAGRAMA_CLASSE', # Ambos gerados juntos, por IA
                                         'CASO_USO_SIMPLES', # Upload do UC e incremento de versão do CD relacionado, sem usar IA
                                         'DIAGRAMA_CLASSE_SIMPLES', # Upload do CD e incremento de versão do UC relacionado, sem usar IA
                                         'CASO_USO_ATUALIZAR', # Upload do UC e geração de nova versão do CD relacionado com IA
                                         'DIAGRAMA_CLASSE_ATUALIZAR']: # Upload do CD e geração de nova versão do UC relacionado com IA
            return DocumentoGenerationService._create_caso_uso_com_classes(data=data_documento, user=user, job=job)
        
        # Definir parUC_CD
        if (data_documento.get('TipoDocumento') == 'CASO_USO' or data_documento.get('TipoDocumento') == 'DIAGRAMA_CLASSE'):
                # Se foi passado, utilize ele
                if data_documento.get('parUC_CD'):
                    par_doc_id = data_documento.get('parUC_CD')
                    par_doc = get_object_or_404(Documento, id=par_doc_id)
                    data_documento['parUC_CD'] = par_doc.id
                # Se não foi passado, tente manter o par da versão anterior
                else:
                    if documento_anterior:
                        doc_anterior = get_object_or_404(Documento, id=documento_anterior)
                        if (doc_anterior.TipoDocumento in ['CASO_USO', 'DIAGRAMA_CLASSE']) and doc_anterior.parUC_CD:
                            data_documento['parUC_CD'] = doc_anterior.parUC_CD.id
                        else:
                            data_documento['parUC_CD'] = None
                    else:
                        data_documento['parUC_CD'] = None

        # Casos simples
        # Se deve ser gerado por IA
        if is_empty_or_null(data_documento.get('arquivo')):
            result_string = send_to_llm(data_documento)
            generated_by_ai = True

            vMajor = 1
            vMinor = 0

            if is_empty_or_null(documento_anterior):
                vMajorAnterior = 0
                vMinorAnterior = 0
            else:
                doc_anterior = get_object_or_404(Documento, pk=documento_anterior)
                vMajorAnterior = doc_anterior.vMajor
                vMinorAnterior = doc_anterior.vMinor

            # Geração de uma nova Narrativa de Domínio
            if data_documento.get('TipoDocumento') == 'MINIMUNDO' and data_documento.get('audio_path'):
                # Baseada em novo áudio
                if documento_anterior:
                    vMajor = vMajorAnterior + 1
                    vMinor = 0
                #Se não tiver DocumentoAnterior, fica 1.0
                    
            else:
                doc_origem_id = data_documento['DocumentoOrigem'][-1]
                doc_origem = get_object_or_404(Documento, id=doc_origem_id) 
                vMajorOrigem = doc_origem.vMajor
                vMinorOrigem = doc_origem.vMinor

                if (vMajorOrigem, vMinorOrigem) >= (vMajorAnterior, vMinorAnterior):
                    vMajor = vMajorOrigem
                    vMinor = vMinorOrigem

                else:
                    vMajor = vMajorAnterior
                    vMinor = vMinorAnterior + 1

        # Se não deve ser gerado por IA
        else:
            generated_by_ai = False
            result_string = data_documento.get('arquivo')

            # Incremento Minor
            if documento_anterior:
                doc_anterior_id = documento_anterior
                doc_anterior = get_object_or_404(Documento, id=doc_anterior_id)
                vMajor, vMinor = update_version(doc_anterior)

            elif data_documento.get('DocumentoOrigem') and len(data_documento.get('DocumentoOrigem')) != 0:
                doc_origem_id = data_documento.get('DocumentoOrigem')[-1]
                doc_origem = get_object_or_404(Documento, id=doc_origem_id)
                vMajor, vMinor = version_from_another_doc(doc_origem)

            else:
                vMajor = 1
                vMinor = 0

        # Mesma lógica de montagem
        # result_string = ''
        # if not isinstance(result, str):
        #     for element in result:
        #         result_string += element + '\n<!-- -->\n'
        # else:
        #     result_string = result

        data_documento['vMajor'] = vMajor
        data_documento['vMinor'] = vMinor
        data_documento['arquivo'] = result_string
        data_documento['geradoIA'] = generated_by_ai
        data_documento['vMaisRecente'] = True

        serializer = DocumentoWriteSerializer(data=data_documento)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(user=user)

        # Caso tenha arquivo de áudio do upload, salvar no campo arquivoAudio
        if audio_path:
            with open(audio_path, "rb") as f:
                instance.arquivoAudio.save(
                    os.path.basename(audio_path),
                    File(f),
                    save=False
                )
        # (Reuso) Apontar para arquivo de áudio do DocumentoAnterior (só para MINIMUNDO)
        elif arquivoAudio_name:
            instance.arquivoAudio.name = arquivoAudio_name
        # Em outros casos, garantir que é None
        else:
            instance.arquivoAudio = None
        
        instance.save(update_fields=['arquivoAudio'])

        # Atualizar parUC_CD relacionado, caso seja UC ou CD gerado por IA
        if data_documento.get('parUC_CD') and (data_documento.get('TipoDocumento') == 'CASO_USO' or data_documento.get('TipoDocumento') == 'DIAGRAMA_CLASSE') and generated_by_ai:
            par_doc_id = data_documento.get('parUC_CD')
            par_doc = get_object_or_404(Documento, id=par_doc_id)
            par_doc.parUC_CD = instance
            par_doc.save(update_fields=['parUC_CD'])

        # Atualizar estado de novidade do documento anterior
        if documento_anterior:
            doc_anterior = get_object_or_404(Documento, id=documento_anterior)
            if doc_anterior.vMaisRecente is not False:
                doc_anterior.vMaisRecente = False
                doc_anterior.save(update_fields=['vMaisRecente'])

        return instance
    
    @staticmethod
    def _create_caso_uso_com_classes(data, user, job):
        documento_anterior = data.get("DocumentoAnterior")
        previous_uc_id = None
        previous_cd_id = None

        if documento_anterior:
            doc_anterior = get_object_or_404(Documento, id=documento_anterior)
            if doc_anterior.TipoDocumento == 'CASO_USO':
                previous_uc_id = doc_anterior.id
                previous_cd_id = getattr(doc_anterior.parUC_CD, 'id', None)
            elif doc_anterior.TipoDocumento == 'DIAGRAMA_CLASSE':
                previous_cd_id = doc_anterior.id
                previous_uc_id = getattr(doc_anterior.parUC_CD, 'id', None)


        # Ambos gerados juntos, por IA
        if data.get('TipoDocumento') == 'CASO_USO_E_DIAGRAMA_CLASSE':
            # Pode ser duas coisas:
            # Gerar os dois pela primeira vez, sem documento anterior
            # Ou gerar uma nova versão dos dois
            result = send_to_llm({
            **data,
            'TipoDocumento': data.get('TipoDocumento')
            })

            if not result:
                return Response({'error': 'Erro ao gerar documentos'}, status=500)

            caso_uso_result = result.get('caso_uso')
            diagrama_classe_result = result.get('diagrama_classe')

            # montar UC
            result_string_uc = ''
            for element in caso_uso_result:
                result_string_uc += element + '\n<!-- -->\n'

            # Versionamento
            vMajor, vMinor = 1, 0

            doc_origem_id = data.get('DocumentoOrigem')[-1]
            doc_origem = get_object_or_404(Documento, id=doc_origem_id)
            vMajorOrigem = doc_origem.vMajor
            vMinorOrigem = doc_origem.vMinor
            vMajorAnteriorUC = 0
            vMinorAnteriorUC = 0

            if previous_uc_id:
                previous_uc = get_object_or_404(Documento, id=previous_uc_id)
                # Como UC e CD têm sempre a mesma versão, pode-se utilizar a mesma versão para ambos
                vMajorAnteriorUC = previous_uc.vMajor
                vMinorAnteriorUC = previous_uc.vMinor

            if (vMajorOrigem, vMinorOrigem) >= (vMajorAnteriorUC, vMinorAnteriorUC):
                vMajor = vMajorOrigem
                vMinor = vMinorOrigem
            else:
                vMajor = vMajorAnteriorUC
                vMinor = vMinorAnteriorUC + 1

            # CASO USO
            data_uc = data.copy()
            data_uc.update({
                'arquivo': result_string_uc,
                'TipoDocumento': 'CASO_USO',
                'vMajor': vMajor,
                'vMinor': vMinor,
                'geradoIA': True,
                'vMaisRecente': True,
                'DocumentoAnterior': previous_uc_id,
            })

            serializer_uc = DocumentoWriteSerializer(data=data_uc)
            serializer_uc.is_valid(raise_exception=True)
            serializer_uc.save(user=user)

            # CLASSES
            data_cd = data.copy()
            data_cd.update({
                'arquivo': diagrama_classe_result,
                'TipoDocumento': 'DIAGRAMA_CLASSE',
                'vMajor': vMajor,
                'vMinor': vMinor,
                'geradoIA': True,
                'vMaisRecente': True,
                'DocumentoAnterior': previous_cd_id,
            })

            serializer_cd = DocumentoWriteSerializer(data=data_cd)
            serializer_cd.is_valid(raise_exception=True)
            serializer_cd.save(user=user)

            uc_instance = serializer_uc.instance
            cd_instance = serializer_cd.instance
            uc_instance.parUC_CD = cd_instance
            uc_instance.save(update_fields=['parUC_CD'])
            cd_instance.parUC_CD = uc_instance
            cd_instance.save(update_fields=['parUC_CD'])

            # Atualizar estado de novidade do documento anterior
            if documento_anterior:
                doc_anterior = get_object_or_404(Documento, id=documento_anterior)
                if doc_anterior.vMaisRecente is not False:
                    doc_anterior.vMaisRecente = False
                    doc_anterior.save(update_fields=['vMaisRecente'])
                if getattr(doc_anterior, 'parUC_CD', None) and doc_anterior.parUC_CD.vMaisRecente is not False:
                    doc_anterior.parUC_CD.vMaisRecente = False
                    doc_anterior.parUC_CD.save(update_fields=['vMaisRecente'])

            return cd_instance

            
        # Se for qualquer outro caso, joga pra essa função que vai criar os dois documentos adequadamente, com IA ou não
        else:
            return DocumentoGenerationService._create_uploaded_uc_cd(data=data, user=user, job=job)
    

    @staticmethod
    def _create_uploaded_uc_cd(data, user, job):
        tipo_documento = data.get('TipoDocumento')
        is_caso_uso = tipo_documento.startswith('CASO_USO')
        is_update = tipo_documento.endswith('_ATUALIZAR')

        # Define o tipo do documento principal e do par
        actual_tipo = 'CASO_USO' if is_caso_uso else 'DIAGRAMA_CLASSE'
        pair_tipo = 'DIAGRAMA_CLASSE' if is_caso_uso else 'CASO_USO'

        documento_anterior = data.get('DocumentoAnterior')
        old_doc = get_object_or_404(Documento, id=documento_anterior) if documento_anterior else None
        pair_previous = getattr(old_doc, 'parUC_CD', None) if old_doc else None

        # Criar documento principal
        data_main = data.copy()
        data_main.update({
            'TipoDocumento': actual_tipo, # Substituir o tipo corretamente (nada de CASO_USO_SIMPLES, etc)
            'geradoIA': False,
            'vMaisRecente': True,
        })

        # Definir versão do documento principal
        vMajor, vMinor = DocumentoGenerationService._compute_uploaded_version(data=data_main)
        data_main['vMajor'] = vMajor
        data_main['vMinor'] = vMinor

        # Criar o documento principal
        serializer_main = DocumentoWriteSerializer(data=data_main)
        serializer_main.is_valid(raise_exception=True)
        serializer_main.save(user=user)
        main_doc = serializer_main.instance

        # Criar o documento par
        pair_doc = None
        if is_update or pair_previous:
            # A princípio, o par recebe os mesmos dados do documento principal, 
            # exceto pelo tipo, pelo relacionamento de versão com o documento anterior do par (se existir),
            # vMaisRecente e parUC_CD
            pair_data = data.copy()
            pair_data.update({
                'TipoDocumento': pair_tipo,
                'DocumentoAnterior': getattr(pair_previous, 'id', None),
                'vMaisRecente': True,
                'parUC_CD': main_doc.id,
            })

            # Se for atualização, o par é gerado por IA.
            if is_update:
                pair_data['geradoIA'] = True

                main_origin_ids = list(main_doc.DocumentoOrigem.values_list('id', flat=True))
                pair_data['DocumentoOrigem'] = main_origin_ids.copy()

                # pair_origin_ids = main_origin_ids.copy()

                # if pair_previous and pair_previous.id not in pair_origin_ids:
                #     pair_origin_ids.append(pair_previous.id)
                # if main_doc.id not in pair_origin_ids:
                #     pair_origin_ids.append(main_doc.id)

                print("\n\nDados enviados para IA:", pair_data)
                pair_content = send_to_llm(pair_data)
                print("Pair_content:", pair_content, "\n\n")

               
                if not isinstance(pair_content, str):
                    pair_content = '' if pair_content is None else '\n<!-- -->\n'.join(pair_content)

                if not pair_content and pair_previous:
                    pair_content = pair_previous.arquivo or ''

                pair_data['arquivo'] = pair_content
            # Se for criação simples, o par continua com mesmo conteúdo que o seu anterior
            else:
                pair_data['geradoIA'] = False
                if pair_previous:
                    pair_data['arquivo'] = pair_previous.arquivo
                    pair_data['DocumentoOrigem'] = list(pair_previous.DocumentoOrigem.values_list('id', flat=True))
                else:
                    pair_data['arquivo'] = ''
                    pair_data['DocumentoOrigem'] = data.get('DocumentoOrigem', [])

            if pair_previous:
                pair_vMajor, pair_vMinor = update_version(pair_previous)
            else:
                pair_vMajor, pair_vMinor = 1, 0

            pair_data['vMajor'] = pair_vMajor
            pair_data['vMinor'] = pair_vMinor

            serializer_pair = DocumentoWriteSerializer(data=pair_data)
            serializer_pair.is_valid(raise_exception=True)
            serializer_pair.save(user=user)
            pair_doc = serializer_pair.instance

            main_doc.parUC_CD = pair_doc
            main_doc.save(update_fields=['parUC_CD'])
            pair_doc.parUC_CD = main_doc
            pair_doc.save(update_fields=['parUC_CD'])

        if documento_anterior:
            if old_doc and old_doc.vMaisRecente is not False:
                old_doc.vMaisRecente = False
                old_doc.save(update_fields=['vMaisRecente'])
            if old_doc and getattr(old_doc, 'parUC_CD', None) and old_doc.parUC_CD.vMaisRecente is not False:
                old_doc.parUC_CD.vMaisRecente = False
                old_doc.parUC_CD.save(update_fields=['vMaisRecente'])

        response_data = serializer_main.data
        # if pair_doc:
        #     response_data['parUC_CD'] = serializer_pair.data

        return main_doc
    
    @staticmethod
    def _compute_uploaded_version(data):
        documento_anterior = data.get('DocumentoAnterior')

        if documento_anterior:
            doc_anterior = get_object_or_404(Documento, id=documento_anterior)
            return update_version(doc_anterior)

        if data.get('DocumentoOrigem') and len(data.get('DocumentoOrigem')) != 0:
            doc_origem_id = data.get('DocumentoOrigem')[-1]
            doc_origem = get_object_or_404(Documento, id=doc_origem_id)
            return version_from_another_doc(doc_origem)

        return 1, 0