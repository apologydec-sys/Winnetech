"""
Run this script to set up initial data:
  python setup_data.py

Creates:
  - Superuser admin with special credentials
  - Full weekly timetable
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'winnitech.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import TimetableEntry
from datetime import time

# ── Special Admin Credentials ─────────────────────────────────
ADMIN_USERNAME = 'WTI_Admin'
ADMIN_PASSWORD = 'Winnitech@2026#Admin'
ADMIN_EMAIL    = 'admin@winnitech.edu.gh'

if not User.objects.filter(username=ADMIN_USERNAME).exists():
    User.objects.create_superuser(
        username=ADMIN_USERNAME,
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
        first_name='WTI',
        last_name='Administrator'
    )
    print(f'✅ Superuser created')
else:
    # Update password in case it changed
    admin = User.objects.get(username=ADMIN_USERNAME)
    admin.set_password(ADMIN_PASSWORD)
    admin.save()
    print('ℹ️  Superuser already exists — password updated')

# ── Timetable ─────────────────────────────────────────────────
TimetableEntry.objects.all().delete()

entries = [
    # MONDAY
    dict(day='monday', subject='Mathematics', start_time=time(8,0), end_time=time(10,0), is_break=False, course_type='electives'),
    dict(day='monday', subject='Break Time', start_time=time(10,0), end_time=time(10,45), is_break=True, course_type=''),
    dict(day='monday', subject='English Language', start_time=time(10,45), end_time=time(12,15), is_break=False, course_type='electives'),
    dict(day='monday', subject='Break Time', start_time=time(12,15), end_time=time(13,5), is_break=True, course_type=''),
    dict(day='monday', subject='Social Studies', start_time=time(13,5), end_time=time(15,30), is_break=False, course_type='electives'),
    # TUESDAY
    dict(day='tuesday', subject='Science', start_time=time(8,0), end_time=time(10,0), is_break=False, course_type='electives'),
    dict(day='tuesday', subject='Break Time', start_time=time(10,0), end_time=time(10,45), is_break=True, course_type=''),
    dict(day='tuesday', subject='EST (Entrepreneur Skills Training)', start_time=time(10,45), end_time=time(12,15), is_break=False, course_type='electives'),
    dict(day='tuesday', subject='Break Time', start_time=time(12,15), end_time=time(13,5), is_break=True, course_type=''),
    dict(day='tuesday', subject='ICT', start_time=time(13,5), end_time=time(15,30), is_break=False, course_type='electives'),
    # WEDNESDAY
    dict(day='wednesday', subject='Mathematics', start_time=time(8,0), end_time=time(9,0), is_break=False, course_type='electives'),
    dict(day='wednesday', subject='Social Studies', start_time=time(9,0), end_time=time(10,0), is_break=False, course_type='electives'),
    dict(day='wednesday', subject='Break Time', start_time=time(10,0), end_time=time(11,0), is_break=True, course_type=''),
    dict(day='wednesday', subject='English Language', start_time=time(11,0), end_time=time(12,0), is_break=False, course_type='electives'),
    dict(day='wednesday', subject='ICT', start_time=time(12,0), end_time=time(13,45), is_break=False, course_type='electives'),
    dict(day='wednesday', subject='Break Time', start_time=time(13,0), end_time=time(13,45), is_break=True, course_type=''),
    dict(day='wednesday', subject='EST (Entrepreneur Skills Training)', start_time=time(13,45), end_time=time(14,0), is_break=False, course_type='electives'),
    dict(day='wednesday', subject='Science', start_time=time(14,0), end_time=time(15,30), is_break=False, course_type='electives'),
    # THURSDAY
    dict(day='thursday', subject='Department', start_time=time(8,0), end_time=time(10,0), is_break=False, course_type='departmental'),
    dict(day='thursday', subject='Break Time', start_time=time(10,0), end_time=time(10,45), is_break=True, course_type=''),
    dict(day='thursday', subject='Break Time', start_time=time(12,15), end_time=time(13,5), is_break=True, course_type=''),
    dict(day='thursday', subject='Department', start_time=time(13,5), end_time=time(15,30), is_break=False, course_type='departmental'),
    # FRIDAY
    dict(day='friday', subject='Department', start_time=time(8,0), end_time=time(10,0), is_break=False, course_type='departmental'),
    dict(day='friday', subject='Break Time', start_time=time(10,0), end_time=time(10,45), is_break=True, course_type=''),
    dict(day='friday', subject='Break Time', start_time=time(12,15), end_time=time(13,5), is_break=True, course_type=''),
    dict(day='friday', subject='Department', start_time=time(13,5), end_time=time(15,30), is_break=False, course_type='departmental'),
]

for e in entries:
    TimetableEntry.objects.create(**e)

print(f'✅ Created {len(entries)} timetable entries')
print()
print('=' * 50)
print('ADMIN LOGIN CREDENTIALS')
print('=' * 50)
print(f'  Username : {ADMIN_USERNAME}')
print(f'  Password : {ADMIN_PASSWORD}')
print(f'  URL      : /admin-portal/')
print('=' * 50)
