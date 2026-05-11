import qrcode
import io
import base64
from datetime import datetime, date, timedelta
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login, logout, authenticate
from django.db import transaction
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, ProtectedError
from django.core.files.base import ContentFile

from .models import (
    TeacherProfile, Attendance, QRCode, Notification,
    TimetableEntry, ClassSchedule, AdminProfile
)
from .forms import (
    TeacherRegistrationForm,
    NotificationForm, TimetableEntryForm, ClassScheduleForm, QRCodeForm
)

logger = logging.getLogger(__name__)

# Teacher profile forms — keep under DB limits (PostgreSQL errors otherwise).
_TEACHER_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


def _dob_input_value(post_data, profile):
    raw = post_data.get('date_of_birth', '').strip()
    if raw:
        return raw
    if getattr(profile, 'date_of_birth', None):
        return profile.date_of_birth.isoformat()
    return ''


def _parse_dob_or_error(raw, errors, field='date_of_birth'):
    raw = (raw or '').strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        errors[field] = 'Please enter a valid date of birth.'
        return None


def _safe_years_experience(raw):
    s = (raw or '').strip()
    if not s.isdigit():
        return 0
    return min(int(s), 2147483647)


def _validate_teacher_profile_lengths(data, errors):
    """Clip or reject fields that exceed model max_length (avoids DB DataError → 500)."""
    limits = [
        ('first_name', 150),
        ('last_name', 150),
        ('phone', 20),
        ('emergency_phone', 20),
        ('emergency_contact', 100),
        ('specialization', 200),
        ('previous_school', 200),
    ]
    for key, max_len in limits:
        val = data.get(key, '') or ''
        if len(val) > max_len:
            errors[key] = f'This field must be at most {max_len} characters.'


def _validate_teacher_uploads(request_files, errors):
    for name in ('profile_photo', 'cv_document', 'certificate_document', 'id_document'):
        f = request_files.get(name)
        if f and getattr(f, 'size', 0) > _TEACHER_MAX_UPLOAD_BYTES:
            errors[name] = 'File is too large (maximum 10 MB per file).'


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
    """Kept for backward compatibility — redirects to login."""
    return redirect('login')


def unified_login(request):
    """Single login for both teachers and admins using Staff ID + password."""
    if request.user.is_authenticated:
        if request.user.is_staff:
            try:
                if request.user.admin_profile.role == 'superadmin':
                    return redirect('superadmin_dashboard')
            except Exception:
                pass
            return redirect('admin_dashboard')
        return redirect('teacher_dashboard')

    error = None
    if request.method == 'POST':
        staff_id = request.POST.get('staff_id', '').strip().upper()
        password = request.POST.get('password', '').strip()
        if not staff_id or not password:
            error = 'Please enter your Staff ID and password.'
        else:
            # Try teacher first
            try:
                profile = TeacherProfile.objects.select_related('user').get(staff_id=staff_id)
                user = authenticate(request, username=profile.user.username, password=password)
                if user is None:
                    error = 'Invalid Staff ID or password.'
                elif not profile.is_approved:
                    error = 'Your account is not yet activated. Contact your admin.'
                else:
                    login(request, user)
                    return redirect('teacher_dashboard')
            except TeacherProfile.DoesNotExist:
                # Try admin (staff_id = username for admins)
                user = authenticate(request, username=staff_id, password=password)
                if user is None:
                    error = 'Invalid Staff ID or password.'
                elif not user.is_staff:
                    error = 'Invalid Staff ID or password.'
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
    return render(request, 'auth/login.html', {'error': error})


def teacher_login(request):
    """Alias — redirects to unified login."""
    return unified_login(request)


def admin_login(request):
    """Alias — redirects to unified login."""
    return unified_login(request)


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

    # Redirect to complete profile if not done yet
    if not profile.profile_complete:
        return redirect('teacher_complete_profile')

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


# ── Teacher Profile Complete / Update / Change Password ───────────────────────

