import json
import qrcode
import io
import base64
from datetime import datetime, date, time, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q
from PIL import Image
from django.core.files.base import ContentFile

from .models import (
    TeacherProfile, Attendance, QRCode, Notification, ChatMessage,
    TimetableEntry, ClassSchedule
)
from .forms import (
    TeacherRegistrationForm, TeacherLoginForm, AdminLoginForm,
    NotificationForm, TimetableEntryForm, ClassScheduleForm,
    ChatMessageForm, QRCodeForm
)


def is_admin(user):
    return user.is_authenticated and user.is_staff


# ─── Welcome Page ─────────────────────────────────────────────────────────────

def welcome(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('teacher_dashboard')
    return render(request, 'welcome.html')


def service_worker(request):
    """Serve the service worker from root scope."""
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
    """Offline fallback page."""
    return render(request, 'offline.html')


# ─── Auth ─────────────────────────────────────────────────────────────────────

def teacher_register(request):
    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(
                    request,
                    f'Registration successful! Welcome {user.get_full_name()}. '
                    'Please wait for admin approval before logging in.'
                )
                return redirect('teacher_login')
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}. Please try again.')
        else:
            # Collect all errors into a readable message
            error_list = []
            for field, errors in form.errors.items():
                label = form.fields[field].label if field in form.fields else field
                for err in errors:
                    error_list.append(f'{label}: {err}' if label else err)
            if error_list:
                messages.error(request, 'Please fix the following: ' + ' | '.join(error_list))
            else:
                messages.error(request, 'Please correct the errors below.')
    else:
        form = TeacherRegistrationForm()
    return render(request, 'auth/register.html', {'form': form})


def teacher_login(request):
    if request.user.is_authenticated and not request.user.is_staff:
        return redirect('teacher_dashboard')
    if request.method == 'POST':
        form = TeacherLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_staff:
                messages.error(request, 'Please use the Admin Portal to login as admin.')
                return redirect('admin_login')
            try:
                profile = user.teacher_profile
                if not profile.is_approved:
                    messages.warning(request, 'Your account is pending admin approval.')
                    return redirect('teacher_login')
            except TeacherProfile.DoesNotExist:
                messages.error(request, 'Teacher profile not found.')
                return redirect('teacher_login')
            login(request, user)
            return redirect('teacher_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = TeacherLoginForm()
    return render(request, 'auth/teacher_login.html', {'form': form})


def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        if not username or not password:
            error = 'Please enter both username and password.'
        else:
            user = authenticate(request, username=username, password=password)
            if user is None:
                error = 'Invalid username or password.'
            elif not user.is_staff:
                error = 'This account does not have admin privileges.'
            elif not user.is_active:
                error = 'This account is disabled.'
            else:
                login(request, user)
                return redirect('admin_dashboard')
    return render(request, 'auth/admin_login.html', {'error': error})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('welcome')


# ─── Teacher Dashboard ────────────────────────────────────────────────────────

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
    today_attendance = Attendance.objects.filter(teacher=profile, date=today).first()
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')[:10]
    all_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:20]

    # Today's schedule
    day_name = today.strftime('%A').lower()
    today_schedule = TimetableEntry.objects.filter(day=day_name, is_break=False, teacher=profile)

    # Upcoming schedules
    upcoming_schedules = ClassSchedule.objects.filter(
        teacher=profile,
        scheduled_date__gte=today
    ).order_by('scheduled_date', 'timetable_entry__start_time')[:5]

    # Chat - get admin users
    admins = User.objects.filter(is_staff=True)
    recent_messages = ChatMessage.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).order_by('-timestamp')[:20]

    # Unread message count
    unread_count = ChatMessage.objects.filter(recipient=request.user, is_read=False).count()

    context = {
        'profile': profile,
        'today_attendance': today_attendance,
        'notifications': notifications,
        'all_notifications': all_notifications,
        'today_schedule': today_schedule,
        'upcoming_schedules': upcoming_schedules,
        'admins': admins,
        'recent_messages': recent_messages,
        'unread_count': unread_count,
        'today': today,
        'unread_notifications': notifications.count(),
    }
    return render(request, 'teacher/dashboard.html', context)


