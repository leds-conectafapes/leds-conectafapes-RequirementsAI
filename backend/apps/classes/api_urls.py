from django.urls import path, register_converter, include
from rest_framework import routers
from .api_views import (
    ProjetoViewSet,
    ModuloViewSet,
    DocumentoViewSet,
    DocumentoGenerationJobViewSet,
    UserViewSet,
    UserAIConfigView,
    HealthViewSet,
)
router = routers.DefaultRouter()

router.register(r'projeto', ProjetoViewSet, basename='projeto')
router.register(r'modulo', ModuloViewSet, basename='modulo')
router.register(r'documento', DocumentoViewSet, basename='documento')
router.register(r'document-generation-jobs', DocumentoGenerationJobViewSet, basename='documento-generation-job')
router.register(r'health', HealthViewSet, basename='health')

urlpatterns = [
    path('classes/', include(router.urls)),
    path('register/', UserViewSet.as_view(), name='user-register'),
    path('classes/ai-config/', UserAIConfigView.as_view(), name='user-ai-config'),
    # path('classes/modulo/get_last_docs/<int:modulo_id>', , name='get_last_docs')
]


# urlpatterns = [
#     path('topics/<int:topic_id>/', views.topic, name='topic'),
# ]