@login_required
def teacher_complete_profile(request):
    """First-login profile completion for teachers."""
    if request.user.is_staff:
        return redirect('admin_dashboard')
    try:
        profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return redirect('welcome')

    if profile.profile_complete:
        return redirect('teacher_dashboard')

    from .models import DEPARTMENT_CHOICES, COURSE_TYPE_CHOICES, GENDER_CHOICES, QUALIFICATION_CHOICES, ELECTIVE_SUBJECTS, DEPARTMENT_SUBJECTS
    errors = {}
    if request.method == 'POST':
        # Collect all fields
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        gender = request.POST.get('gender', '').strip()
        dob_raw = request.POST.get('date_of_birth', '').strip()
        address = request.POST.get('address', '').strip()
        qualification = request.POST.get('qualification', '').strip()
        specialization = request.POST.get('specialization', '').strip()
        years_exp = request.POST.get('years_of_experience', '0').strip()
        course_type = request.POST.get('course_type', '').strip()
        preferred_subject = request.POST.get('preferred_subject', '').strip()[:100]
        department = request.POST.get('department', '').strip()[:100]
        previous_school = request.POST.get('previous_school', '').strip()
        bio = request.POST.get('bio', '').strip()
        emergency_contact = request.POST.get('emergency_contact', '').strip()
        emergency_phone = request.POST.get('emergency_phone', '').strip()
        email = request.POST.get('email', '').strip()

        # Validate required
        if not first_name: errors['first_name'] = 'First name is required.'
        if not last_name: errors['last_name'] = 'Last name is required.'
        if not phone: errors['phone'] = 'Phone number is required.'
        if not gender: errors['gender'] = 'Please select your gender.'
        if not address: errors['address'] = 'Address is required.'
        if not qualification: errors['qualification'] = 'Please select your qualification.'
        if not specialization: errors['specialization'] = 'Specialization is required.'
        if not course_type: errors['course_type'] = 'Please select a course type.'
        if not preferred_subject: errors['preferred_subject'] = 'Please select your subject.'
        if course_type == 'departmental' and not department:
            errors['department'] = 'Please select your department.'

        _validate_teacher_profile_lengths({
            'first_name': first_name, 'last_name': last_name, 'phone': phone,
            'emergency_phone': emergency_phone, 'emergency_contact': emergency_contact,
            'specialization': specialization, 'previous_school': previous_school,
        }, errors)
        _validate_teacher_uploads(request.FILES, errors)
        date_of_birth = _parse_dob_or_error(dob_raw, errors)

        if not errors:
            user = request.user
            user.first_name = first_name[:150]
            user.last_name = last_name[:150]
            if email:
                user.email = email[:254]
            profile.phone = phone[:20]
            profile.gender = gender
            profile.date_of_birth = date_of_birth
            profile.address = address
            profile.qualification = qualification
            profile.specialization = specialization[:200]
            profile.years_of_experience = _safe_years_experience(years_exp)
            profile.course_type = course_type
            profile.preferred_subject = preferred_subject
            profile.department = department if course_type == 'departmental' else ''
            profile.previous_school = previous_school[:200]
            profile.bio = bio
            profile.emergency_contact = emergency_contact[:100]
            profile.emergency_phone = emergency_phone[:20]
            profile.profile_complete = True
            if request.FILES.get('profile_photo'):
                profile.profile_photo = request.FILES['profile_photo']
            if request.FILES.get('cv_document'):
                profile.cv_document = request.FILES['cv_document']
            if request.FILES.get('certificate_document'):
                profile.certificate_document = request.FILES['certificate_document']
            if request.FILES.get('id_document'):
                profile.id_document = request.FILES['id_document']
            try:
                with transaction.atomic():
                    user.save()
                    profile.save()
            except Exception:
                logger.exception('teacher_complete_profile save failed')
                errors['save'] = (
                    'We could not save your profile. If you uploaded files, try smaller images '
                    '(under 10 MB each) or skip documents for now.'
                )
                profile.refresh_from_db()
                user.refresh_from_db()

        if not errors:
            messages.success(request, f'Welcome {first_name}! Your profile is complete.')
            return redirect('teacher_dashboard')

    dob_input_value = _dob_input_value(request.POST, profile)
    return render(request, 'teacher/complete_profile.html', {
        'profile': profile,
        'errors': errors,
        'post': request.POST,
        'dob_input_value': dob_input_value,
        'dept_choices': DEPARTMENT_CHOICES,
        'course_types': COURSE_TYPE_CHOICES,
        'genders': GENDER_CHOICES,
        'qualifications': QUALIFICATION_CHOICES,
        'elective_subjects': ELECTIVE_SUBJECTS,
        'dept_subjects': DEPARTMENT_SUBJECTS,
    })


