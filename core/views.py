import qrcode
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
        return user.admin_profile.role == 'superadmin'
    except Exception:
        return user.is_superuser


# ── Welcome ───────────────────────────────────────────────────────────────────

def welcome(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            try:
                if request.user.admin_profile.role == 'superadmin':
                    return redirect('superadmin_dashboard')
            except Exception:
                if request.user.is_superuser:
                    return redirect('superadmin_dashboard')
            return redirect('admin_dashboard')
        return redirect('teacher_dashboard')
    return render(request, 'welcome.html')


def service_worker(request):
    import os
    from django.conf import settings
    from django.http import FileResponse, Http404
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'sw.js')
    if not os.path.exists(sw_path):
        raise Http404
    response = FileResponse(open(sw_path, 'rb'), content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache'
    return response


def offline_page(request):
    return render(request, 'offline.html')


# ── Auth ──────────────────────────────────────────────────────────────────────

def teacher_register(request):
    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(request, f'Registration successful! Welcome {user.get_full_name()}. Awaiting admin approval.')
                return redirect('teacher_login')
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
        else:
            errs = []
            for field, errors in form.errors.items():
                label = form.fields[field].label if field in form.fields else field
                for err in errors:
                    errs.append(f'{label}: {err}' if label else err)
            messages.error(request, 'Fix: ' + ' | '.join(errs) if errs else 'Please correct errors.')
    else:
        form = TeacherRegistrationForm()
    return render(request, 'auth/register.html', {'form': form})


def teacher_login(request):
    if request.user.is_authenticated and not request.user.is_staff:
        return redirect('teacher_dashboard')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is None:
            error = 'Invalid username or password.'
        elif user.is_staff:
            error = 'Please use the Admin Portal to login as admin.'
        else:
            try:
                profile = user.teacher_profile
                if not profile.is_approved:
                    error = 'Your account is pending admin approval.'
                else:
                    login(request, user)
                    return redirect('teacher_dashboard')
            except TeacherProfile.DoesNotExist:
                error = 'Teacher profile not found.'
    return render(request, 'auth/teacher_login.html', {'error': error})


def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        try:
            if request.user.admin_profile.role == 'superadmin':
                return redirect('superadmin_dashboard')
        except Exception:
            pass
        return redirect('admin_dashboard')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is None:
            error = 'Invalid username or password.'
        elif not user.is_staff:
            error = 'This account does not have admin privileges.'
        elif not user.is_active:
            error = 'This account is disabled.'
        else:
            try:
                if user.admin_profile.role == 'superadmin':
                    error = 'Please use the Super Admin Portal.'
                else:
                    login(request, user)
                    return redirect('admin_dashboard')
            except Exception:
                login(request, user)
                return redirect('admin_dashboard')
    return render(request, 'auth/admin_login.html', {'error': error})


def superadmin_login(request):
    if request.user.is_authenticated and is_superadmin(request.user):
        return redirect('superadmin_dashboard')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is None:
            error = 'Invalid username or password.'
        elif not user.is_staff:
            error = 'No admin privileges.'
        elif not is_superadmin(user):
            error = 'This is the Super Admin portal. Use Admin Portal for regular admin login.'
        else:
            login(request, user)
            return redirect('superadmin_dashboard')
    return render(request, 'auth/superadmin_login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('welcome')


# ── Teacher Dashboard ─────────────────────────────────────────────────────────

@login_required
def teacher_dashboard(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')
    try:
        profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('welcome')

    today = timezone.localdate()
    today_att = Attendance.objects.filter(teacher=profile, date=today).first()
    all_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:20]
    unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False).count()
    day_name = today.strftime('%A').lower()
    today_schedule = TimetableEntry.objects.filter(day=day_name, is_break=False, teacher=profile)
    upcoming_schedules = ClassSchedule.objects.filter(
        teacher=profile, scheduled_date__gte=today, is_completed=False
    ).order_by('scheduled_date', 'timetable_entry__start_time')[:5]

    # Active QR codes for scanning
    school_qr = QRCode.objects.filter(qr_type='school_attendance', is_active=True).first()
    lesson_qr = QRCode.objects.filter(qr_type='lesson', is_active=True).first()

    return render(request, 'teacher/dashboard.html', {
        'profile': profile,
        'today_att': today_att,
        'all_notifications': all_notifications,
        'unread_notifications': unread_notifications,
        'today_schedule': today_schedule,
        'upcoming_schedules': upcoming_schedules,
        'today': today,
        'school_qr': school_qr,
        'lesson_qr': lesson_qr,
    })


@login_required
def mark_notification_read(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notif.is_read = True
    notif.save()
    return JsonResponse({'status': 'ok'})


@login_required
def qr_scanner(request):
    return render(request, 'qr/scanner.html')


@login_required
def view_timetable(request):
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    timetable_by_day = [(d, list(TimetableEntry.objects.filter(day=d).order_by('start_time'))) for d in days]
    try:
        profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        profile = None
    all_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:20]
    unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return render(request, 'timetable.html', {
        'timetable_by_day': timetable_by_day, 'days': days,
        'profile': profile,
        'all_notifications': all_notifications,
        'unread_notifications': unread_notifications,
    })


# ── QR Scanning ───────────────────────────────────────────────────────────────

def scan_school_qr(request, qr_uuid):
    qr_obj = get_object_or_404(QRCode, code=qr_uuid, qr_type='school_attendance', is_active=True)
    today = timezone.localdate()
    now = timezone.localtime().time()
    if not qr_obj.is_valid_today:
        return render(request, 'qr/scan_result.html', {'success': False, 'message': 'This QR code has expired.'})
    if not request.user.is_authenticated:
        return redirect(f'/login/?next=/scan/school/{qr_uuid}/')
    if request.user.is_staff:
        return render(request, 'qr/scan_result.html', {'success': False, 'message': 'Admins do not scan attendance.'})
    try:
        profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return render(request, 'qr/scan_result.html', {'success': False, 'message': 'Teacher profile not found.'})

    att, created = Attendance.objects.get_or_create(
        teacher=profile, date=today,
        defaults={'school_qr': qr_obj, 'check_in_time': now, 'school_status': 'present'}
    )
    if not created and att.school_status == 'absent':
        att.school_qr = qr_obj
        att.check_in_time = now
        att.school_status = 'present'
        att.save()

    msg = f'{profile.full_name} checked in at {now.strftime("%H:%M")}.' if created else f'{profile.full_name} already checked in.' 
    for admin in User.objects.filter(is_staff=True):
        Notification.objects.create(
            recipient=admin, sender=request.user,
            title=f'School Attendance: {profile.full_name}',
            message=msg, notification_type='attendance'
        )
    return render(request, 'qr/scan_result.html', {
        'success': True, 'scan_type': 'school', 'message': msg,
        'teacher': profile, 'time': now.strftime('%H:%M')
    })


def scan_lesson_qr(request, qr_uuid):
    qr_obj = get_object_or_404(QRCode, code=qr_uuid, qr_type='lesson', is_active=True)
    today = timezone.localdate()
    now = timezone.localtime().time()
    if not qr_obj.is_valid_today:
        return render(request, 'qr/scan_result.html', {'success': False, 'message': 'This QR code has expired.'})
    if not request.user.is_authenticated:
        return redirect(f'/login/?next=/scan/lesson/{qr_uuid}/')
    if request.user.is_staff:
        return render(request, 'qr/scan_result.html', {'success': False, 'message': 'Admins do not scan lessons.'})
    try:
        profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return render(request, 'qr/scan_result.html', {'success': False, 'message': 'Teacher profile not found.'})

    att, created = Attendance.objects.get_or_create(
        teacher=profile, date=today,
        defaults={'lesson_qr': qr_obj, 'lesson_done_time': now, 'lesson_status': 'done'}
    )
    if not created:
        att.lesson_qr = qr_obj
        att.lesson_done_time = now
        att.lesson_status = 'done'
        att.save()

    msg = f'{profile.full_name} completed lesson at {now.strftime("%H:%M")}.' 
    for admin in User.objects.filter(is_staff=True):
        Notification.objects.create(
            recipient=admin, sender=request.user,
            title=f'Lesson Done: {profile.full_name}',
            message=msg, notification_type='attendance'
        )
    return render(request, 'qr/scan_result.html', {
        'success': True, 'scan_type': 'lesson', 'message': msg,
        'teacher': profile, 'time': now.strftime('%H:%M')
    })


# ── Admin Dashboard ───────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    today = timezone.localdate()
    approved_teachers = TeacherProfile.objects.filter(is_approved=True).select_related('user')
    pending_teachers = TeacherProfile.objects.filter(is_approved=False)
    today_att = Attendance.objects.filter(date=today).select_related('teacher__user')
    present_count = today_att.filter(school_status='present').count()
    absent_count = approved_teachers.count() - present_count
    recent_notifs = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:10]
    school_qr = QRCode.objects.filter(qr_type='school_attendance', is_active=True).first()
    lesson_qr = QRCode.objects.filter(qr_type='lesson', is_active=True).first()
    day_name = today.strftime('%A').lower()
    today_timetable = TimetableEntry.objects.filter(day=day_name).order_by('start_time')

    # Group teachers by department/course_type
    from .models import DEPARTMENT_CHOICES
    departments = {}
    for val, label in DEPARTMENT_CHOICES:
        dept_teachers = approved_teachers.filter(department=val)
        if dept_teachers.exists():
            departments[label] = dept_teachers
    core_teachers = approved_teachers.filter(course_type='core')
    if core_teachers.exists():
        departments['Core Subjects'] = core_teachers

    return render(request, 'admin/dashboard.html', {
        'approved_teachers': approved_teachers,
        'pending_teachers': pending_teachers,
        'today_att': today_att,
        'present_count': present_count,
        'absent_count': absent_count,
        'total_teachers': approved_teachers.count(),
        'recent_notifs': recent_notifs,
        'school_qr': school_qr,
        'lesson_qr': lesson_qr,
        'today_timetable': today_timetable,
        'today': today,
        'departments': departments,
    })


