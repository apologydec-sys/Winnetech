"""
Reset all admin credentials to clean simple ones.

Super Admin: username=WTISuperAdmin  password=super2026
Admin:       username=WTIAdmin       password=admin2026
             (Admin Staff ID = WTIAdmin, used to login at /admin-portal/)
"""
from django.db import migrations


def reset_credentials(apps, schema_editor):
    from django.contrib.auth.models import User
    from core.models import AdminProfile

    # ── Super Admin ──────────────────────────────────────────────────────────
    sa_username = 'WTISuperAdmin'
    sa_password = 'super2026'

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
            username=sa_username, password=sa_password,
            email='superadmin@winnitech.edu.gh',
            first_name='WTI', last_name='SuperAdmin'
        )
        AdminProfile.objects.create(user=u, role='superadmin')

    # ── Admin ─────────────────────────────────────────────────────────────────
    # Admin Staff ID = WTIAdmin (used as username for login)
    admin_username = 'WTIAdmin'
    admin_password = 'admin2026'

    # Remove old admin accounts (except superadmin)
    User.objects.filter(is_staff=True, is_superuser=False).delete()

    # Create fresh admin
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

    print('=== CREDENTIALS RESET ===')
    print(f'Super Admin: {sa_username} / {sa_password}  → /superadmin-portal/')
    print(f'Admin:       {admin_username} / {admin_password}  → /admin-portal/ (Staff ID login)')


class Migration(migrations.Migration):
    dependencies = [('core', '0007_fix_qr_valid_until')]
    operations = [migrations.RunPython(reset_credentials, migrations.RunPython.noop)]
