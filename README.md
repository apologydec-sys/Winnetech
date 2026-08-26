# Winneba Technical Institute — Staff Management System

A comprehensive full-stack Django web application for managing teachers, attendance, timetables, and real-time communication at Winneba Technical Institute.

## 🌟 Features

### 1. **Welcome Page**
- Modern animated slideshow with school images
- Particle effects and smooth animations
- Two portals: Admin Portal & Teacher Registration
- Clean, responsive UI design

### 2. **Teacher Registration & Authentication**
- Multi-step registration form with validation
- Profile photo and document uploads (CV, certificates, ID)
- Course type selection (Electives vs Departmental)
- Subject preference based on specialization
- Admin approval workflow

### 3. **Admin Portal**
- **Dashboard**: Overview of attendance, pending approvals, today's timetable
- **Teacher Management**: View, approve, reject teacher applications
- **Attendance System**: QR code-based attendance tracking
- **Timetable Management**: Create and manage weekly class schedules
- **Class Scheduling**: Assign teachers to specific classes with automatic notifications
- **Notifications**: Send announcements to teachers
- **Real-time Chat**: WebSocket-based chat with teachers
- **QR Code Generation**: Generate and print attendance QR codes

### 4. **Teacher Portal**
- **Dashboard**: Personal attendance status, today's classes, notifications
- **QR Scanner**: Built-in camera scanner for attendance marking
- **Timetable View**: Full weekly timetable
- **Real-time Chat**: Communicate with administrators
- **Class Reminders**: Automatic 10-minute reminders before classes
- **Notification System**: Receive announcements with sound alerts

### 5. **QR Code Attendance System**
- Generate daily QR codes for attendance
- Teachers scan QR code to check in
- Second scan marks lesson completion
- Automatic absent marking for non-scanned teachers
- School hours: 7:00 AM – 3:30 PM

### 6. **Real-time Features**
- **WebSocket Chat**: Instant messaging between admin and teachers
- **Live Notifications**: Push notifications with sound alerts
- **Class Reminders**: 10-minute, 2-minute, and start-time reminders
- **Notification Polling**: Auto-refresh every 15 seconds

### 7. **Responsive Design**
- Mobile-first approach
- Works on all devices (desktop, tablet, mobile)
- Touch-friendly interface
- Optimized for classroom wall-mounted tablets

## 📋 Course Structure

### Electives
- Mathematics
- English Language
- Social Studies
- ICT
- Science
- EST (Entrepreneur Skills Training)

### Departmental (Vocational)
1. **Information Technology**
   - Computer System & Servicing
   - Workshop Practice & Power Management
   - Networking & Data Communication

2. **Plumbing**
   - Plumbing (General)
   - Plumbing Installation
   - Plumbing Maintenance

3. **Electricals**
   - Electrical Installation
   - Electrical Maintenance
   - Electrical Wiring

4. **Welding & Fabrication**
   - Welding & Fabrication
   - Metal Work

5. **Fashion**
   - Fashion Design
   - Garment Construction
   - Textile Studies

6. **Catering**
   - Catering (General)
   - Food & Beverage
   - Hospitality Management

7. **Mechanical Engineering**
   - Mechanical Engineering
   - Machine Maintenance

8. **Auto Mechanics**
   - Auto Mechanics
   - Auto Electrical

9. **Building & Construction**
   - Building & Construction
   - Masonry
   - Carpentry

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### 1. Install Dependencies
```bash
pip install django channels daphne qrcode[pil] pillow django-crispy-forms crispy-bootstrap5 django-widget-tweaks
```

### 2. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Setup Initial Data
```bash
python setup_data.py
```

This creates:
- Admin user (username: `admin`, password: `admin123`)
- Full weekly timetable

### 4. Start the Server
```bash
python manage.py runserver
```

### 5. Access the Application
- **Welcome Page**: http://127.0.0.1:8000/
- **Admin Portal**: http://127.0.0.1:8000/admin-portal/
- **Teacher Login**: http://127.0.0.1:8000/login/
- **Teacher Registration**: http://127.0.0.1:8000/register/

## 🔐 Default Credentials

### Admin
- **Username**: admin
- **Password**: admin123

### Test Teacher (after registration)
Register a new teacher account and wait for admin approval.

## 📁 Project Structure