@login_required
@user_passes_test(is_admin)
def teacher_detail(request, teacher_id):
    """Admin can only VIEW QR codes, not generate them."""
    school_qrs = QRCode.objects.filter(qr_type='school_attendance').order_by('-created_at')
    lesson_qrs = QRCode.objects.filter(qr_type='lesson').order_by('-created_at')
    return render(request, 'admin/qr_view.html', {
        'school_qrs': school_qrs,
        'lesson_qrs': lesson_qrs,
    })


@login_required
@user_passes_test(is_admin)
def admin_department_view(request, dept_slug):
    """Show all teachers in a specific department with their attendance."""
    from .models import DEPARTMENT_CHOICES
    dept_map = dict(DEPARTMENT_CHOICES)
    dept_name = dept_map.get(dept_slug, dept_slug.replace('_', ' ').title())

    if dept_slug == 'core':
        teachers = TeacherProfile.objects.filter(
            is_approved=True, course_type='core'
        ).select_related('user')
        dept_name = 'Core Subjects'
    else:
        teachers = TeacherProfile.objects.filter(
            is_approved=True, department=dept_slug
        ).select_related('user')

    today = timezone.localdate()
    # Get today's attendance for these teachers
    teacher_ids = teachers.values_list('id', flat=True)
    today_att = Attendance.objects.filter(
        date=today, teacher_id__in=teacher_ids
    ).select_related('teacher__user')
    att_map = {a.teacher_id: a for a in today_att}

    teacher_data = []
    for t in teachers:
        att = att_map.get(t.id)
        teacher_data.append({
            'teacher': t,
            'attendance': att,
            'school_status': att.school_status if att else 'absent',
            'lesson_status': att.lesson_status if att else 'pending',
            'check_in': att.check_in_time if att else None,
            'lesson_done': att.lesson_done_time if att else None,
        })

    return render(request, 'admin/department_view.html', {
        'dept_name': dept_name,
        'dept_slug': dept_slug,
        'teacher_data': teacher_data,
        'today': today,
        'total': teachers.count(),
        'present': sum(1 for d in teacher_data if d['school_status'] == 'present'),
        'lesson_done': sum(1 for d in teacher_data if d['lesson_status'] == 'done'),
    })


