from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models


def get_ai_key_encryption_key() -> bytes:
    key = getattr(settings, 'AI_CONFIG_ENCRYPTION_KEY', None)
    if not key:
        raise ImproperlyConfigured(
            'Missing AI_CONFIG_ENCRYPTION_KEY environment variable.'
        )
    return key.encode('utf-8') if isinstance(key, str) else key


def get_ai_key_fernet() -> Fernet:
    return Fernet(get_ai_key_encryption_key())


def encrypt_value(value: str) -> str:
    if value is None:
        return value
    return get_ai_key_fernet().encrypt(value.encode('utf-8')).decode('utf-8')


def decrypt_value(value: str) -> str:
    if value is None:
        return value
    try:
        return get_ai_key_fernet().decrypt(value.encode('utf-8')).decode('utf-8')
    except InvalidToken as exc:
        raise ValueError('Invalid encrypted value') from exc


def is_fernet_encrypted(value: str) -> bool:
    return isinstance(value, str) and value.startswith('gAAAA') and len(value) > 10


class EncryptedTextField(models.TextField):
    description = 'Text field encrypted with Fernet before storage.'

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt_value(value)

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, str) and is_fernet_encrypted(value):
            return decrypt_value(value)
        return value

    def get_prep_value(self, value):
        if value is None:
            return value
        if isinstance(value, str) and is_fernet_encrypted(value):
            return value
        return encrypt_value(value)
