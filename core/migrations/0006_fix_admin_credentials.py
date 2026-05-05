from django.db import migrations


def create_default_admin(apps, schema_editor):
    """Create a default admin account with known credentials."""
    from django.contrib.auth.models import User
    from core.models import AdminProfile

    username = 'WTI_Admin'
    password = 'Admin@WTI2026'

    if not User.objects.filter(username=username).exists():
        u = User.objects.create_user(
            username=username,
            password=password,
            first_name='WTI',
            last_name='Admin',
            email='admin@winnitech.edu.gh',
            is_staff=True,
            is_active=True,
        )
        AdminProfile.objects.get_or_create(user=u, defaults={'role': 'admin'})
        print(f'Admin created: {username} / {password}')
    else:
        u = User.objects.get(username=username)
        u.set_password(password)
        u.is_staff = True
        u.is_active = True
        u.save()
        AdminProfile.objects.get_or_create(user=u, defaults={'role': 'admin'})
        print(f'Admin updated: {username} / {password}')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_update_qr_attendance'),
    ]

    operations = [
        migrations.RunPython(create_default_admin, migrations.RunPython.noop),
    ]
