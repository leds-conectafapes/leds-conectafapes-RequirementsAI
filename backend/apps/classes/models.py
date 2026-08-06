from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from polymorphic.models import PolymorphicModel

from .encryption import EncryptedTextField


User = get_user_model()

class DOCS(models.TextChoices):
    """"""
    MINIMUNDO = 'MINIMUNDO', _('Minimundo')
    REQUISITOS = 'REQUISITOS', _('Requisitos')
    CASO_USO = 'CASO_USO', _('Caso uso')
    DIAGRAMA_CLASSE = 'DIAGRAMA_CLASSE', _('Diagrama classe')
    PROTOTIPO_INTERFACE = 'PROTOTIPO_INTERFACE', _('Prototipo interface')


class Projeto(PolymorphicModel, models.Model):
    ''''''

    nome = models.CharField(max_length=300, null=True, blank=True)
    descricao = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projetos')

    class Meta:
        db_table = 'projeto'

class Modulo(PolymorphicModel, models.Model):
    ''''''

    nome = models.CharField(max_length=300, null=True, blank=True)
    descricao = models.TextField(null=True, blank=True)

    Projeto = models.ForeignKey('Projeto', blank=True, null=True, on_delete=models.CASCADE, related_name="projeto_%(class)s")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='modulos')


    class Meta:
        db_table = 'modulo'

class Documento(PolymorphicModel, models.Model):
    ''''''
    # versao do documento
    vMajor = models.IntegerField(null=True, blank=True)
    vMinor = models.IntegerField(null=True, blank=True)

    # tag gerado por IA
    geradoIA = models.BooleanField(null=True, blank=True)
    # tag ultima versão
    vMaisRecente = models.BooleanField(null=True, blank=True)
    obsoleto = models.BooleanField(default=False)

    # string do documento
    arquivo = models.TextField(null=True, blank=True)
    
    # audio de origem do documento (se houver)
    arquivoAudio = models.FileField(upload_to='audios/',null=True, blank=True)
    
    # id dos documentos de origem
    DocumentoOrigem = models.ManyToManyField('Documento', blank=True, null=True, symmetrical=False, related_name='documento_%(class)s_origem')
    
    # id da versao anterior do documento (se houver)
    DocumentoAnterior = models.ForeignKey('Documento', blank=True, null=True, on_delete=models.DO_NOTHING, related_name="documento_%(class)s_anteior")
    
    # par de CASO_USO <-> DIAGRAMA_CLASSE
    parUC_CD = models.ForeignKey('Documento', blank=True, null=True, on_delete=models.DO_NOTHING, related_name="documento_%(class)s_paruc_cd")

    # id do modulo que o documento pertence
    Modulo = models.ForeignKey('Modulo', blank=True, null=True, on_delete=models.CASCADE, related_name="modulo_%(class)s")
    
    # tipo do documento
    TipoDocumento = models.CharField(max_length=20, choices=DOCS.choices, default=DOCS.MINIMUNDO)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documentos')

    def atualizar_obsolescencia(self):
        documento_anterior = self.DocumentoAnterior

        # Herda obsolescência da versão anterior
        # exceto se foi regenerado por IA
        if (
            documento_anterior
            and documento_anterior.obsoleto
            and not self.geradoIA
        ):
            self.obsoleto = True
            return

        origens = self.DocumentoOrigem.all()

        if not origens.exists():
            self.obsoleto = False
            return

        self.obsoleto = any(
            doc.obsoleto or doc.vMaisRecente is False
            for doc in origens
        )

    def marcar_dependentes_como_obsoletos(self):
        dependentes = Documento.objects.filter(DocumentoOrigem=self)

        for doc in dependentes:
            doc.atualizar_obsolescencia()
            doc.save(update_fields=['obsoleto'], skip_obsolescencia=True)

    def save(self, *args, **kwargs):
        skip_obsolescencia = kwargs.pop('skip_obsolescencia', False)
        previous_vMaisRecente = None

        if self.TipoDocumento not in {DOCS.CASO_USO, DOCS.DIAGRAMA_CLASSE}:
            self.parUC_CD = None
        elif self.parUC_CD:
            if self.TipoDocumento == DOCS.CASO_USO and self.parUC_CD.TipoDocumento != DOCS.DIAGRAMA_CLASSE:
                self.parUC_CD = None
            elif self.TipoDocumento == DOCS.DIAGRAMA_CLASSE and self.parUC_CD.TipoDocumento != DOCS.CASO_USO:
                self.parUC_CD = None

        if self.pk and not skip_obsolescencia:
            previous_vMaisRecente = Documento.objects.filter(pk=self.pk).values_list('vMaisRecente', flat=True).first()

        super().save(*args, **kwargs)

        if skip_obsolescencia:
            return

        self.atualizar_obsolescencia()
        super().save(update_fields=['obsoleto'])

        if self.vMaisRecente is False and previous_vMaisRecente is not False:
            self.marcar_dependentes_como_obsoletos()

    class Meta:
        db_table = 'documento'

class DocumentoGenerationJob(models.Model):
    id = models.UUIDField(primary_key=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='documento_generation_jobs'
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("RUNNING", "Running"),
            ("SUCCESS", "Success"),
            ("FAILED", "Failed")
        ]
    )

    progress = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    finished_at = models.DateTimeField(
        null=True,
        blank=True
    )

    error = models.TextField(
        null=True,
        blank=True
    )

    documento = models.ForeignKey(
        Documento,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="generation_jobs"
    )


class UserAIConfig(models.Model):
    class Providers(models.TextChoices):
        OPENAI = 'openai', _('OpenAI')
        GEMINI = 'gemini', _('Gemini (Google)')

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_config'
    )
    provider = models.CharField(
        max_length=50,
        choices=Providers.choices,
        default=Providers.GEMINI,
    )
    api_key = EncryptedTextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_ai_config'
