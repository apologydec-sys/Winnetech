"""
Management command: setup_admins

Creates or updates the superadmin and admin accounts with fixed credentials.
Runs automatically on every deploy via build.sh.

Super Admin  →  username: WTISuperAdmin  password: WTI@Super2026!
              login at: /superadmin-portal/

Admin        →  username: WTIAdmin       password: WTI@Admin2026!
              login at: /login/
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction


SUPERADMIN_USERNAME = 'WTI_SuperAdmin'
SUPERADMIN_PASSWORD = 'Wnn@Tech#9271'

ADMIN_USERNAME = 'WTIAdmin'
ADMIN_PASSWORD = 'WTI@Admin2026!'


class Command(BaseCommand):
    help = 'Create or update superadmin and admin accounts.'

    def handle(self, *args, **options):
        from core.models import AdminProfile

        with transaction.atomic():

            # ── Super Admin ───────────────────────────────────────────────
            sa_user, sa_created = User.objects.get_or_create(
                username=SUPERADMIN_USERNAME,
                defaults={
                    'email': 'superadmin@winnitech.edu.gh',
                    'first_name': 'WTI',
                    'last_name': 'SuperAdmin',
                    'is_staff': True,
                    'is_superuser': True,
                    'is_active': True,
                }
            )
            sa_user.set_password(SUPERADMIN_PASSWORD)
            sa_user.is_staff = True
            sa_user.is_superuser = True
            sa_user.is_active = True
            sa_user.save()

            AdminProfile.objects.update_or_create(
                user=sa_user,
                defaults={'role': 'superadmin'}
            )

            label = 'Created' if sa_created else 'Updated'
            self.stdout.write(self.style.SUCCESS(
                f'{label} Super Admin: {SUPERADMIN_USERNAME}  →  /superadmin-portal/'
            ))

            # ── Admin ─────────────────────────────────────────────────────
            admin_user, admin_created = User.objects.get_or_create(
                username=ADMIN_USERNAME,
                defaults={
                    'email': 'admin@winnitech.edu.gh',
                    'first_name': 'WTI',
                    'last_name': 'Admin',
                    'is_staff': True,
                    'is_superuser': False,
                    'is_active': True,
                }
            )
            admin_user.set_password(ADMIN_PASSWORD)
            admin_user.is_staff = True
            admin_user.is_superuser = False
            admin_user.is_active = True
            admin_user.save()

            AdminProfile.objects.update_or_create(
                user=admin_user,
                defaults={'role': 'admin'}
            )

            label = 'Created' if admin_created else 'Updated'
            self.stdout.write(self.style.SUCCESS(
                f'{label} Admin:       {ADMIN_USERNAME}  →  /login/'
            ))

        self.stdout.write(self.style.SUCCESS('Admin accounts ready.'))
