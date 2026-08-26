from django.db import migrations


def create_superadmin(apps, schema_editor):
    from django.contrib.auth.models import User

    username = 'WTI_SuperAdmin'
    password = 'Wnn@Tech#9271'

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            email='superadmin@winnitech.edu.gh',
            password=password,
            first_name='WTI',
            last_name='SuperAdmin',
        )
    else:
        u = User.objects.get(username=username)
        u.set_password(password)
        u.is_staff = True
        u.is_superuser = True
        u.is_active = True
        u.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_teacherprofile_department'),
    ]

    operations = [
        migrations.RunPython(create_superadmin, migrations.RunPython.noop),
    ]