@login_required
@user_passes_test(is_superadmin)
def qr_detail_sa(request, qr_id):
    """Super admin QR detail view."""
    return qr_detail(request, qr_id)


@login_required
@user_passes_test(is_admin)
def admin_teachers(request):
    teachers = TeacherProfile.objects.select_related('user').all().order_by('-date_joined')
    return render(request, 'admin/teachers.html', {'teachers': teachers})
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    attendances = Attendance.objects.filter(teacher=teacher).order_by('-date')[:30]
    return render(request, 'admin/teacher_detail.html', {'teacher': teacher, 'attendances': attendances})


@login_required
@user_passes_test(is_admin)
def approve_teacher(request, teacher_id):
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    teacher.is_approved = True
    teacher.save()
    Notification.objects.create(
        recipient=teacher.user, sender=request.user,
        title='Account Approved',
        message='Your teacher account has been approved. You can now login.',
        notification_type='admin'
    )
    messages.success(request, f'{teacher.full_name} approved.')
    return redirect('admin_teachers')


@login_required
@user_passes_test(is_admin)
def reject_teacher(request, teacher_id):
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    name = teacher.full_name
    teacher.user.delete()
    messages.warning(request, f'{name} rejected and removed.')
    return redirect('admin_teachers')


@login_required
@user_passes_test(is_admin)
def delete_teacher(request, teacher_id):
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    if request.method == 'POST':
        name = teacher.full_name
        teacher.user.delete()
        messages.success(request, f'{name} permanently deleted.')
        return redirect('admin_teachers')
    return render(request, 'admin/confirm_delete.html', {'teacher': teacher})


