import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0004_adminprofile'),
    ]

    operations = [
        # ── Update QRCode model ──────────────────────────────────────────────
        migrations.AddField(
            model_name='qrcode',
            name='qr_type',
            field=models.CharField(
                choices=[('school_attendance', 'School Attendance'), ('lesson', 'Lesson')],
                default='school_attendance', max_length=20
            ),
        ),
        migrations.AddField(
            model_name='qrcode',
            name='valid_from',
            field=models.DateField(default=datetime.date.today),
        ),
        migrations.AddField(
            model_name='qrcode',
            name='valid_until',
            field=models.DateField(null=True, blank=True),
        ),
        # Remove old date field
        migrations.RemoveField(model_name='qrcode', name='date'),

        # ── Update Attendance model ──────────────────────────────────────────
        # Add new fields
        migrations.AddField(
            model_name='attendance',
            name='school_qr',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='school_attendances', to='core.qrcode'
            ),
        ),
        migrations.AddField(
            model_name='attendance',
            name='school_status',
            field=models.CharField(
                choices=[('present', 'Present'), ('absent', 'Absent'), ('late', 'Late')],
                default='absent', max_length=10
            ),
        ),
        migrations.AddField(
            model_name='attendance',
            name='lesson_qr',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='lesson_attendances', to='core.qrcode'
            ),
        ),
        migrations.AddField(
            model_name='attendance',
            name='lesson_status',
            field=models.CharField(
                choices=[('done', 'Lesson Done'), ('not_done', 'Lesson Not Done'), ('pending', 'Pending')],
                default='pending', max_length=10
            ),
        ),
        # Remove old fields
        migrations.RemoveField(model_name='attendance', name='qr_code'),
        migrations.RemoveField(model_name='attendance', name='status'),
        migrations.RemoveField(model_name='attendance', name='scan_type'),

        # ── Update superadmin credentials ────────────────────────────────────
        migrations.RunPython(
            lambda apps, se: _update_superadmin(apps, se),
            migrations.RunPython.noop,
        ),

        # ── Remove ChatMessage model ─────────────────────────────────────────
        migrations.DeleteModel(name='ChatMessage'),
    ]


def _update_superadmin(apps, schema_editor):
    from django.contrib.auth.models import User as RealUser
    AdminProfile = apps.get_model('core', 'AdminProfile')
    new_username = 'WTI_SuperAdmin'
    new_password = 'WTI@Super#2026'
    for u in RealUser.objects.filter(is_superuser=True):
        if u.username == 'admin':
            u.username = new_username
            u.first_name = 'WTI'
            u.last_name = 'SuperAdmin'
        u.set_password(new_password)
        u.save()
        AdminProfile.objects.update_or_create(
            user_id=u.id,
            defaults={'role': 'superadmin'}
        )