@login_required
def teacher_update_profile(request):
    """Teacher updates their profile details."""
    if request.user.is_staff:
        return redirect('admin_dashboard')
    try:
        profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return redirect('welcome')

    from .models import DEPARTMENT_CHOICES, COURSE_TYPE_CHOICES, GENDER_CHOICES, QUALIFICATION_CHOICES, ELECTIVE_SUBJECTS, DEPARTMENT_SUBJECTS
    errors = {}
    success = None
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        gender = request.POST.get('gender', '').strip()
        address = request.POST.get('address', '').strip()
        qualification = request.POST.get('qualification', '').strip()
        specialization = request.POST.get('specialization', '').strip()
        years_exp = request.POST.get('years_of_experience', '0').strip()
        course_type = request.POST.get('course_type', '').strip()
        preferred_subject = request.POST.get('preferred_subject', '').strip()[:100]
        department = request.POST.get('department', '').strip()[:100]
        previous_school = request.POST.get('previous_school', '').strip()
        bio = request.POST.get('bio', '').strip()
        emergency_contact = request.POST.get('emergency_contact', '').strip()
        emergency_phone = request.POST.get('emergency_phone', '').strip()
        email = request.POST.get('email', '').strip()
        dob_raw = request.POST.get('date_of_birth', '').strip()

        if not first_name: errors['first_name'] = 'First name is required.'
        if not last_name: errors['last_name'] = 'Last name is required.'
        if not phone: errors['phone'] = 'Phone is required.'
        if not gender: errors['gender'] = 'Gender is required.'
        if not address: errors['address'] = 'Address is required.'
        if not qualification: errors['qualification'] = 'Qualification is required.'
        if not specialization: errors['specialization'] = 'Specialization is required.'
        if not course_type: errors['course_type'] = 'Course type is required.'
        if not preferred_subject: errors['preferred_subject'] = 'Subject is required.'
        if course_type == 'departmental' and not department:
            errors['department'] = 'Please select your department.'

        _validate_teacher_profile_lengths({
            'first_name': first_name, 'last_name': last_name, 'phone': phone,
            'emergency_phone': emergency_phone, 'emergency_contact': emergency_contact,
            'specialization': specialization, 'previous_school': previous_school,
        }, errors)
        _validate_teacher_uploads(request.FILES, errors)
        date_of_birth = _parse_dob_or_error(dob_raw, errors)

        if not errors:
            user = request.user
            user.first_name = first_name[:150]
            user.last_name = last_name[:150]
            if email:
                user.email = email[:254]
            profile.phone = phone[:20]
            profile.gender = gender
            profile.date_of_birth = date_of_birth
            profile.address = address
            profile.qualification = qualification
            profile.specialization = specialization[:200]
            profile.years_of_experience = _safe_years_experience(years_exp)
            profile.course_type = course_type
            profile.preferred_subject = preferred_subject
            profile.department = department if course_type == 'departmental' else ''
            profile.previous_school = previous_school[:200]
            profile.bio = bio
            profile.emergency_contact = emergency_contact[:100]
            profile.emergency_phone = emergency_phone[:20]
            if request.FILES.get('profile_photo'):
                profile.profile_photo = request.FILES['profile_photo']
            if request.FILES.get('cv_document'):
                profile.cv_document = request.FILES['cv_document']
            if request.FILES.get('certificate_document'):
                profile.certificate_document = request.FILES['certificate_document']
            if request.FILES.get('id_document'):
                profile.id_document = request.FILES['id_document']
            try:
                with transaction.atomic():
                    user.save()
                    profile.save()
                success = 'Profile updated successfully!'
            except Exception:
                logger.exception('teacher_update_profile save failed')
                errors['save'] = (
                    'Could not save changes. Try smaller files (under 10 MB each) or remove optional uploads.'
                )
                profile.refresh_from_db()
                user.refresh_from_db()

    dob_input_value = _dob_input_value(request.POST, profile)
    return render(request, 'teacher/update_profile.html', {
        'profile': profile,
        'errors': errors,
        'success': success,
        'post': request.POST,
        'dob_input_value': dob_input_value,
        'dept_choices': DEPARTMENT_CHOICES,
        'course_types': COURSE_TYPE_CHOICES,
        'genders': GENDER_CHOICES,
        'qualifications': QUALIFICATION_CHOICES,
        'elective_subjects': ELECTIVE_SUBJECTS,
        'dept_subjects': DEPARTMENT_SUBJECTS,
    })


