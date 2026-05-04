"""
Custom management command to create the WTI admin user.
Run: python manage.py create_admin
Called automatically during Render build.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create the WTI admin superuser'

    def handle(self, *args, **options):
        username = 'WTI_Admin'
        password = 'Winnitech@2026'
        email = 'admin@winnitech.edu.gh'

        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save()
            self.stdout.write(self.style.SUCCESS(
                f'Admin updated: {username} / {password}'
            ))
        else:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name='WTI',
                last_name='Administrator',
            )
            self.stdout.write(self.style.SUCCESS(
                f'Admin created: {username} / {password}'
            ))
