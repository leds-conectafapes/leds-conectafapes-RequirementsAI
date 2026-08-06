from rest_framework import serializers, generics
from django.contrib.auth.models import User

from .models import (
    Projeto,
    Modulo,
    Documento,
    DocumentoGenerationJob,
    UserAIConfig,
)


class DocumentoGenerationJobSerializer(serializers.ModelSerializer):

    documento_id = serializers.UUIDField(
        source='documento.id',
        read_only=True
    )
    class Meta:
        model = DocumentoGenerationJob
        fields = [
            'id',
            'status',
            'progress',
            'documento_id',
            'error',
            'created_at',
            'finished_at',
        ]
class DocumentoWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documento
        exclude = ("polymorphic_ctype",)
        read_only_fields = ("user",)

class DocumentoReadSerializer(serializers.ModelSerializer):
    class Meta:
        depth = 1
        model = Documento
        exclude = ("polymorphic_ctype",)

class ModuloWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modulo
        exclude = ("polymorphic_ctype",)
        read_only_fields = ("user",)

class ModuloReadSerializer(serializers.ModelSerializer):
    modulo_documento = DocumentoReadSerializer(many=True, read_only=True)

    class Meta:
        depth = 1
        model = Modulo
        exclude = ("polymorphic_ctype",)

class ProjetoWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Projeto
        exclude = ("polymorphic_ctype",)
        read_only_fields = ("user",)


class ProjetoReadSerializer(serializers.ModelSerializer):
    projeto_modulo = ModuloReadSerializer(many=True, read_only=True)

    class Meta:
        depth = 1
        model = Projeto
        exclude = ("polymorphic_ctype",)


class UserAIConfigSerializer(serializers.ModelSerializer):
    api_key = serializers.CharField(write_only=True, required=False, allow_blank=False)
    configured = serializers.SerializerMethodField(read_only=True)
    masked_key = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserAIConfig
        fields = [
            'provider',
            'api_key',
            'configured',
            'masked_key',
        ]
        extra_kwargs = {
            'provider': {'required': False},
        }

    def get_configured(self, obj):
        return bool(obj and obj.api_key)

    def get_masked_key(self, obj):
        if not obj or not obj.api_key:
            return None

        raw_key = obj.api_key
        if len(raw_key) <= 8:
            return '*' * len(raw_key)

        visible_suffix = raw_key[-4:]
        return f'{raw_key[:3]}****{visible_suffix}' if raw_key.startswith('sk-') else f'****{visible_suffix}'

    def validate(self, data):
        if self.instance is None and not data.get('api_key'):
            raise serializers.ValidationError({'api_key': 'API Key é obrigatória.'})
        return data

    def create(self, validated_data):
        api_key = validated_data.pop('api_key', None)
        instance = UserAIConfig.objects.create(**validated_data, api_key=api_key)
        return instance

    def update(self, instance, validated_data):
        api_key = validated_data.pop('api_key', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if api_key is not None:
            instance.api_key = api_key
        instance.save()
        return instance


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user