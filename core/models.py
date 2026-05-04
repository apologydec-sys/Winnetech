from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import random
import string


# ─── Subject / Course Choices ────────────────────────────────────────────────

ELECTIVE_SUBJECTS = [
    ('mathematics', 'Mathematics'),
    ('english_language', 'English Language'),
    ('social_studies', 'Social Studies'),
    ('ict', 'ICT'),
    ('science', 'Science'),
    ('est', 'EST (Entrepreneur Skills Training)'),
]

DEPARTMENT_SUBJECTS = [
    # Information Technology
    ('computer_system_servicing', 'Computer System & Servicing'),
    ('workshop_practice_power', 'Workshop Practice & Power Management'),
    ('networking_data_comm', 'Networking & Data Communication'),
    # Plumbing
    ('plumbing_general', 'Plumbing (General)'),
    ('plumbing_installation', 'Plumbing Installation'),
    ('plumbing_maintenance', 'Plumbing Maintenance'),
    # Electricals
    ('electrical_installation', 'Electrical Installation'),
    ('electrical_maintenance', 'Electrical Maintenance'),
    ('electrical_wiring', 'Electrical Wiring'),
    # Welding & Fabrication
    ('welding_fabrication', 'Welding & Fabrication'),
    ('metal_work', 'Metal Work'),
    # Fashion
    ('fashion_design', 'Fashion Design'),
    ('garment_construction', 'Garment Construction'),
    ('textile_studies', 'Textile Studies'),
    # Catering
    ('catering_general', 'Catering (General)'),
    ('food_beverage', 'Food & Beverage'),
    ('hospitality', 'Hospitality Management'),
    # Mechanical Engineering
    ('mechanical_engineering', 'Mechanical Engineering'),
    ('machine_maintenance', 'Machine Maintenance'),
    # Auto Mechanics
    ('auto_mechanics', 'Auto Mechanics'),
    ('auto_electrical', 'Auto Electrical'),
    # Building & Construction
    ('building_construction', 'Building & Construction'),
    ('masonry', 'Masonry'),
    ('carpentry', 'Carpentry'),
]

DEPARTMENT_CHOICES = [
    ('information_technology', 'Information Technology'),
    ('plumbing', 'Plumbing'),
    ('electricals', 'Electricals'),
    ('welding_fabrication', 'Welding & Fabrication'),
    ('fashion', 'Fashion'),
    ('catering', 'Catering'),
    ('mechanical_engineering', 'Mechanical Engineering'),
    ('auto_mechanics', 'Auto Mechanics'),
    ('building_construction', 'Building & Construction'),
]

COURSE_TYPE_CHOICES = [
    ('electives', 'Electives'),
    ('departmental', 'Departmental'),
]

GENDER_CHOICES = [
    ('male', 'Male'),
    ('female', 'Female'),
    ('other', 'Other'),
]

QUALIFICATION_CHOICES = [
    ('phd', 'PhD'),
    ('masters', "Master's Degree"),
    ('degree', "Bachelor's Degree"),
    ('hnd', 'HND'),
    ('diploma', 'Diploma'),
    ('certificate', 'Certificate'),
    ('other', 'Other'),
]


def generate_unique_staff_id():
    """Generate a guaranteed-unique staff ID like WTI0001, WTI0002 …
    Falls back to a random suffix if sequential IDs collide (e.g. after deletions)."""
    # Try sequential first
    count = TeacherProfile.objects.count() + 1
    for attempt in range(count, count + 9999):
        candidate = f'WTI{str(attempt).zfill(4)}'
        if not TeacherProfile.objects.filter(staff_id=candidate).exists():
            return candidate
    # Absolute fallback: random alphanumeric suffix
    while True:
        suffix = ''.join(random.choices(string.digits, k=6))
        candidate = f'WTI{suffix}'
        if not TeacherProfile.objects.filter(staff_id=candidate).exists():
            return candidate


# ─── Teacher Profile ─────────────────────────────────────────────────────────