@login_required
@user_passes_test(is_admin)
def admin_attendance(request):
    today = timezone.localdate()
    selected_date = request.GET.get('date', str(today))
    try:
        from datetime import date as dt
        selected_date = dt.fromisoformat(selected_date)
    except ValueError:
        selected_date = today
    attendances = Attendance.objects.filter(date=selected_date).select_related('teacher__user')
    approved_teachers = TeacherProfile.objects.filter(is_approved=True)
    present_ids = attendances.filter(school_status='present').values_list('teacher_id', flat=True)
    absent_teachers = approved_teachers.exclude(id__in=present_ids)
    lesson_done_ids = attendances.filter(lesson_status='done').values_list('teacher_id', flat=True)
    lesson_not_done = approved_teachers.exclude(id__in=lesson_done_ids)
    return render(request, 'admin/attendance.html', {
        'attendances': attendances,
        'absent_teachers': absent_teachers,
        'lesson_not_done': lesson_not_done,
        'selected_date': selected_date,
        'today': today,
    })


@login_required
@user_passes_test(is_admin)
def admin_timetable(request):
    if request.method == 'POST':
        form = TimetableEntryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Timetable entry added.')
            return redirect('admin_timetable')
    else:
        form = TimetableEntryForm()
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    timetable_by_day = [(d, list(TimetableEntry.objects.filter(day=d).order_by('start_time'))) for d in days]
    return render(request, 'admin/timetable.html', {'form': form, 'timetable_by_day': timetable_by_day, 'days': days})


@login_required
@user_passes_test(is_admin)
def delete_timetable_entry(request, entry_id):
    get_object_or_404(TimetableEntry, id=entry_id).delete()
    messages.success(request, 'Entry deleted.')
    return redirect('admin_timetable')


@login_required
@user_passes_test(is_admin)
def admin_schedule(request):
    if request.method == 'POST':
        form = ClassScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            schedule.save()
            Notification.objects.create(
                recipient=schedule.teacher.user, sender=request.user,
                title=f'Class Scheduled: {schedule.timetable_entry.subject}',
                message=f'You teach {schedule.timetable_entry.subject} on {schedule.scheduled_date} from {schedule.timetable_entry.start_time.strftime("%H:%M")} to {schedule.timetable_entry.end_time.strftime("%H:%M")}.',
                notification_type='schedule', related_timetable=schedule.timetable_entry
            )
            messages.success(request, f'Scheduled and {schedule.teacher.full_name} notified.')
            return redirect('admin_schedule')
    else:
        form = ClassScheduleForm()
    schedules = ClassSchedule.objects.select_related('teacher__user', 'timetable_entry').order_by('-scheduled_date')[:50]
    return render(request, 'admin/schedule.html', {'form': form, 'schedules': schedules})


