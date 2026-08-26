from django.contrib import admin
from .models import (
    TeacherProfile, Attendance, QRCode, Notification,
    TimetableEntry, ClassSchedule, AdminProfile
)


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'staff_id', 'course_type', 'preferred_subject', 'is_approved', 'date_joined']
    list_filter = ['is_approved', 'course_type', 'gender', 'qualification']
    search_fields = ['user__first_name', 'user__last_name', 'staff_id', 'phone']
    actions = ['approve_teachers']

    def approve_teachers(self, request, queryset):
        queryset.update(is_approved=True)
    approve_teachers.short_description = 'Approve selected teachers'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'date', 'school_status', 'lesson_status', 'check_in_time', 'lesson_done_time']
    list_filter = ['school_status', 'lesson_status', 'date']
    search_fields = ['teacher__user__first_name', 'teacher__user__last_name']


@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ['label', 'qr_type', 'valid_from', 'valid_until', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'qr_type']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']


@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = ['day', 'subject', 'start_time', 'end_time', 'teacher', 'is_break']
    list_filter = ['day', 'is_break', 'course_type']


@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'timetable_entry', 'scheduled_date', 'is_completed']
    list_filter = ['is_completed', 'scheduled_date']


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'created_at']
    list_filter = ['role']