class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    staff_id = models.CharField(max_length=20, unique=True, blank=True)
    phone = models.CharField(max_length=20)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField()
    profile_photo = models.ImageField(upload_to='profiles/', null=True, blank=True)
    qualification = models.CharField(max_length=20, choices=QUALIFICATION_CHOICES)
    specialization = models.CharField(max_length=200)
    years_of_experience = models.PositiveIntegerField(default=0)
    previous_school = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)

    # Course preference
    course_type = models.CharField(max_length=20, choices=COURSE_TYPE_CHOICES)
    preferred_subject = models.CharField(max_length=100)
    # department stored as free text so any value is accepted without choices validation
    department = models.CharField(max_length=100, blank=True)

    # Documents
    cv_document = models.FileField(upload_to='documents/cv/', null=True, blank=True)
    certificate_document = models.FileField(upload_to='documents/certificates/', null=True, blank=True)
    id_document = models.FileField(upload_to='documents/ids/', null=True, blank=True)

    # Status
    is_approved = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)

    def save(self, *args, **kwargs):
        if not self.staff_id:
            self.staff_id = generate_unique_staff_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.staff_id})"

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    def get_department_display_name(self):
        dept_map = dict(DEPARTMENT_CHOICES)
        return dept_map.get(self.department, self.department)


# ─── Attendance ───────────────────────────────────────────────────────────────

class QRCode(models.Model):
    code = models.UUIDField(default=uuid.uuid4, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='qr_codes')
    created_at = models.DateTimeField(auto_now_add=True)
    date = models.DateField(default=timezone.localdate)
    is_active = models.BooleanField(default=True)
    qr_image = models.ImageField(upload_to='qrcodes/', null=True, blank=True)
    label = models.CharField(max_length=100, default='Daily Attendance QR')

    def __str__(self):
        return f"QR Code - {self.date} ({self.label})"

    class Meta:
        ordering = ['-created_at']


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]
    SCAN_TYPE_CHOICES = [
        ('check_in', 'Check In'),
        ('lesson_done', 'Lesson Done'),
    ]

    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='attendances')
    qr_code = models.ForeignKey(QRCode, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(default=timezone.localdate)
    check_in_time = models.TimeField(null=True, blank=True)
    lesson_done_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='absent')
    scan_type = models.CharField(max_length=20, choices=SCAN_TYPE_CHOICES, default='check_in')
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['teacher', 'date']
        ordering = ['-date', 'teacher']

    def __str__(self):
        return f"{self.teacher.full_name} - {self.date} - {self.status}"


# ─── Timetable ────────────────────────────────────────────────────────────────

class TimetableEntry(models.Model):
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
    ]

    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    subject = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    teacher = models.ForeignKey(
        TeacherProfile, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='timetable_entries'
    )
    is_break = models.BooleanField(default=False)
    room = models.CharField(max_length=50, blank=True)
    course_type = models.CharField(max_length=20, choices=COURSE_TYPE_CHOICES, blank=True)

    class Meta:
        ordering = ['day', 'start_time']

    def __str__(self):
        return f"{self.day} - {self.subject} ({self.start_time}-{self.end_time})"


# ─── Notifications ────────────────────────────────────────────────────────────

class Notification(models.Model):
    TYPE_CHOICES = [
        ('attendance', 'Attendance'),
        ('schedule', 'Schedule'),
        ('reminder', 'Class Reminder'),
        ('general', 'General'),
        ('chat', 'Chat'),
        ('admin', 'Admin Notice'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='general')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_timetable = models.ForeignKey(TimetableEntry, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"To {self.recipient.username}: {self.title}"


# ─── Chat ─────────────────────────────────────────────────────────────────────

class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='chat_attachments/', null=True, blank=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username} → {self.recipient.username}: {self.message[:50]}"


# ─── Class Schedule ───────────────────────────────────────────────────────────

class ClassSchedule(models.Model):
    timetable_entry = models.ForeignKey(TimetableEntry, on_delete=models.CASCADE, related_name='schedules')
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='schedules')
    scheduled_date = models.DateField()
    reminder_sent = models.BooleanField(default=False)
    reminder_10min_sent = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_schedules')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_date', 'timetable_entry__start_time']

    def __str__(self):
        return f"{self.teacher.full_name} - {self.timetable_entry.subject} on {self.scheduled_date}"
