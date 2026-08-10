import json
import os

from .models import (
    Projeto,
    Modulo,
    Documento,
    DocumentoGenerationJob,
    UserAIConfig,
    DOCS
)
from .serializers import (
    ProjetoReadSerializer, ProjetoWriteSerializer,
    ModuloReadSerializer, ModuloWriteSerializer,
    DocumentoReadSerializer, DocumentoWriteSerializer,
    DocumentoGenerationJobSerializer,
    UserAIConfigSerializer,
    UserRegisterSerializer,
)

from .tasks import generate_documento as generate_documento_task

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db.models import Case, When, IntegerField
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet, ModelViewSet, ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_condition import And, Or
from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope, OAuth2Authentication
from rest_framework.authentication import SessionAuthentication
from .pagination import CustomPagination
from rest_framework import generics
from rest_framework import filters
import django_filters.rest_framework
import logging
import requests
import uuid

logger = logging.getLogger(__name__)

from rest_framework.permissions import AllowAny # for testing
from .filters import DocumentoFilter
from .utils import is_empty_or_null, send_to_llm, version_from_another_doc, version_from_audio, update_version, persist_uploaded_audio

class HealthViewSet(ViewSet):

    permission_classes = [AllowAny]

    @action(detail='', url_path='')
    def check(self, request):
        response_data = {'content': 'OK'}
        return JsonResponse(response_data, status=201)


class ProjetoViewSet(ModelViewSet):
    queryset = Projeto.objects.all()
    pagination_class = CustomPagination
    authentication_classes = [OAuth2Authentication, SessionAuthentication]
    permission_classes = [Or(IsAdminUser, IsAuthenticated, TokenHasReadWriteScope)]

    # permission_classes = [AllowAny]

    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.rest_framework.DjangoFilterBackend
    )
    filterset_fields = '__all__'
    search_fields = ['nome', 'descricao']
    ordering_fields = '__all__'
    ordering = ["id"]
    
    def get_serializer_class(self):
        if self.request.method in ['GET']:
            return ProjetoReadSerializer
        return ProjetoWriteSerializer
    
    def get_object(self):
        '''
        return the Projeto and the associated Modulo's objects
        '''

        queryset = self.filter_queryset(self.get_queryset())

        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('projeto_modulo')
        
        obj = get_object_or_404(queryset, **self.kwargs)
        
        self.check_object_permissions(self.request, obj)
        return obj
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return Projeto.objects.filter(user=self.request.user)

class ModuloViewSet(ModelViewSet):
    queryset = Modulo.objects.all()
    pagination_class = CustomPagination
    authentication_classes = [OAuth2Authentication, SessionAuthentication]
    permission_classes = permission_classes = [Or(IsAdminUser, TokenHasReadWriteScope)]

    # permission_classes = [AllowAny]

    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.rest_framework.DjangoFilterBackend
    )
    filterset_fields = '__all__'
    search_fields = ['nome', 'descricao']
    ordering_fields = '__all__'
    ordering = ["id"]
    
    def get_serializer_class(self):
        if self.request.method in ['GET']:
            return ModuloReadSerializer
        return ModuloWriteSerializer
    
    def get_object(self) -> any:
        queryset = self.filter_queryset(self.get_queryset())

        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('modulo_documento')
        
        obj = get_object_or_404(queryset, **self.kwargs)
        
        self.check_object_permissions(self.request, obj)
        return obj
    
    @action(detail=False, methods=['get'], url_path=r'get_last_docs/(?P<modulo_id>\d+)', filter_backends=[])
    def get_last_docs(self, request, modulo_id=None):

        mod = get_object_or_404(Modulo, id=int(modulo_id))

        docs = mod.modulo_documento.filter(
            vMaisRecente=True
        ).order_by(
            Case(
                When(TipoDocumento='MINIMUNDO', then=0),
                When(TipoDocumento='REQUISITOS', then=1),
                When(TipoDocumento='CASO_USO', then=2),
                When(TipoDocumento='DIAGRAMA_CLASSE', then=3),
                output_field=IntegerField()
            )
        )

        return Response(
            DocumentoReadSerializer(docs, many=True).data
        )
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return Modulo.objects.filter(user=self.request.user)