@login_required
def teacher_change_password(request):
    """Teacher changes their own password."""
    if request.user.is_staff:
        return redirect('admin_dashboard')
    error = None
    success = None
    if request.method == 'POST':
        current = request.POST.get('current_password', '').strip()
        new_pw = request.POST.get('new_password', '').strip()
        confirm = request.POST.get('confirm_password', '').strip()
        if not current:
            error = 'Please enter your current password.'
        elif not authenticate(request, username=request.user.username, password=current):
            error = 'Current password is incorrect.'
        elif not new_pw:
            error = 'New password is required.'
        elif len(new_pw) < 4:
            error = 'New password must be at least 4 characters.'
        elif new_pw != confirm:
            error = 'New passwords do not match.'
        else:
            request.user.set_password(new_pw)
            request.user.save()
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            success = 'Password changed successfully!'
    return render(request, 'teacher/change_password.html', {'error': error, 'success': success})


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
def admin_qr_view(request):
    school_qrs = QRCode.objects.filter(qr_type='school_attendance').order_by('-created_at')
    lesson_qrs = QRCode.objects.filter(qr_type='lesson').order_by('-created_at')
    return render(request, 'admin/qr_view.html', {'school_qrs': school_qrs, 'lesson_qrs': lesson_qrs})


@login_required
@user_passes_test(is_admin)
def teacher_detail(request, teacher_id):
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    attendances = Attendance.objects.filter(teacher=teacher).order_by('-date')[:30]
    return render(request, 'admin/teacher_detail.html', {'teacher': teacher, 'attendances': attendances})


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
        ).select_related('user').order_by('preferred_subject')
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
        'is_core': dept_slug == 'core',
    })


@login_required
@user_passes_test(is_superadmin)
def qr_detail_sa(request, qr_id):
    """Super admin QR detail view."""
    return qr_detail(request, qr_id)


@login_required
@user_passes_test(is_superadmin)
def delete_qr(request, qr_id):
    """Permanently remove a generated QR code (superadmin only)."""
    qr_obj = get_object_or_404(QRCode, id=qr_id)
    if request.method != 'POST':
        messages.error(request, 'To delete a QR code, use the delete action from the QR management page.')
        return redirect('qr_detail_sa', qr_id=qr_id)
    label = qr_obj.label
    pk = qr_obj.pk
    try:
        with transaction.atomic():
            # Clear FK refs first (handles any DB quirks; Attendance uses SET_NULL).
            Attendance.objects.filter(school_qr_id=pk).update(school_qr=None)
            Attendance.objects.filter(lesson_qr_id=pk).update(lesson_qr=None)

            img = qr_obj.qr_image
            if getattr(img, 'name', None):
                try:
                    img.delete(save=False)
                except Exception as exc:
                    logger.warning('QR image delete skipped (id=%s): %s', pk, exc)

            qr_obj.delete()
    except ProtectedError:
        messages.error(request, 'This QR code cannot be deleted because other records depend on it.')
        return redirect('qr_detail_sa', qr_id=qr_id)
    except Exception:
        logger.exception('delete_qr failed for id=%s', qr_id)
        messages.error(request, 'Deleting this QR code failed. Try again later.')
        return redirect('qr_detail_sa', qr_id=qr_id)

    messages.success(request, f'QR code "{label}" was permanently deleted.')
    return redirect('generate_qr')


