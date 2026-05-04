from django.urls import path
from . import views

urlpatterns = [
    # Welcome
    path('', views.welcome, name='welcome'),
    path('sw.js', views.service_worker, name='service_worker'),
    path('offline/', views.offline_page, name='offline'),

    # Auth
    path('register/', views.teacher_register, name='teacher_register'),
    path('login/', views.teacher_login, name='teacher_login'),
    path('admin-portal/', views.admin_login, name='admin_login'),
    path('logout/', views.logout_view, name='logout'),

    # Teacher
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/chat/<int:admin_id>/', views.teacher_chat, name='teacher_chat'),
    path('teacher/notification/<int:notif_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('teacher/timetable/', views.view_timetable, name='view_timetable'),
    path('teacher/qr-scanner/', views.qr_scanner, name='qr_scanner'),

    # QR Scan
    path('scan/<uuid:qr_uuid>/', views.scan_qr, name='scan_qr'),

    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/teachers/', views.admin_teachers, name='admin_teachers'),
    path('admin-dashboard/teachers/<int:teacher_id>/', views.teacher_detail, name='teacher_detail'),
    path('admin-dashboard/teachers/<int:teacher_id>/approve/', views.approve_teacher, name='approve_teacher'),
    path('admin-dashboard/teachers/<int:teacher_id>/reject/', views.reject_teacher, name='reject_teacher'),
    path('admin-dashboard/attendance/', views.admin_attendance, name='admin_attendance'),
    path('admin-dashboard/timetable/', views.admin_timetable, name='admin_timetable'),
    path('admin-dashboard/timetable/<int:entry_id>/delete/', views.delete_timetable_entry, name='delete_timetable_entry'),
    path('admin-dashboard/schedule/', views.admin_schedule, name='admin_schedule'),
    path('admin-dashboard/notifications/', views.admin_notifications, name='admin_notifications'),
    path('admin-dashboard/chat/', views.admin_chat, name='admin_chat'),
    path('admin-dashboard/chat/<int:teacher_id>/', views.admin_chat, name='admin_chat_teacher'),
    path('admin-dashboard/qr/', views.generate_qr, name='generate_qr'),
    path('admin-dashboard/qr/<int:qr_id>/', views.qr_detail, name='qr_detail'),

    # API
    path('api/notifications/', views.get_notifications_api, name='notifications_api'),
    path('api/schedule-reminders/', views.get_schedule_reminders_api, name='schedule_reminders_api'),
    path('api/schedule/<int:schedule_id>/complete/', views.mark_schedule_complete, name='mark_schedule_complete'),
]
