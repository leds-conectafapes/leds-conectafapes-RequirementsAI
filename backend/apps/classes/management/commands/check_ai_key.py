from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import connection

from apps.classes.models import UserAIConfig
from apps.classes.serializers import UserAIConfigSerializer


class Command(BaseCommand):
    help = 'Check storage and retrieval of User AI API key for a given username (local/dev use only).'

    def add_arguments(self, parser):
        parser.add_argument('--username', '-u', required=True, help='Username to inspect')

    def handle(self, *args, **options):
        username = options.get('username')
        User = get_user_model()

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User "{username}" does not exist')

        config = UserAIConfig.objects.filter(user=user).first()

        if not config:
            self.stdout.write(self.style.WARNING(f'No UserAIConfig found for user "{username}"'))
            return

        # Serializer provides masked_key and configured
        serialized = UserAIConfigSerializer(config).data

        self.stdout.write(self.style.SUCCESS(f'Found UserAIConfig for "{username}"'))
        self.stdout.write(f'  provider: {serialized.get("provider")}')
        self.stdout.write(f'  configured: {serialized.get("configured")}')
        self.stdout.write(f'  masked_key: {serialized.get("masked_key")}')

        # Accessing config.api_key uses the EncryptedTextField to return decrypted value
        try:
            decrypted = config.api_key
        except Exception as e:
            decrypted = f'<error retrieving decrypted value: {e}>'

        self.stdout.write(f'  decrypted (in-memory): {decrypted}')

        # Raw value in DB (likely encrypted)
        with connection.cursor() as cursor:
            cursor.execute('SELECT api_key FROM user_ai_config WHERE user_id = %s', [user.id])
            row = cursor.fetchone()
            raw_db = row[0] if row else None

        self.stdout.write(f'  raw_db_value: {raw_db}')

        if raw_db and raw_db == decrypted:
            self.stdout.write(self.style.WARNING('Raw DB value equals decrypted value (unexpected).'))

        self.stdout.write(self.style.SUCCESS('Check complete.'))