@login_required
def teacher_chat(request, admin_id):
    if request.user.is_staff:
        return redirect('admin_dashboard')
    admin_user = get_object_or_404(User, id=admin_id, is_staff=True)
    messages_qs = ChatMessage.objects.filter(
        Q(sender=request.user, recipient=admin_user) |
        Q(sender=admin_user, recipient=request.user)
    ).order_by('timestamp')
    # Mark as read
    messages_qs.filter(recipient=request.user, is_read=False).update(is_read=True)

    room_name = f"teacher_{min(request.user.id, admin_user.id)}_{max(request.user.id, admin_user.id)}"
    try:
        profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        profile = None
    admins = User.objects.filter(is_staff=True)
    all_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:20]
    unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return render(request, 'teacher/chat.html', {
        'admin_user': admin_user,
        'messages': messages_qs,
        'room_name': room_name,
        'profile': profile,
        'admins': admins,
        'all_notifications': all_notifications,
        'unread_notifications': unread_notifications,
    })


@login_required
def mark_notification_read(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notif.is_read = True
    notif.save()
    return JsonResponse({'status': 'ok'})


# ─── QR Code Scanning ─────────────────────────────────────────────────────────

def scan_qr(request, qr_uuid):
    """Public QR scan endpoint - teacher scans this URL"""
    qr_obj = get_object_or_404(QRCode, code=qr_uuid, is_active=True)
    today = timezone.localdate()
    now = timezone.localtime().time()

    if qr_obj.date != today:
        return render(request, 'qr/scan_result.html', {
            'success': False,
            'message': 'This QR code is not valid for today.',
        })

    if not request.user.is_authenticated:
        request.session['qr_uuid'] = str(qr_uuid)
        return redirect(f'/login/?next=/scan/{qr_uuid}/')

    if request.user.is_staff:
        return render(request, 'qr/scan_result.html', {
            'success': False,
            'message': 'Admins do not need to scan attendance.',
        })

    try:
        profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return render(request, 'qr/scan_result.html', {
            'success': False,
            'message': 'Teacher profile not found.',
        })

    attendance, created = Attendance.objects.get_or_create(
        teacher=profile,
        date=today,
        defaults={
            'qr_code': qr_obj,
            'check_in_time': now,
            'status': 'present',
            'scan_type': 'check_in',
        }
    )

    if not created:
        # Second scan = lesson done
        attendance.lesson_done_time = now
        attendance.scan_type = 'lesson_done'
        attendance.save()
        scan_type = 'lesson_done'
        msg = f'{profile.full_name} has completed their lesson at {now.strftime("%H:%M")}.'
    else:
        scan_type = 'check_in'
        msg = f'{profile.full_name} has checked in at {now.strftime("%H:%M")}.'

    # Notify admins
    for admin in User.objects.filter(is_staff=True):
        Notification.objects.create(
            recipient=admin,
            sender=request.user,
            title=f'Attendance: {profile.full_name}',
            message=msg,
            notification_type='attendance',
        )

    return render(request, 'qr/scan_result.html', {
        'success': True,
        'scan_type': scan_type,
        'message': msg,
        'teacher': profile,
        'time': now.strftime('%H:%M'),
    })


# ─── Admin Dashboard ──────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    today = timezone.localdate()
    teachers = TeacherProfile.objects.select_related('user').all()
    pending_teachers = teachers.filter(is_approved=False)
    approved_teachers = teachers.filter(is_approved=True)

    today_attendance = Attendance.objects.filter(date=today).select_related('teacher__user')
    present_count = today_attendance.filter(status='present').count()
    absent_count = approved_teachers.count() - present_count

    recent_notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:10]

    # Active QR code for today
    active_qr = QRCode.objects.filter(date=today, is_active=True).first()

    # Today's timetable
    day_name = today.strftime('%A').lower()
    today_timetable = TimetableEntry.objects.filter(day=day_name).order_by('start_time')

    context = {
        'teachers': approved_teachers,
        'pending_teachers': pending_teachers,
        'today_attendance': today_attendance,
        'present_count': present_count,
        'absent_count': absent_count,
        'total_teachers': approved_teachers.count(),
        'recent_notifications': recent_notifications,
        'active_qr': active_qr,
        'today_timetable': today_timetable,
        'today': today,
    }
    return render(request, 'admin/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def admin_teachers(request):
    teachers = TeacherProfile.objects.select_related('user').all().order_by('-date_joined')
    return render(request, 'admin/teachers.html', {'teachers': teachers})


@login_required
@user_passes_test(is_admin)
def teacher_detail(request, teacher_id):
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    attendances = Attendance.objects.filter(teacher=teacher).order_by('-date')[:30]
    schedules = ClassSchedule.objects.filter(teacher=teacher).order_by('-scheduled_date')[:10]
    return render(request, 'admin/teacher_detail.html', {
        'teacher': teacher,
        'attendances': attendances,
        'schedules': schedules,
    })


@login_required
@user_passes_test(is_admin)
def approve_teacher(request, teacher_id):
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    teacher.is_approved = True
    teacher.save()
    Notification.objects.create(
        recipient=teacher.user,
        sender=request.user,
        title='Account Approved',
        message='Your teacher account has been approved. You can now login to the system.',
        notification_type='admin',
    )
    messages.success(request, f'{teacher.full_name} has been approved.')
    return redirect('admin_teachers')


@login_required
@user_passes_test(is_admin)
def reject_teacher(request, teacher_id):
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    name = teacher.full_name
    teacher.user.delete()
    messages.warning(request, f'{name} has been rejected and removed.')
    return redirect('admin_teachers')


@login_required
@user_passes_test(is_admin)
def delete_teacher(request, teacher_id):
    """Fully delete an approved or pending teacher with confirmation."""
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    if request.method == 'POST':
        name = teacher.full_name
        teacher.user.delete()  # cascades to profile, attendance, etc.
        messages.success(request, f'{name} has been permanently deleted.')
        return redirect('admin_teachers')
    # GET — show confirmation page
    return render(request, 'admin/confirm_delete.html', {'teacher': teacher})


# ─── QR Code Management ───────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def generate_qr(request):
    if request.method == 'POST':
        form = QRCodeForm(request.POST)
        if form.is_valid():
            qr_obj = form.save(commit=False)
            qr_obj.created_by = request.user
            qr_obj.save()

            # Generate QR image
            scan_url = request.build_absolute_uri(f'/scan/{qr_obj.code}/')
            qr_img = qrcode.make(scan_url)
            buffer = io.BytesIO()
            qr_img.save(buffer, format='PNG')
            buffer.seek(0)
            qr_obj.qr_image.save(f'qr_{qr_obj.code}.png', ContentFile(buffer.read()), save=True)

            messages.success(request, 'QR Code generated successfully!')
            return redirect('qr_detail', qr_id=qr_obj.id)
    else:
        form = QRCodeForm(initial={'date': timezone.localdate()})

    qr_codes = QRCode.objects.all().order_by('-created_at')
    return render(request, 'admin/qr_generate.html', {'form': form, 'qr_codes': qr_codes})


@login_required
@user_passes_test(is_admin)
def qr_detail(request, qr_id):
    qr_obj = get_object_or_404(QRCode, id=qr_id)
    scan_url = request.build_absolute_uri(f'/scan/{qr_obj.code}/')

    # Generate QR as base64 for display
    qr_img = qrcode.make(scan_url)
    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG')
    qr_b64 = base64.b64encode(buffer.getvalue()).decode()

    return render(request, 'admin/qr_detail.html', {
        'qr_obj': qr_obj,
        'scan_url': scan_url,
        'qr_b64': qr_b64,
    })


# ─── Attendance Management ────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def admin_attendance(request):
    today = timezone.localdate()
    selected_date = request.GET.get('date', str(today))
    try:
        selected_date = date.fromisoformat(selected_date)
    except ValueError:
        selected_date = today

    attendances = Attendance.objects.filter(date=selected_date).select_related('teacher__user')
    approved_teachers = TeacherProfile.objects.filter(is_approved=True)

    # Mark absent for teachers who haven't scanned
    present_ids = attendances.values_list('teacher_id', flat=True)
    absent_teachers = approved_teachers.exclude(id__in=present_ids)

    return render(request, 'admin/attendance.html', {
        'attendances': attendances,
        'absent_teachers': absent_teachers,
        'selected_date': selected_date,
        'today': today,
    })


# ─── Timetable Management ─────────────────────────────────────────────────────

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
    # Build list of (day_name, queryset) tuples for easy template iteration
    timetable_by_day = [
        (day, list(TimetableEntry.objects.filter(day=day).order_by('start_time')))
        for day in days
    ]

    return render(request, 'admin/timetable.html', {
        'form': form,
        'timetable_by_day': timetable_by_day,
        'days': days,
    })


@login_required
@user_passes_test(is_admin)
def delete_timetable_entry(request, entry_id):
    entry = get_object_or_404(TimetableEntry, id=entry_id)
    entry.delete()
    messages.success(request, 'Timetable entry deleted.')
    return redirect('admin_timetable')


# ─── Class Scheduling ─────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def admin_schedule(request):
    if request.method == 'POST':
        form = ClassScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            schedule.save()

            # Notify teacher
            Notification.objects.create(
                recipient=schedule.teacher.user,
                sender=request.user,
                title=f'Class Scheduled: {schedule.timetable_entry.subject}',
                message=(
                    f'You have been scheduled to teach {schedule.timetable_entry.subject} '
                    f'on {schedule.scheduled_date} from '
                    f'{schedule.timetable_entry.start_time.strftime("%H:%M")} to '
                    f'{schedule.timetable_entry.end_time.strftime("%H:%M")}.'
                ),
                notification_type='schedule',
                related_timetable=schedule.timetable_entry,
            )
            messages.success(request, f'Class scheduled and {schedule.teacher.full_name} notified.')
            return redirect('admin_schedule')
    else:
        form = ClassScheduleForm()

    schedules = ClassSchedule.objects.select_related(
        'teacher__user', 'timetable_entry'
    ).order_by('-scheduled_date')[:50]

    return render(request, 'admin/schedule.html', {'form': form, 'schedules': schedules})


# ─── Notifications ────────────────────────────────────────────────────────────

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

    sent_notifications = Notification.objects.filter(sender=request.user).order_by('-created_at')[:30]
    return render(request, 'admin/notifications.html', {
        'form': form,
        'sent_notifications': sent_notifications,
    })


# ─── Admin Chat ───────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def admin_chat(request, teacher_id=None):
    teachers = TeacherProfile.objects.filter(is_approved=True).select_related('user')
    selected_teacher = None
    messages_qs = []
    room_name = ''

    if teacher_id:
        selected_teacher = get_object_or_404(TeacherProfile, id=teacher_id)
        messages_qs = ChatMessage.objects.filter(
            Q(sender=request.user, recipient=selected_teacher.user) |
            Q(sender=selected_teacher.user, recipient=request.user)
        ).order_by('timestamp')
        messages_qs.filter(recipient=request.user, is_read=False).update(is_read=True)
        room_name = f"teacher_{min(request.user.id, selected_teacher.user.id)}_{max(request.user.id, selected_teacher.user.id)}"

    return render(request, 'admin/chat.html', {
        'teachers': teachers,
        'selected_teacher': selected_teacher,
        'messages': messages_qs,
        'room_name': room_name,
    })


# ─── API Endpoints ────────────────────────────────────────────────────────────

@login_required
def get_notifications_api(request):
    notifs = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).order_by('-created_at')[:10]
    data = [{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'type': n.notification_type,
        'time': n.created_at.strftime('%H:%M'),
    } for n in notifs]
    return JsonResponse({'notifications': data, 'count': len(data)})