@login_required
@user_passes_test(is_admin)
def admin_notifications(request):
    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            notif = form.save(commit=False)
            notif.sender = request.user
            notif.save()
            messages.success(request, 'Notification sent.')
            return redirect('admin_notifications')
    else:
        form = NotificationForm()
    sent = Notification.objects.filter(sender=request.user).order_by('-created_at')[:30]
    return render(request, 'admin/notifications.html', {'form': form, 'sent_notifications': sent})


@login_required
@user_passes_test(is_admin)
def admin_qr_view(request):
    """Admin can only VIEW QR codes — generation is superadmin only."""
    school_qrs = QRCode.objects.filter(qr_type='school_attendance').order_by('-created_at')
    lesson_qrs = QRCode.objects.filter(qr_type='lesson').order_by('-created_at')
    return render(request, 'admin/qr_view.html', {
        'school_qrs': school_qrs,
        'lesson_qrs': lesson_qrs,
    })


@login_required
@user_passes_test(is_superadmin)
def generate_qr(request):
    if request.method == 'POST':
        form = QRCodeForm(request.POST)
        if form.is_valid():
            qr_obj = form.save(commit=False)
            qr_obj.created_by = request.user
            qr_obj.save()
            scan_path = f'/scan/school/{qr_obj.code}/' if qr_obj.qr_type == 'school_attendance' else f'/scan/lesson/{qr_obj.code}/'
            scan_url = request.build_absolute_uri(scan_path)
            img = qrcode.make(scan_url)
            buf = __import__('io').BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            qr_obj.qr_image.save(f'qr_{qr_obj.code}.png', ContentFile(buf.read()), save=True)
            messages.success(request, f'{qr_obj.get_qr_type_display()} QR Code generated! Valid for 5 years.')
            return redirect('qr_detail', qr_id=qr_obj.id)
    else:
        form = QRCodeForm()
    school_qrs = QRCode.objects.filter(qr_type='school_attendance').order_by('-created_at')
    lesson_qrs = QRCode.objects.filter(qr_type='lesson').order_by('-created_at')
    return render(request, 'admin/qr_generate.html', {'form': form, 'school_qrs': school_qrs, 'lesson_qrs': lesson_qrs})


@login_required
@user_passes_test(is_admin)
def qr_detail(request, qr_id):
    qr_obj = get_object_or_404(QRCode, id=qr_id)
    scan_path = f'/scan/school/{qr_obj.code}/' if qr_obj.qr_type == 'school_attendance' else f'/scan/lesson/{qr_obj.code}/'
    scan_url = request.build_absolute_uri(scan_path)
    img = qrcode.make(scan_url)
    buf = __import__('io').BytesIO()
    img.save(buf, format='PNG')
    qr_b64 = __import__('base64').b64encode(buf.getvalue()).decode()
    return render(request, 'admin/qr_detail.html', {'qr_obj': qr_obj, 'scan_url': scan_url, 'qr_b64': qr_b64})


# ── API ───────────────────────────────────────────────────────────────────────

@login_required
def get_notifications_api(request):
    notifs = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')[:10]
    data = [{'id': n.id, 'title': n.title, 'message': n.message, 'type': n.notification_type, 'time': n.created_at.strftime('%H:%M')} for n in notifs]
    return JsonResponse({'notifications': data, 'count': len(data)})


@login_required
def get_schedule_reminders_api(request):
    if request.user.is_staff:
        return JsonResponse({'schedules': []})
    try:
        profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return JsonResponse({'schedules': []})
    today = timezone.localdate()
    now = timezone.localtime().time()
    schedules = ClassSchedule.objects.filter(teacher=profile, scheduled_date=today, is_completed=False).select_related('timetable_entry')
    data = []
    for s in schedules:
        start = s.timetable_entry.start_time
        diff = (datetime.combine(today, start) - datetime.combine(today, now)).total_seconds() / 60
        data.append({'id': s.id, 'subject': s.timetable_entry.subject, 'start_time': start.strftime('%H:%M'), 'end_time': s.timetable_entry.end_time.strftime('%H:%M'), 'minutes_until': round(diff)})
    return JsonResponse({'schedules': data})