class DocumentoViewSet(ModelViewSet):
    queryset = Documento.objects.all()
    pagination_class = CustomPagination
    authentication_classes = [OAuth2Authentication, SessionAuthentication]
    permission_classes = [Or(IsAdminUser, TokenHasReadWriteScope)]
    parser_classes = (MultiPartParser, FormParser)

    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.rest_framework.DjangoFilterBackend
    )
    filterset_fields = [
        'id',
        'vMajor',
        'vMinor',
        'geradoIA',
        'vMaisRecente',
        'obsoleto',
        'TipoDocumento',
        'DocumentoAnterior',
        'DocumentoOrigem',
        'parUC_CD',
        'Modulo',
    ]
    search_fields = ['versao', 'arquivo']
    ordering_fields = '__all__'
    ordering = ["id"]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Documento.objects.none()
        return Documento.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return DocumentoReadSerializer
        return DocumentoWriteSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        # Validar se o usuário tem uma chave de API configurada
        user_config = UserAIConfig.objects.filter(user=request.user).first()
        if not user_config or not user_config.api_key:
            logger.warning(
                "Tentativa de gerar documento sem API key configurada",
                extra={"user_id": request.user.id, "username": request.user.username}
            )
            return Response(
                {
                    "error": "Você não configurou uma chave de API de IA. Por favor, configure uma chave antes de gerar documentos.",
                    "error_code": "NO_AI_API_KEY_CONFIGURED"
                },
                status=403
            )

        data = {}

        for key, value in request.data.items():
            if key != "arquivoAudio":
                data[key] = value

        arquivoAudio = request.FILES.get('arquivoAudio')
        documento_anterior = data.get('DocumentoAnterior')
        
        documentos_origem = request.data.getlist('DocumentoOrigem')
        # Força sempre lista no data, e nunca string
        data['DocumentoOrigem'] = documentos_origem

        logger.info("FILES:", extra={"files": request.FILES})
        logger.info("audio:", extra={
            "existeAudio": bool(request.FILES.get('arquivoAudio')),
            "sizeAudio": getattr(request.FILES.get('arquivoAudio'), 'size', None)
        })

        if not arquivoAudio:
            data.pop('arquivoAudio', None)

        # Payload para a task
        payload = {
            "documento_data": data
        }
        
        # Persistir o áudio em um diretório compartilhado para o worker do Celery
        if arquivoAudio:
            payload["audio_path"] = persist_uploaded_audio(
                arquivoAudio,
                filename=getattr(arquivoAudio, 'name', None)
            )

        # Reuso de arquivo senão houver upload e tiver documento anterior
        elif documento_anterior:
            doc_anterior = get_object_or_404(Documento, pk=documento_anterior)
            
            if (data.get("TipoDocumento") == "MINIMUNDO" and doc_anterior.arquivoAudio):
                payload["arquivoAudio_name"] = (doc_anterior.arquivoAudio.name)

        try:
            json.dumps(payload)
        except TypeError as e:
            print("Payload inválido:", e)

            for key, value in payload.items():
                print(key, type(value))

                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        print(
                            f"  {subkey}: {type(subvalue)}"
                        )

            raise

        job = DocumentoGenerationJob.objects.create(
            id=uuid.uuid4(),
            user=request.user,
            status="PENDING"
        )
        
        generate_documento_task.delay(
            job_id=str(job.id),
            user_id=request.user.id,
            payload=payload
        )
        
        return Response(
            {
                "job_id": str(job.id),
                "status": "PENDING"
            },
            status=202
        )

class DocumentoGenerationJobViewSet(ReadOnlyModelViewSet):
    def get_queryset(self):
        return (DocumentoGenerationJob.objects.filter(user=self.request.user))
    
    serializer_class = (DocumentoGenerationJobSerializer)
    authentication_classes = [
        OAuth2Authentication,
        SessionAuthentication
    ]
    permission_classes = [
        Or(IsAdminUser, TokenHasReadWriteScope)
    ]
    lookup_field = 'id'
    
class UserAIConfigView(generics.GenericAPIView):
    serializer_class = UserAIConfigSerializer
    authentication_classes = [OAuth2Authentication, SessionAuthentication]
    permission_classes = [Or(IsAdminUser, IsAuthenticated, TokenHasReadWriteScope)]

    def get_object(self):
        return UserAIConfig.objects.filter(user=self.request.user).first()

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance:
            return Response({
                'configured': False,
                'masked_key': None,
                'provider': UserAIConfig.Providers.GEMINI,
            })
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        if instance:
            serializer.save()
        else:
            serializer.save(user=request.user)
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if instance:
            serializer.save()
        else:
            serializer.save(user=request.user)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance:
            return Response(status=404)
        instance.delete()
        return Response(status=204)


class UserViewSet(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permissions_classes = [AllowAny]