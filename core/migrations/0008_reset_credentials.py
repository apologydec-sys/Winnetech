"""
Reset all admin credentials to the definitive production values.

Super Admin: username=WTISuperAdmin  password=WTI@Super2026!  → /superadmin-portal/
Admin:       username=WTIAdmin       password=WTI@Admin2026!  → /login/
"""
from django.db import migrations


def reset_credentials(apps, schema_editor):
    from django.contrib.auth.models import User
    from core.models import AdminProfile

    # ── Super Admin ──────────────────────────────────────────────────────────
    sa_username = 'WTISuperAdmin'
    sa_password = 'WTI@Super2026!'

    sa_users = User.objects.filter(is_superuser=True)
    if sa_users.exists():
        for u in sa_users:
            u.username = sa_username
            u.set_password(sa_password)
            u.is_staff = True
            u.is_active = True
            u.save()
            AdminProfile.objects.update_or_create(user=u, defaults={'role': 'superadmin'})
    else:
        u = User.objects.create_superuser(
            username=sa_username,
            password=sa_password,
            email='superadmin@winnitech.edu.gh',
            first_name='WTI',
            last_name='SuperAdmin',
        )
        AdminProfile.objects.create(user=u, role='superadmin')

    # ── Admin ─────────────────────────────────────────────────────────────────
    admin_username = 'WTIAdmin'
    admin_password = 'WTI@Admin2026!'

    # Remove any old stale admin accounts
    User.objects.filter(is_staff=True, is_superuser=False).delete()

    admin_user = User.objects.create_user(
        username=admin_username,
        password=admin_password,
        email='admin@winnitech.edu.gh',
        first_name='WTI',
        last_name='Admin',
        is_staff=True,
        is_active=True,
    )
    AdminProfile.objects.create(user=admin_user, role='admin')

    print('=== ADMIN ACCOUNTS READY ===')
    print(f'Super Admin: {sa_username}  →  /superadmin-portal/')
    print(f'Admin:       {admin_username}  →  /login/')


class Migration(migrations.Migration):
    dependencies = [('core', '0007_fix_qr_valid_until')]
    operations = [migrations.RunPython(reset_credentials, migrations.RunPython.noop)]