@login_required
@user_passes_test(is_admin)
def admin_teachers(request):
    teachers = TeacherProfile.objects.select_related('user').all().order_by('-date_joined')
    return render(request, 'admin/teachers.html', {'teachers': teachers})


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
def admin_create_teacher(request):
    """Admin creates teacher with ONLY Staff ID + Password. Teacher fills rest on first login."""
    error = None
    success = None
    if request.method == 'POST':
        staff_id = request.POST.get('staff_id', '').strip().upper()
        password = request.POST.get('password', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        if not staff_id:
            error = 'Staff ID is required.'
        elif not password:
            error = 'Password is required.'
        elif len(staff_id) < 3:
            error = 'Staff ID must be at least 3 characters.'
        elif len(password) < 4:
            error = 'Password must be at least 4 characters.'
        elif User.objects.filter(username=staff_id).exists():
            error = f'Staff ID "{staff_id}" already exists.'
        elif TeacherProfile.objects.filter(staff_id=staff_id).exists():
            error = f'Staff ID "{staff_id}" already taken.'
        else:
            try:
                new_user = User.objects.create_user(
                    username=staff_id, password=password,
                    first_name=first_name, last_name=last_name,
                    is_active=True
                )
                TeacherProfile.objects.create(
                    user=new_user, staff_id=staff_id,
                    phone='', gender='male', address='',
                    qualification='other', specialization='',
                    course_type='core', preferred_subject='',
                    is_approved=True, profile_complete=False,
                )
                success = f'✅ Account created! Staff ID: {staff_id} | Password: {password} — Teacher must complete profile on first login.'
            except Exception as e:
                error = f'Error: {str(e)}'
    return render(request, 'admin/create_teacher.html', {'error': error, 'success': success})


@login_required
@user_passes_test(is_admin)
def admin_qr_view(request):
    school_qrs = QRCode.objects.filter(qr_type='school_attendance').order_by('-created_at')
    lesson_qrs = QRCode.objects.filter(qr_type='lesson').order_by('-created_at')
    return render(request, 'admin/qr_view.html', {'school_qrs': school_qrs, 'lesson_qrs': lesson_qrs})


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
            return redirect('qr_detail_sa', qr_id=qr_obj.id)
    else:
        form = QRCodeForm()
    school_qrs = QRCode.objects.filter(qr_type='school_attendance').order_by('-created_at')
    lesson_qrs = QRCode.objects.filter(qr_type='lesson').order_by('-created_at')
    return render(request, 'superadmin/qr_generate.html', {'form': form, 'school_qrs': school_qrs, 'lesson_qrs': lesson_qrs})


@login_required
def qr_detail(request, qr_id):
    if not (request.user.is_staff):
        return redirect('welcome')
    qr_obj = get_object_or_404(QRCode, id=qr_id)
    scan_path = f'/scan/school/{qr_obj.code}/' if qr_obj.qr_type == 'school_attendance' else f'/scan/lesson/{qr_obj.code}/'
    scan_url = request.build_absolute_uri(scan_path)
    img = qrcode.make(scan_url)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode()
    qr_list_url = reverse('generate_qr') if is_superadmin(request.user) else reverse('admin_qr_view')
    return render(request, 'admin/qr_detail.html', {
        'qr_obj': qr_obj,
        'scan_url': scan_url,
        'qr_b64': qr_b64,
        'show_qr_delete': is_superadmin(request.user),
        'qr_list_url': qr_list_url,
    })


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
        staff_id = request.POST.get('staff_id', '').strip().upper()
        password = request.POST.get('password', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        if not staff_id or not password:
            error = 'Staff ID and password are required.'
        elif len(staff_id) < 3:
            error = 'Staff ID must be at least 3 characters.'
        elif User.objects.filter(username=staff_id).exists():
            error = f'Staff ID "{staff_id}" is already taken.'
        else:
            new_user = User.objects.create_user(
                username=staff_id, password=password,
                first_name=first_name, last_name=last_name,
                email=email, is_staff=True, is_active=True
            )
            AdminProfile.objects.create(user=new_user, role='admin', created_by=request.user)
            messages.success(request, f'Admin created — Staff ID: {staff_id} / Password: {password}')
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
        messages.success(request, f'{name} permanently deleted.')
        return redirect('superadmin_teachers')
    return render(request, 'superadmin/confirm_delete_teacher.html', {'teacher': teacher})


@login_required
@user_passes_test(is_superadmin)
def superadmin_change_credentials(request):
    """Super admin can change their own username and password."""
    error = None
    success = None
    if request.method == 'POST':
        new_username = request.POST.get('new_username', '').strip()
        current_password = request.POST.get('current_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not current_password:
            error = 'Please enter your current password to confirm changes.'
        elif not authenticate(request, username=request.user.username, password=current_password):
            error = 'Current password is incorrect.'
        elif new_username and User.objects.filter(username=new_username).exclude(pk=request.user.pk).exists():
            error = f'Username "{new_username}" is already taken.'
        elif new_password and new_password != confirm_password:
            error = 'New passwords do not match.'
        elif new_password and len(new_password) < 6:
            error = 'New password must be at least 6 characters.'
        else:
            user = request.user
            changed = []
            if new_username and new_username != user.username:
                user.username = new_username
                changed.append('username')
            if new_password:
                user.set_password(new_password)
                changed.append('password')
            if changed:
                user.save()
                # Re-login to keep session valid after password change
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)
                success = f'Successfully updated: {", ".join(changed)}.'
            else:
                success = 'No changes made.'

    return render(request, 'superadmin/change_credentials.html', {
        'error': error,
        'success': success,
        'current_username': request.user.username,
    })


@login_required
@user_passes_test(is_superadmin)
def superadmin_staff_ids(request):
    """Registry of all teacher Staff IDs."""
    teachers = TeacherProfile.objects.select_related('user').all().order_by('staff_id')
    return render(request, 'superadmin/staff_ids.html', {'teachers': teachers})