```
winnitech/
├── core/                      # Main application
│   ├── models.py             # Database models
│   ├── views.py              # View functions
│   ├── forms.py              # Form definitions
│   ├── urls.py               # URL routing
│   ├── consumers.py          # WebSocket consumers
│   ├── routing.py            # WebSocket routing
│   ├── admin.py              # Admin panel config
│   └── migrations/           # Database migrations
├── templates/                 # HTML templates
│   ├── admin/                # Admin portal templates
│   ├── teacher/              # Teacher portal templates
│   ├── auth/                 # Authentication templates
│   ├── qr/                   # QR scanner templates
│   ├── base.html             # Base template
│   └── welcome.html          # Landing page
├── static/                    # Static files
│   ├── css/
│   │   └── main.css          # Main stylesheet
│   ├── js/
│   │   └── main.js           # JavaScript functionality
│   └── images/               # School images
├── media/                     # User uploads
│   ├── profiles/             # Profile photos
│   ├── documents/            # CV, certificates, IDs
│   └── qrcodes/              # Generated QR codes
├── winnitech/                 # Project settings
│   ├── settings.py           # Django settings
│   ├── urls.py               # Root URL config
│   ├── asgi.py               # ASGI config (WebSockets)
│   └── wsgi.py               # WSGI config
├── manage.py                  # Django management script
├── setup_data.py             # Initial data setup
└── README.md                 # This file
```

## 🎨 Technology Stack

### Backend
- **Django 5.x**: Web framework
- **Channels**: WebSocket support
- **Daphne**: ASGI server
- **SQLite**: Database (can be upgraded to PostgreSQL)

### Frontend
- **Bootstrap 5**: UI framework
- **Font Awesome 6**: Icons
- **Poppins Font**: Typography
- **Vanilla JavaScript**: Interactivity
- **WebSocket API**: Real-time communication

### Libraries
- **qrcode**: QR code generation
- **Pillow**: Image processing
- **html5-qrcode**: Browser-based QR scanner
- **django-crispy-forms**: Form rendering
- **django-widget-tweaks**: Form customization

## 🔧 Configuration

### School Hours
Edit in `winnitech/settings.py`:
```python
SCHOOL_START_TIME = '07:00'
SCHOOL_END_TIME = '15:30'
```

### Time Zone
```python
TIME_ZONE = 'Africa/Accra'
```

### WebSocket Configuration
Uses in-memory channel layer (no Redis required for development).
For production, configure Redis in `settings.py`.

## 📱 Mobile Responsiveness

The system is fully responsive and works on:
- Desktop computers (1920px+)
- Laptops (1366px+)
- Tablets (768px+)
- Mobile phones (320px+)

## 🔔 Notification System

### Types
- **Attendance**: Check-in/lesson completion alerts
- **Schedule**: Class assignment notifications
- **Reminder**: 10-minute class reminders
- **General**: Announcements
- **Admin**: Administrative notices

### Sound Alerts
- Notification sound: Two-tone beep
- Reminder sound: Four-note chime
- Success sound: Three-note ascending

## 🎯 Key Workflows

### Teacher Registration Flow
1. Teacher fills multi-step registration form
2. Uploads documents (CV, certificates, ID)
3. Selects course type and preferred subject
4. Admin reviews application
5. Admin approves/rejects
6. Teacher receives notification
7. Teacher can login

### Attendance Flow
1. Admin generates daily QR code
2. QR code displayed/printed in classroom
3. Teacher scans QR code (check-in)
4. System marks teacher present
5. Admin receives notification
6. After lesson, teacher scans again (lesson done)
7. System records completion time

### Class Scheduling Flow
1. Admin creates timetable entries
2. Admin schedules specific class
3. Teacher receives notification
4. 10 minutes before class: First reminder
5. 2 minutes before class: Second reminder
6. At class time: Final reminder
7. Teacher scans QR after teaching

## 🐛 Troubleshooting

### QR Scanner Not Working
- Ensure HTTPS or localhost
- Grant camera permissions
- Use modern browser (Chrome, Firefox, Safari)

### WebSocket Connection Failed
- Check if Daphne is running
- Verify ASGI configuration
- Check firewall settings

### Images Not Loading
- Run `python manage.py collectstatic`
- Check MEDIA_ROOT and MEDIA_URL settings
- Verify file permissions

## 📄 License

This project is developed for Winneba Technical Institute.

## 👨‍💻 Developer

Built with ❤️ for Winneba Technical Institute
Transforming and Empowering the Youth Through Vocational Skills

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section
2. Review Django logs: `python manage.py runserver`
3. Check browser console for JavaScript errors
4. Verify database migrations are applied

---

**Winneba Technical Institute** — Est. Winneba, Ghana