@login_required
def mark_schedule_complete(request, schedule_id):
    if request.method == 'POST':
        try:
            profile = request.user.teacher_profile
            schedule = get_object_or_404(ClassSchedule, id=schedule_id, teacher=profile)
            schedule.is_completed = True
            schedule.save()
            return JsonResponse({'status': 'ok'})
        except TeacherProfile.DoesNotExist:
            return JsonResponse({'status': 'error'}, status=403)
    return JsonResponse({'status': 'error'}, status=405)


# ── Super Admin ───────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_superadmin)
def superadmin_dashboard(request):
    admins = User.objects.filter(is_staff=True).select_related('admin_profile')
    teachers = TeacherProfile.objects.select_related('user').all()
    pending = teachers.filter(is_approved=False)
    today = timezone.localdate()
    today_att = Attendance.objects.filter(date=today)
    return render(request, 'superadmin/dashboard.html', {
        'admins': admins, 'teachers': teachers, 'pending': pending,
        'total_admins': admins.count(), 'total_teachers': teachers.count(),
        'pending_count': pending.count(),
        'present_today': today_att.filter(school_status='present').count(),
        'today': today,
    })


@login_required
@user_passes_test(is_superadmin)
def superadmin_admins(request):
    admins = User.objects.filter(is_staff=True).select_related('admin_profile').order_by('username')
    return render(request, 'superadmin/admins.html', {'admins': admins})


@login_required
@user_passes_test(is_superadmin)
def superadmin_create_admin(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        if not username or not password:
            error = 'Username and password are required.'
        elif User.objects.filter(username=username).exists():
            error = f'Username "{username}" already exists.'
        else:
            new_user = User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name, email=email, is_staff=True, is_active=True)
            AdminProfile.objects.create(user=new_user, role='admin', created_by=request.user)
            messages.success(request, f'Admin "{username}" created.')
            return redirect('superadmin_admins')
    return render(request, 'superadmin/create_admin.html', {'error': error})


@login_required
@user_passes_test(is_superadmin)
def superadmin_delete_admin(request, admin_id):
    admin_user = get_object_or_404(User, id=admin_id, is_staff=True)
    if admin_user == request.user:
        messages.error(request, 'Cannot delete your own account.')
        return redirect('superadmin_admins')
    try:
        if admin_user.admin_profile.role == 'superadmin':
            messages.error(request, 'Cannot delete another Super Admin.')
            return redirect('superadmin_admins')
    except Exception:
        pass
    if request.method == 'POST':
        name = admin_user.get_full_name() or admin_user.username
        admin_user.delete()
        messages.success(request, f'Admin "{name}" deleted.')
        return redirect('superadmin_admins')
    return render(request, 'superadmin/confirm_delete_admin.html', {'admin_user': admin_user})


@login_required
@user_passes_test(is_superadmin)
def superadmin_teachers(request):
    teachers = TeacherProfile.objects.select_related('user').all().order_by('-date_joined')
    return render(request, 'superadmin/teachers.html', {'teachers': teachers})


@login_required
@user_passes_test(is_superadmin)
def superadmin_approve_teacher(request, teacher_id):
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    teacher.is_approved = True
    teacher.save()
    Notification.objects.create(
        recipient=teacher.user, sender=request.user,
        title='Account Approved',
        message='Your teacher account has been approved by the Super Admin. You can now login.',
        notification_type='admin'
    )
    messages.success(request, f'{teacher.full_name} approved.')
    return redirect('superadmin_teachers')


@login_required
@user_passes_test(is_superadmin)
def superadmin_delete_teacher(request, teacher_id):
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    if request.method == 'POST':
        name = teacher.full_name
        teacher.user.delete()
        messages.success(request, f'{name} deleted.')
        return redirect('superadmin_teachers')
    return render(request, 'superadmin/confirm_delete_teacher.html', {'teacher': teacher})