@login_required
def get_schedule_reminders_api(request):
    """Returns upcoming class schedules for reminder system"""
    if request.user.is_staff:
        return JsonResponse({'schedules': []})
    try:
        profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return JsonResponse({'schedules': []})

    today = timezone.localdate()
    now = timezone.localtime().time()
    schedules = ClassSchedule.objects.filter(
        teacher=profile,
        scheduled_date=today,
        is_completed=False,
    ).select_related('timetable_entry')

    data = []
    for s in schedules:
        start = s.timetable_entry.start_time
        # Calculate minutes until class
        start_dt = datetime.combine(today, start)
        now_dt = datetime.combine(today, now)
        diff_minutes = (start_dt - now_dt).total_seconds() / 60
        data.append({
            'id': s.id,
            'subject': s.timetable_entry.subject,
            'start_time': start.strftime('%H:%M'),
            'end_time': s.timetable_entry.end_time.strftime('%H:%M'),
            'minutes_until': round(diff_minutes),
        })
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


# ─── QR Scanner Page ──────────────────────────────────────────────────────────

@login_required
def qr_scanner(request):
    return render(request, 'qr/scanner.html')


# ─── Timetable View (public for teachers) ─────────────────────────────────────

@login_required
def view_timetable(request):
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    timetable_by_day = [
        (day, list(TimetableEntry.objects.filter(day=day).order_by('start_time')))
        for day in days
    ]
    try:
        profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        profile = None
    admins = User.objects.filter(is_staff=True)
    all_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:20]
    unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return render(request, 'timetable.html', {
        'timetable_by_day': timetable_by_day,
        'days': days,
        'profile': profile,
        'admins': admins,
        'all_notifications': all_notifications,
        'unread_notifications': unread_notifications,
    })
