from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import (
    TeacherProfile, ELECTIVE_SUBJECTS, DEPARTMENT_SUBJECTS,
    DEPARTMENT_CHOICES, COURSE_TYPE_CHOICES, GENDER_CHOICES,
    QUALIFICATION_CHOICES, TimetableEntry, Notification,
    QRCode, ClassSchedule, SchoolLocation
)

# All valid subject values for server-side validation
ALL_SUBJECT_VALUES = (
    [v for v, _ in ELECTIVE_SUBJECTS] +
    [v for v, _ in DEPARTMENT_SUBJECTS]
)


class TeacherRegistrationForm(UserCreationForm):
    # ── Staff ID (chosen by teacher, used for login) ───────────────────────
    staff_id = forms.CharField(
        max_length=20, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. WTI0042',
            'style': 'text-transform:uppercase;font-weight:600;letter-spacing:1px',
        }),
        help_text='This will be your login ID. Must be unique (e.g. WTI0042).'
    )

    # ── Personal ──────────────────────────────────────────────
    first_name = forms.CharField(
        max_length=100, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(
        max_length=100, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    phone = forms.CharField(
        max_length=20, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))
    gender = forms.ChoiceField(
        choices=[('', '-- Select Gender --')] + list(GENDER_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'}))

    # ── Professional ──────────────────────────────────────────
    qualification = forms.ChoiceField(
        choices=[('', '-- Select Qualification --')] + list(QUALIFICATION_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'}))
    years_of_experience = forms.IntegerField(
        min_value=0, initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}))
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief Bio'}))

    # ── Course Preference ─────────────────────────────────────
    course_type = forms.ChoiceField(
        choices=[('', '-- Select Course Type --')] + list(COURSE_TYPE_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'}))
    preferred_subject = forms.CharField(
        max_length=100, required=True,
        widget=forms.HiddenInput())
    department = forms.CharField(
        max_length=100, required=False,
        widget=forms.HiddenInput())

    # ── Documents ─────────────────────────────────────────────
    profile_photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}))
    certificate_document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        # No username field — we generate it from staff_id
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Create a strong password'})
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control', 'placeholder': 'Confirm your password'})

    def clean_staff_id(self):
        sid = self.cleaned_data.get('staff_id', '').strip().upper()
        if not sid:
            raise ValidationError('Staff ID is required.')
        if len(sid) < 4:
            raise ValidationError('Staff ID must be at least 4 characters.')
        # Check uniqueness
        if TeacherProfile.objects.filter(staff_id=sid).exists():
            raise ValidationError(f'Staff ID "{sid}" is already taken. Choose a different one.')
        # Also check no user with this username
        if User.objects.filter(username=sid).exists():
            raise ValidationError(f'Staff ID "{sid}" is already in use.')
        return sid

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError('A user with this email address already exists.')
        return email

    def clean_gender(self):
        gender = self.cleaned_data.get('gender', '')
        if not gender:
            raise ValidationError('Please select your gender.')
        return gender

    def clean_qualification(self):
        qual = self.cleaned_data.get('qualification', '')
        if not qual:
            raise ValidationError('Please select your qualification.')
        return qual

    def clean_course_type(self):
        ct = self.cleaned_data.get('course_type', '')
        if not ct:
            raise ValidationError('Please select a course type (Core Subjects or Departmental).')
        return ct

    def clean_preferred_subject(self):
        subject = self.cleaned_data.get('preferred_subject', '').strip()
        if not subject:
            raise ValidationError('Please select a preferred subject.')
        return subject

    def clean_years_of_experience(self):
        yoe = self.cleaned_data.get('years_of_experience')
        if yoe is None or yoe < 0:
            return 0
        return yoe

    def save(self, commit=True):
        user = super().save(commit=False)
        staff_id = self.cleaned_data['staff_id']
        # Use staff_id as the username so login works
        user.username = staff_id
        user.first_name = self.cleaned_data['first_name'].strip()
        user.last_name = self.cleaned_data['last_name'].strip()
        user.email = self.cleaned_data['email'].strip().lower()
        if commit:
            user.save()
            TeacherProfile.objects.create(
                user=user,
                staff_id=staff_id,  # explicitly set — no auto-generation needed
                phone=self.cleaned_data.get('phone', '').strip(),
                gender=self.cleaned_data.get('gender', ''),
                address='',
                qualification=self.cleaned_data.get('qualification', ''),
                specialization='',
                years_of_experience=self.cleaned_data.get('years_of_experience', 0),
                bio=self.cleaned_data.get('bio', '').strip(),
                course_type=self.cleaned_data.get('course_type', ''),
                preferred_subject=self.cleaned_data.get('preferred_subject', '').strip(),
                department=self.cleaned_data.get('department', '').strip(),
                profile_photo=self.cleaned_data.get('profile_photo'),
                certificate_document=self.cleaned_data.get('certificate_document'),
            )
        return user


# ── Auth Forms ────────────────────────────────────────────────────────────────

class TeacherLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))


class AdminLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Admin Username'}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Admin Password'}))


# ── Admin Forms ───────────────────────────────────────────────────────────────

class NotificationForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=False),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='-- Select Teacher --')

    class Meta:
        model = Notification
        fields = ['recipient', 'title', 'message', 'notification_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Notification Title'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'notification_type': forms.Select(attrs={'class': 'form-select'}),
        }


class TimetableEntryForm(forms.ModelForm):
    class Meta:
        model = TimetableEntry
        fields = ['day', 'subject', 'start_time', 'end_time', 'teacher', 'is_break', 'room', 'course_type']
        widgets = {
            'day': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
            'is_break': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'room': forms.TextInput(attrs={'class': 'form-control'}),
            'course_type': forms.Select(attrs={'class': 'form-select'}),
        }


class ClassScheduleForm(forms.ModelForm):
    class Meta:
        model = ClassSchedule
        fields = ['timetable_entry', 'teacher', 'scheduled_date']
        widgets = {
            'timetable_entry': forms.Select(attrs={'class': 'form-select'}),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class QRCodeForm(forms.ModelForm):
    class Meta:
        model = QRCode
        fields = ['qr_type', 'label']
        widgets = {
            'qr_type': forms.Select(attrs={'class': 'form-select'}),
            'label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Main Gate QR / Classroom QR'}),
        }


class SchoolLocationForm(forms.ModelForm):
    class Meta:
        model = SchoolLocation
        fields = ['name', 'latitude', 'longitude', 'allowed_radius', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Main Campus'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001', 'placeholder': 'e.g. 5.6037'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001', 'placeholder': 'e.g. -0.1870'}),
            'allowed_radius': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Radius in meters'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
