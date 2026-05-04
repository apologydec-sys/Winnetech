content = '''
# ── Admin Dashboard ───────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    today = timezone.localdate()
    approved_teachers = TeacherProfile.objects.filter(is_approved=True).select_related(\'user\')
    pending_teachers = TeacherProfile.objects.filter(is_approved=False)
    today_att = Attendance.objects.filter(date=today).select_related(\'teacher__user\')
    present_count = today_att.filter(school_status=\'present\').count()
    absent_count = approved_teachers.count() - present_count
    recent_notifs = Notification.objects.filter(recipient=request.user).order_by(\'-created_at\')[:10]
    school_qr = QRCode.objects.filter(qr_type=\'school_attendance\', is_active=True).first()
    lesson_qr = QRCode.objects.filter(qr_type=\'lesson\', is_active=True).first()
    day_name = today.strftime(\'%A\').lower()
    today_timetable = TimetableEntry.objects.filter(day=day_name).order_by(\'start_time\')
    return render(request, \'admin/dashboard.html\', {
        \'approved_teachers\': approved_teachers,
        \'pending_teachers\': pending_teachers,
        \'today_att\': today_att,
        \'present_count\': present_count,
        \'absent_count\': absent_count,
        \'total_teachers\': approved_teachers.count(),
        \'recent_notifs\': recent_notifs,
        \'school_qr\': school_qr,
        \'lesson_qr\': lesson_qr,
        \'today_timetable\': today_timetable,
        \'today\': today,
    })


@login_required
@user_passes_test(is_admin)
def admin_teachers(request):
    teachers = TeacherProfile.objects.select_related(\'user\').all().order_by(\'-date_joined\')
    return render(request, \'admin/teachers.html\', {\'teachers\': teachers})


@login_required
@user_passes_test(is_admin)
def teacher_detail(request, teacher_id):
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    attendances = Attendance.objects.filter(teacher=teacher).order_by(\'-date\')[:30]
    return render(request, \'admin/teacher_detail.html\', {\'teacher\': teacher, \'attendances\': attendances})


@login_required
@user_passes_test(is_admin)
def approve_teacher(request, teacher_id):
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    teacher.is_approved = True
    teacher.save()
    Notification.objects.create(
        recipient=teacher.user, sender=request.user,
        title=\'Account Approved\',
        message=\'Your teacher account has been approved. You can now login.\',
        notification_type=\'admin\'
    )
    messages.success(request, f\'{teacher.full_name} approved.\')
    return redirect(\'admin_teachers\')


@login_required
@user_passes_test(is_admin)
def reject_teacher(request, teacher_id):
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    name = teacher.full_name
    teacher.user.delete()
    messages.warning(request, f\'{name} rejected and removed.\')
    return redirect(\'admin_teachers\')


@login_required
@user_passes_test(is_admin)
def delete_teacher(request, teacher_id):
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    if request.method == \'POST\':
        name = teacher.full_name
        teacher.user.delete()
        messages.success(request, f\'{name} permanently deleted.\')
        return redirect(\'admin_teachers\')
    return render(request, \'admin/confirm_delete.html\', {\'teacher\': teacher})


@login_required
@user_passes_test(is_admin)
def admin_attendance(request):
    today = timezone.localdate()
    selected_date = request.GET.get(\'date\', str(today))
    try:
        from datetime import date as dt
        selected_date = dt.fromisoformat(selected_date)
    except ValueError:
        selected_date = today
    attendances = Attendance.objects.filter(date=selected_date).select_related(\'teacher__user\')
    approved_teachers = TeacherProfile.objects.filter(is_approved=True)
    present_ids = attendances.filter(school_status=\'present\').values_list(\'teacher_id\', flat=True)
    absent_teachers = approved_teachers.exclude(id__in=present_ids)
    lesson_done_ids = attendances.filter(lesson_status=\'done\').values_list(\'teacher_id\', flat=True)
    lesson_not_done = approved_teachers.exclude(id__in=lesson_done_ids)
    return render(request, \'admin/attendance.html\', {
        \'attendances\': attendances,
        \'absent_teachers\': absent_teachers,
        \'lesson_not_done\': lesson_not_done,
        \'selected_date\': selected_date,
        \'today\': today,
    })


@login_required
@user_passes_test(is_admin)
def admin_timetable(request):
    if request.method == \'POST\':
        form = TimetableEntryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, \'Timetable entry added.\')
            return redirect(\'admin_timetable\')
    else:
        form = TimetableEntryForm()
    days = [\'monday\', \'tuesday\', \'wednesday\', \'thursday\', \'friday\']
    timetable_by_day = [(d, list(TimetableEntry.objects.filter(day=d).order_by(\'start_time\'))) for d in days]
    return render(request, \'admin/timetable.html\', {\'form\': form, \'timetable_by_day\': timetable_by_day, \'days\': days})


@login_required
@user_passes_test(is_admin)
def delete_timetable_entry(request, entry_id):
    get_object_or_404(TimetableEntry, id=entry_id).delete()
    messages.success(request, \'Entry deleted.\')
    return redirect(\'admin_timetable\')


@login_required
@user_passes_test(is_admin)
def admin_schedule(request):
    if request.method == \'POST\':
        form = ClassScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            schedule.save()
            Notification.objects.create(
                recipient=schedule.teacher.user, sender=request.user,
                title=f\'Class Scheduled: {schedule.timetable_entry.subject}\',
                message=f\'You teach {schedule.timetable_entry.subject} on {schedule.scheduled_date} from {schedule.timetable_entry.start_time.strftime("%H:%M")} to {schedule.timetable_entry.end_time.strftime("%H:%M")}.\',
                notification_type=\'schedule\', related_timetable=schedule.timetable_entry
            )
            messages.success(request, f\'Scheduled and {schedule.teacher.full_name} notified.\')
            return redirect(\'admin_schedule\')
    else:
        form = ClassScheduleForm()
    schedules = ClassSchedule.objects.select_related(\'teacher__user\', \'timetable_entry\').order_by(\'-scheduled_date\')[:50]
    return render(request, \'admin/schedule.html\', {\'form\': form, \'schedules\': schedules})


@login_required
@user_passes_test(is_admin)
def admin_notifications(request):
    if request.method == \'POST\':
        form = NotificationForm(request.POST)
        if form.is_valid():
            notif = form.save(commit=False)
            notif.sender = request.user
            notif.save()
            messages.success(request, \'Notification sent.\')
            return redirect(\'admin_notifications\')
    else:
        form = NotificationForm()
    sent = Notification.objects.filter(sender=request.user).order_by(\'-created_at\')[:30]
    return render(request, \'admin/notifications.html\', {\'form\': form, \'sent_notifications\': sent})


@login_required
@user_passes_test(is_admin)
def generate_qr(request):
    if request.method == \'POST\':
        form = QRCodeForm(request.POST)
        if form.is_valid():
            qr_obj = form.save(commit=False)
            qr_obj.created_by = request.user
            qr_obj.save()
            scan_path = f\'/scan/school/{qr_obj.code}/\' if qr_obj.qr_type == \'school_attendance\' else f\'/scan/lesson/{qr_obj.code}/\'
            scan_url = request.build_absolute_uri(scan_path)
            img = qrcode.make(scan_url)
            buf = __import__(\'io\').BytesIO()
            img.save(buf, format=\'PNG\')
            buf.seek(0)
            qr_obj.qr_image.save(f\'qr_{qr_obj.code}.png\', ContentFile(buf.read()), save=True)
            messages.success(request, f\'{qr_obj.get_qr_type_display()} QR Code generated! Valid for 5 years.\')
            return redirect(\'qr_detail\', qr_id=qr_obj.id)
    else:
        form = QRCodeForm()
    school_qrs = QRCode.objects.filter(qr_type=\'school_attendance\').order_by(\'-created_at\')
    lesson_qrs = QRCode.objects.filter(qr_type=\'lesson\').order_by(\'-created_at\')
    return render(request, \'admin/qr_generate.html\', {\'form\': form, \'school_qrs\': school_qrs, \'lesson_qrs\': lesson_qrs})


@login_required
@user_passes_test(is_admin)
def qr_detail(request, qr_id):
    qr_obj = get_object_or_404(QRCode, id=qr_id)
    scan_path = f\'/scan/school/{qr_obj.code}/\' if qr_obj.qr_type == \'school_attendance\' else f\'/scan/lesson/{qr_obj.code}/\'
    scan_url = request.build_absolute_uri(scan_path)
    img = qrcode.make(scan_url)
    buf = __import__(\'io\').BytesIO()
    img.save(buf, format=\'PNG\')
    qr_b64 = __import__(\'base64\').b64encode(buf.getvalue()).decode()
    return render(request, \'admin/qr_detail.html\', {\'qr_obj\': qr_obj, \'scan_url\': scan_url, \'qr_b64\': qr_b64})


# ── API ───────────────────────────────────────────────────────────────────────

@login_required
def get_notifications_api(request):
    notifs = Notification.objects.filter(recipient=request.user, is_read=False).order_by(\'-created_at\')[:10]
    data = [{\'id\': n.id, \'title\': n.title, \'message\': n.message, \'type\': n.notification_type, \'time\': n.created_at.strftime(\'%H:%M\')} for n in notifs]
    return JsonResponse({\'notifications\': data, \'count\': len(data)})


@login_required
def get_schedule_reminders_api(request):
    if request.user.is_staff:
        return JsonResponse({\'schedules\': []})
    try:
        profile = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return JsonResponse({\'schedules\': []})
    today = timezone.localdate()
    now = timezone.localtime().time()
    schedules = ClassSchedule.objects.filter(teacher=profile, scheduled_date=today, is_completed=False).select_related(\'timetable_entry\')
    data = []
    for s in schedules:
        start = s.timetable_entry.start_time
        diff = (datetime.combine(today, start) - datetime.combine(today, now)).total_seconds() / 60
        data.append({\'id\': s.id, \'subject\': s.timetable_entry.subject, \'start_time\': start.strftime(\'%H:%M\'), \'end_time\': s.timetable_entry.end_time.strftime(\'%H:%M\'), \'minutes_until\': round(diff)})
    return JsonResponse({\'schedules\': data})


@login_required
def mark_schedule_complete(request, schedule_id):
    if request.method == \'POST\':
        try:
            profile = request.user.teacher_profile
            schedule = get_object_or_404(ClassSchedule, id=schedule_id, teacher=profile)
            schedule.is_completed = True
            schedule.save()
            return JsonResponse({\'status\': \'ok\'})
        except TeacherProfile.DoesNotExist:
            return JsonResponse({\'status\': \'error\'}, status=403)
    return JsonResponse({\'status\': \'error\'}, status=405)


# ── Super Admin ───────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_superadmin)
def superadmin_dashboard(request):
    admins = User.objects.filter(is_staff=True).select_related(\'admin_profile\')
    teachers = TeacherProfile.objects.select_related(\'user\').all()
    pending = teachers.filter(is_approved=False)
    today = timezone.localdate()
    today_att = Attendance.objects.filter(date=today)
    return render(request, \'superadmin/dashboard.html\', {
        \'admins\': admins, \'teachers\': teachers, \'pending\': pending,
        \'total_admins\': admins.count(), \'total_teachers\': teachers.count(),
        \'pending_count\': pending.count(),
        \'present_today\': today_att.filter(school_status=\'present\').count(),
        \'today\': today,
    })


@login_required
@user_passes_test(is_superadmin)
def superadmin_admins(request):
    admins = User.objects.filter(is_staff=True).select_related(\'admin_profile\').order_by(\'username\')
    return render(request, \'superadmin/admins.html\', {\'admins\': admins})


@login_required
@user_passes_test(is_superadmin)
def superadmin_create_admin(request):
    error = None
    if request.method == \'POST\':
        username = request.POST.get(\'username\', \'\').strip()
        password = request.POST.get(\'password\', \'\').strip()
        first_name = request.POST.get(\'first_name\', \'\').strip()
        last_name = request.POST.get(\'last_name\', \'\').strip()
        email = request.POST.get(\'email\', \'\').strip()
        if not username or not password:
            error = \'Username and password are required.\'
        elif User.objects.filter(username=username).exists():
            error = f\'Username "{username}" already exists.\'
        else:
            new_user = User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name, email=email, is_staff=True, is_active=True)
            AdminProfile.objects.create(user=new_user, role=\'admin\', created_by=request.user)
            messages.success(request, f\'Admin "{username}" created.\')
            return redirect(\'superadmin_admins\')
    return render(request, \'superadmin/create_admin.html\', {\'error\': error})


@login_required
@user_passes_test(is_superadmin)
def superadmin_delete_admin(request, admin_id):
    admin_user = get_object_or_404(User, id=admin_id, is_staff=True)
    if admin_user == request.user:
        messages.error(request, \'Cannot delete your own account.\')
        return redirect(\'superadmin_admins\')
    try:
        if admin_user.admin_profile.role == \'superadmin\':
            messages.error(request, \'Cannot delete another Super Admin.\')
            return redirect(\'superadmin_admins\')
    except Exception:
        pass
    if request.method == \'POST\':
        name = admin_user.get_full_name() or admin_user.username
        admin_user.delete()
        messages.success(request, f\'Admin "{name}" deleted.\')
        return redirect(\'superadmin_admins\')
    return render(request, \'superadmin/confirm_delete_admin.html\', {\'admin_user\': admin_user})


@login_required
@user_passes_test(is_superadmin)
def superadmin_teachers(request):
    teachers = TeacherProfile.objects.select_related(\'user\').all().order_by(\'-date_joined\')
    return render(request, \'superadmin/teachers.html\', {\'teachers\': teachers})


@login_required
@user_passes_test(is_superadmin)
def superadmin_approve_teacher(request, teacher_id):
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    teacher.is_approved = True
    teacher.save()
    Notification.objects.create(
        recipient=teacher.user, sender=request.user,
        title=\'Account Approved\',
        message=\'Your teacher account has been approved by the Super Admin. You can now login.\',
        notification_type=\'admin\'
    )
    messages.success(request, f\'{teacher.full_name} approved.\')
    return redirect(\'superadmin_teachers\')


@login_required
@user_passes_test(is_superadmin)
def superadmin_delete_teacher(request, teacher_id):
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    if request.method == \'POST\':
        name = teacher.full_name
        teacher.user.delete()
        messages.success(request, f\'{name} deleted.\')
        return redirect(\'superadmin_teachers\')
    return render(request, \'superadmin/confirm_delete_teacher.html\', {\'teacher\': teacher})
'''
with open('core/views_part2.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('views part2 written')
