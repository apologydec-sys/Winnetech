from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import random
import string
from datetime import date


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
    ('computer_system_servicing', 'Computer System & Servicing'),
    ('workshop_practice_power', 'Workshop Practice & Power Management'),
    ('networking_data_comm', 'Networking & Data Communication'),
    ('plumbing_general', 'Plumbing (General)'),
    ('plumbing_installation', 'Plumbing Installation'),
    ('plumbing_maintenance', 'Plumbing Maintenance'),
    ('electrical_installation', 'Electrical Installation'),
    ('electrical_maintenance', 'Electrical Maintenance'),
    ('electrical_wiring', 'Electrical Wiring'),
    ('welding_fabrication', 'Welding & Fabrication'),
    ('metal_work', 'Metal Work'),
    ('fashion_design', 'Fashion Design'),
    ('garment_construction', 'Garment Construction'),
    ('textile_studies', 'Textile Studies'),
    ('catering_general', 'Catering (General)'),
    ('food_beverage', 'Food & Beverage'),
    ('hospitality', 'Hospitality Management'),
    ('mechanical_engineering', 'Mechanical Engineering'),
    ('machine_maintenance', 'Machine Maintenance'),
    ('auto_mechanics', 'Auto Mechanics'),
    ('auto_electrical', 'Auto Electrical'),
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
    ('core', 'Core Subjects'),
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
    count = TeacherProfile.objects.count() + 1
    for attempt in range(count, count + 9999):
        candidate = f'WTI{str(attempt).zfill(4)}'
        if not TeacherProfile.objects.filter(staff_id=candidate).exists():
            return candidate
    while True:
        suffix = ''.join(random.choices(string.digits, k=6))
        candidate = f'WTI{suffix}'
        if not TeacherProfile.objects.filter(staff_id=candidate).exists():
            return candidate


# ─── Admin Profile ────────────────────────────────────────────────────────────

class AdminProfile(models.Model):
    ROLE_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('admin', 'Admin'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='admin')
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_admins'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def is_superadmin(self):
        return self.role == 'superadmin'


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
    course_type = models.CharField(max_length=20, choices=COURSE_TYPE_CHOICES)
    preferred_subject = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True)
    cv_document = models.FileField(upload_to='documents/cv/', null=True, blank=True)
    certificate_document = models.FileField(upload_to='documents/certificates/', null=True, blank=True)
    id_document = models.FileField(upload_to='documents/ids/', null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    profile_complete = models.BooleanField(default=False)  # True after teacher fills details
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


# ─── QR Code — Two types: school_attendance and lesson ───────────────────────

class QRCode(models.Model):
    QR_TYPE_CHOICES = [
        ('school_attendance', 'School Attendance'),
        ('lesson', 'Lesson'),
    ]
    code = models.UUIDField(default=uuid.uuid4, unique=True)
    qr_type = models.CharField(max_length=20, choices=QR_TYPE_CHOICES, default='school_attendance')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='qr_codes')
    created_at = models.DateTimeField(auto_now_add=True)
    # Valid for 5 years from creation
    valid_from = models.DateField(default=date.today)
    valid_until = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    qr_image = models.ImageField(upload_to='qrcodes/', null=True, blank=True)
    label = models.CharField(max_length=100, default='School Attendance QR')

    def save(self, *args, **kwargs):
        if not self.valid_until and self.valid_from:
            try:
                self.valid_until = self.valid_from.replace(year=self.valid_from.year + 5)
            except ValueError:
                # Feb 29 edge case
                self.valid_until = self.valid_from.replace(year=self.valid_from.year + 5, day=28)
        super().save(*args, **kwargs)

    @property
    def is_valid_today(self):
        today = date.today()
        if not self.valid_until:
            return self.is_active
        return self.is_active and self.valid_from <= today <= self.valid_until

    def __str__(self):
        return f"{self.get_qr_type_display()} QR — {self.label}"

    class Meta:
        ordering = ['-created_at']


# ─── Attendance ───────────────────────────────────────────────────────────────

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]
    LESSON_STATUS_CHOICES = [
        ('done', 'Lesson Done'),
        ('not_done', 'Lesson Not Done'),
        ('pending', 'Pending'),
    ]

    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.localdate)

    # School attendance (scan school QR)
    school_qr = models.ForeignKey(
        QRCode, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='school_attendances'
    )
    school_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='absent')
    check_in_time = models.TimeField(null=True, blank=True)

    # Lesson attendance (scan lesson QR)
    lesson_qr = models.ForeignKey(
        QRCode, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lesson_attendances'
    )
    lesson_status = models.CharField(max_length=10, choices=LESSON_STATUS_CHOICES, default='pending')
    lesson_done_time = models.TimeField(null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['teacher', 'date']
        ordering = ['-date', 'teacher']

    def __str__(self):
        return f"{self.teacher.full_name} — {self.date} — School:{self.school_status} Lesson:{self.lesson_status}"


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
        return f"{self.day} — {self.subject} ({self.start_time}–{self.end_time})"


# ─── Notifications ────────────────────────────────────────────────────────────

class Notification(models.Model):
    TYPE_CHOICES = [
        ('attendance', 'Attendance'),
        ('schedule', 'Schedule'),
        ('reminder', 'Class Reminder'),
        ('general', 'General'),
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
        return f"{self.teacher.full_name} — {self.timetable_entry.subject} on {self.scheduled_date}"


# ─── School Location Settings ─────────────────────────────────────────────────

class SchoolLocation(models.Model):
    """Stores school location and allowed radius for QR code scanning."""
    name = models.CharField(max_length=200, default='Main Campus')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, help_text='School latitude coordinate')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, help_text='School longitude coordinate')
    allowed_radius = models.PositiveIntegerField(default=100, help_text='Allowed radius in meters')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'School Location'
        verbose_name_plural = 'School Locations'

    def __str__(self):
        return f"{self.name} (Radius: {self.allowed_radius}m)"

    def is_within_radius(self, user_lat, user_lon):
        """Check if user coordinates are within allowed radius using Haversine formula."""
        from math import radians, cos, sin, sqrt, asin

        # Convert decimal degrees to radians
        lat1, lon1 = radians(float(self.latitude)), radians(float(self.longitude))
        lat2, lon2 = radians(float(user_lat)), radians(float(user_lon))

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of Earth in meters
        r = 6371000
        distance = c * r

        return distance <= self.allowed_radius
