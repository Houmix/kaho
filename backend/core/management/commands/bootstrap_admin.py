from decouple import config
from django.core.management.base import BaseCommand

from core.models import User


class Command(BaseCommand):
    help = "Crée (ou met à jour) le compte administrateur à partir de ADMIN_EMAIL / ADMIN_PASSWORD. Idempotent."

    def handle(self, *args, **options):
        email = config('ADMIN_EMAIL', default='').strip().lower()
        password = config('ADMIN_PASSWORD', default='')
        if not email or not password:
            self.stdout.write("ADMIN_EMAIL / ADMIN_PASSWORD absents : aucun admin créé.")
            return
        user, created = User.objects.get_or_create(
            username=email,
            defaults={
                'email': email,
                'first_name': config('ADMIN_FIRST_NAME', default='Admin'),
                'last_name': config('ADMIN_LAST_NAME', default='Kaho'),
            },
        )
        user.role = 'ADMIN'
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f"Admin {'créé' if created else 'mis à jour'} : {email}"))
