content = '''import qrcode
import io
import base64
from datetime import datetime, date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from django.core.files.base import ContentFile

from .models import (
    TeacherProfile, Attendance, QRCode, Notification,
    TimetableEntry, ClassSchedule, AdminProfile
)
from .forms import (
    TeacherRegistrationForm, TeacherLoginForm,
    NotificationForm, TimetableEntryForm, ClassScheduleForm, QRCodeForm
)


# ── Role checks ───────────────────────────────────────────────────────────────

def is_admin(user):
    return user.is_authenticated and user.is_staff

def is_superadmin(user):
    if not (user.is_authenticated and user.is_staff):
        return False
    try:
        return user.admin_profile.role == \'superadmin\'
    except Exception:
        return user.is_superuser


# ── Welcome ───────────────────────────────────────────────────────────────────

def welcome(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            try:
                if request.user.admin_profile.role == \'superadmin\':
                    return redirect(\'superadmin_dashboard\')
            except Exception:
                if request.user.is_superuser:
                    return redirect(\'superadmin_dashboard\')
            return redirect(\'admin_dashboard\')
        return redirect(\'teacher_dashboard\')
    return render(request, \'welcome.html\')


def service_worker(request):
    import os
    from django.conf import settings
    from django.http import FileResponse, Http404
    sw_path = os.path.join(settings.BASE_DIR, \'static\', \'js\', \'sw.js\')
    if not os.path.exists(sw_path):
        raise Http404
    response = FileResponse(open(sw_path, \'rb\'), content_type=\'application/javascript\')
    response[\'Service-Worker-Allowed\'] = \'/\'
    response[\'Cache-Control\'] = \'no-cache\'
    return response


def offline_page(request):
    return render(request, \'offline.html\')


# ── Auth ──────────────────────────────────────────────────────────────────────

def teacher_register(request):
    if request.method == \'POST\':
        form = TeacherRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(request, f\'Registration successful! Welcome {user.get_full_name()}. Awaiting admin approval.\')
                return redirect(\'teacher_login\')
            except Exception as e:
                messages.error(request, f\'Registration failed: {str(e)}\')
        else:
            errs = []
            for field, errors in form.errors.items():
                label = form.fields[field].label if field in form.fields else field
                for err in errors:
                    errs.append(f\'{label}: {err}\' if label else err)
            messages.error(request, \'Fix: \' + \' | \'.join(errs) if errs else \'Please correct errors.\')
    else:
        form = TeacherRegistrationForm()
    return render(request, \'auth/register.html\', {\'form\': form})


def teacher_login(request):
    if request.user.is_authenticated and not request.user.is_staff:
        return redirect(\'teacher_dashboard\')
    error = None
    if request.method == \'POST\':
        username = request.POST.get(\'username\', \'\').strip()
        password = request.POST.get(\'password\', \'\').strip()
        user = authenticate(request, username=username, password=password)
        if user is None:
            error = \'Invalid username or password.\'
        elif user.is_staff:
            error = \'Please use the Admin Portal to login as admin.\'
        else:
            try:
                profile = user.teacher_profile
                if not profile.is_approved:
                    error = \'Your account is pending admin approval.\'
                else:
                    login(request, user)
                    return redirect(\'teacher_dashboard\')
            except TeacherProfile.DoesNotExist:
                error = \'Teacher profile not found.\'
    return render(request, \'auth/teacher_login.html\', {\'error\': error})


def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        try:
            if request.user.admin_profile.role == \'superadmin\':
                return redirect(\'superadmin_dashboard\')
        except Exception:
            pass
        return redirect(\'admin_dashboard\')
    error = None
    if request.method == \'POST\':
        username = request.POST.get(\'username\', \'\').strip()
        password = request.POST.get(\'password\', \'\').strip()
        user = authenticate(request, username=username, password=password)
        if user is None:
            error = \'Invalid username or password.\'
        elif not user.is_staff:
            error = \'This account does not have admin privileges.\'
        elif not user.is_active:
            error = \'This account is disabled.\'
        else:
            try:
                if user.admin_profile.role == \'superadmin\':
                    error = \'Please use the Super Admin Portal.\'
                else:
                    login(request, user)
                    return redirect(\'admin_dashboard\')
            except Exception:
                login(request, user)
                return redirect(\'admin_dashboard\')
    return render(request, \'auth/admin_login.html\', {\'error\': error})


def superadmin_login(request):
    if request.user.is_authenticated and is_superadmin(request.user):
        return redirect(\'superadmin_dashboard\')
    error = None
    if request.method == \'POST\':
        username = request.POST.get(\'username\', \'\').strip()
        password = request.POST.get(\'password\', \'\').strip()
        user = authenticate(request, username=username, password=password)
        if user is None:
            error = \'Invalid username or password.\'
        elif not user.is_staff:
            error = \'No admin privileges.\'
        elif not is_superadmin(user):
            error = \'This is the Super Admin portal. Use Admin Portal for regular admin login.\'
        else:
            login(request, user)
            return redirect(\'superadmin_dashboard\')
    return render(request, \'auth/superadmin_login.html\', {\'error\': error})


def logout_view(request):
    logout(request)
    return redirect(\'welcome\')


# ── Teacher Dashboard ─────────────────────────────────────────────────────────

@login_required
def teacher_dashboard(request):
    if request.user.is_staff:
        return redirect(\'admin_dashboard\')
    try:
        profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        messages.error(request, \'Teacher profile not found.\')
        return redirect(\'welcome\')

    today = timezone.localdate()
    today_att = Attendance.objects.filter(teacher=profile, date=today).first()
    all_notifications = Notification.objects.filter(recipient=request.user).order_by(\'-created_at\')[:20]
    unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False).count()
    day_name = today.strftime(\'%A\').lower()
    today_schedule = TimetableEntry.objects.filter(day=day_name, is_break=False, teacher=profile)
    upcoming_schedules = ClassSchedule.objects.filter(
        teacher=profile, scheduled_date__gte=today, is_completed=False
    ).order_by(\'scheduled_date\', \'timetable_entry__start_time\')[:5]

    # Active QR codes for scanning
    school_qr = QRCode.objects.filter(qr_type=\'school_attendance\', is_active=True).first()
    lesson_qr = QRCode.objects.filter(qr_type=\'lesson\', is_active=True).first()

    return render(request, \'teacher/dashboard.html\', {
        \'profile\': profile,
        \'today_att\': today_att,
        \'all_notifications\': all_notifications,
        \'unread_notifications\': unread_notifications,
        \'today_schedule\': today_schedule,
        \'upcoming_schedules\': upcoming_schedules,
        \'today\': today,
        \'school_qr\': school_qr,
        \'lesson_qr\': lesson_qr,
    })


@login_required
def mark_notification_read(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notif.is_read = True
    notif.save()
    return JsonResponse({\'status\': \'ok\'})


@login_required
def qr_scanner(request):
    return render(request, \'qr/scanner.html\')


@login_required
def view_timetable(request):
    days = [\'monday\', \'tuesday\', \'wednesday\', \'thursday\', \'friday\']
    timetable_by_day = [(d, list(TimetableEntry.objects.filter(day=d).order_by(\'start_time\'))) for d in days]
    try:
        profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        profile = None
    all_notifications = Notification.objects.filter(recipient=request.user).order_by(\'-created_at\')[:20]
    unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return render(request, \'timetable.html\', {
        \'timetable_by_day\': timetable_by_day, \'days\': days,
        \'profile\': profile,
        \'all_notifications\': all_notifications,
        \'unread_notifications\': unread_notifications,
    })


# ── QR Scanning ───────────────────────────────────────────────────────────────

def scan_school_qr(request, qr_uuid):
    qr_obj = get_object_or_404(QRCode, code=qr_uuid, qr_type=\'school_attendance\', is_active=True)
    today = timezone.localdate()
    now = timezone.localtime().time()
    if not qr_obj.is_valid_today:
        return render(request, \'qr/scan_result.html\', {\'success\': False, \'message\': \'This QR code has expired.\'})
    if not request.user.is_authenticated:
        return redirect(f\'/login/?next=/scan/school/{qr_uuid}/\')
    if request.user.is_staff:
        return render(request, \'qr/scan_result.html\', {\'success\': False, \'message\': \'Admins do not scan attendance.\'})
    try:
        profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return render(request, \'qr/scan_result.html\', {\'success\': False, \'message\': \'Teacher profile not found.\'})

    att, created = Attendance.objects.get_or_create(
        teacher=profile, date=today,
        defaults={\'school_qr\': qr_obj, \'check_in_time\': now, \'school_status\': \'present\'}
    )
    if not created and att.school_status == \'absent\':
        att.school_qr = qr_obj
        att.check_in_time = now
        att.school_status = \'present\'
        att.save()

    msg = f\'{profile.full_name} checked in at {now.strftime("%H:%M")}.\' if created else f\'{profile.full_name} already checked in.\' 
    for admin in User.objects.filter(is_staff=True):
        Notification.objects.create(
            recipient=admin, sender=request.user,
            title=f\'School Attendance: {profile.full_name}\',
            message=msg, notification_type=\'attendance\'
        )
    return render(request, \'qr/scan_result.html\', {
        \'success\': True, \'scan_type\': \'school\', \'message\': msg,
        \'teacher\': profile, \'time\': now.strftime(\'%H:%M\')
    })


def scan_lesson_qr(request, qr_uuid):
    qr_obj = get_object_or_404(QRCode, code=qr_uuid, qr_type=\'lesson\', is_active=True)
    today = timezone.localdate()
    now = timezone.localtime().time()
    if not qr_obj.is_valid_today:
        return render(request, \'qr/scan_result.html\', {\'success\': False, \'message\': \'This QR code has expired.\'})
    if not request.user.is_authenticated:
        return redirect(f\'/login/?next=/scan/lesson/{qr_uuid}/\')
    if request.user.is_staff:
        return render(request, \'qr/scan_result.html\', {\'success\': False, \'message\': \'Admins do not scan lessons.\'})
    try:
        profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return render(request, \'qr/scan_result.html\', {\'success\': False, \'message\': \'Teacher profile not found.\'})

    att, created = Attendance.objects.get_or_create(
        teacher=profile, date=today,
        defaults={\'lesson_qr\': qr_obj, \'lesson_done_time\': now, \'lesson_status\': \'done\'}
    )
    if not created:
        att.lesson_qr = qr_obj
        att.lesson_done_time = now
        att.lesson_status = \'done\'
        att.save()

    msg = f\'{profile.full_name} completed lesson at {now.strftime("%H:%M")}.\' 
    for admin in User.objects.filter(is_staff=True):
        Notification.objects.create(
            recipient=admin, sender=request.user,
            title=f\'Lesson Done: {profile.full_name}\',
            message=msg, notification_type=\'attendance\'
        )
    return render(request, \'qr/scan_result.html\', {
        \'success\': True, \'scan_type\': \'lesson\', \'message\': msg,
        \'teacher\': profile, \'time\': now.strftime(\'%H:%M\')
    })

'''
with open('core/views_part1.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('views part1 written')
