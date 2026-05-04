T = """{% extends 'admin/base_admin.html' %}
{% load static %}
{% block title %}Admin Dashboard — WTI{% endblock %}
{% block page_title %}Dashboard{% endblock %}
{% block nav_dashboard %}active{% endblock %}
{% block mob_dashboard %}active{% endblock %}

{% block content %}
<!-- Stats -->
<div class="row g-3 mb-4">
  <div class="col-6 col-md-3">
    <div class="stat-card"><div class="stat-icon gold"><i class="fas fa-chalkboard-teacher"></i></div>
    <div class="stat-info"><h3>{{ total_teachers }}</h3><p>Total Teachers</p></div></div>
  </div>
  <div class="col-6 col-md-3">
    <div class="stat-card"><div class="stat-icon green"><i class="fas fa-user-check"></i></div>
    <div class="stat-info"><h3>{{ present_count }}</h3><p>Present Today</p></div></div>
  </div>
  <div class="col-6 col-md-3">
    <div class="stat-card"><div class="stat-icon red"><i class="fas fa-user-times"></i></div>
    <div class="stat-info"><h3>{{ absent_count }}</h3><p>Absent Today</p></div></div>
  </div>
  <div class="col-6 col-md-3">
    <div class="stat-card"><div class="stat-icon blue"><i class="fas fa-clock"></i></div>
    <div class="stat-info"><h3>{{ pending_teachers.count }}</h3><p>Pending Approval</p></div></div>
  </div>
</div>

<div class="row g-3">
  <!-- Left: Departments -->
  <div class="col-lg-8">
    <!-- Departments with teachers -->
    {% for dept_name, dept_teachers in departments.items %}
    <div class="wti-card mb-3">
      <div class="wti-card-header">
        <h5><i class="fas fa-building"></i> {{ dept_name }}</h5>
        <span style="background:rgba(0,48,135,.1);color:#003087;font-size:.72rem;font-weight:700;padding:3px 10px;border-radius:20px">{{ dept_teachers.count }} Teacher{{ dept_teachers.count|pluralize }}</span>
      </div>
      <div style="padding:0">
        {% for t in dept_teachers %}
        <div style="display:flex;align-items:center;gap:.8rem;padding:.8rem 1.2rem;border-bottom:1px solid #f8f9fa">
          <div style="width:38px;height:38px;border-radius:50%;background:linear-gradient(135deg,#003087,#0047b3);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:.82rem;flex-shrink:0;overflow:hidden">
            {% if t.profile_photo %}<img src="{{ t.profile_photo.url }}" style="width:100%;height:100%;object-fit:cover">{% else %}{{ t.user.first_name|first|upper }}{{ t.user.last_name|first|upper }}{% endif %}
          </div>
          <div style="flex:1">
            <div style="font-weight:600;font-size:.87rem;color:#001f5c">{{ t.full_name }}</div>
            <small style="color:#888">{{ t.staff_id }} &middot; {{ t.preferred_subject|title }}</small>
          </div>
          {% with att=today_att %}
          {% for a in att %}{% if a.teacher.id == t.id %}
            {% if a.school_status == 'present' %}<span style="background:rgba(40,167,69,.1);color:#28a745;font-size:.7rem;font-weight:600;padding:3px 8px;border-radius:20px"><i class="fas fa-check-circle me-1"></i>Present</span>
            {% else %}<span style="background:rgba(220,53,69,.1);color:#dc3545;font-size:.7rem;font-weight:600;padding:3px 8px;border-radius:20px"><i class="fas fa-times-circle me-1"></i>Absent</span>{% endif %}
          {% endif %}{% endfor %}
          {% endwith %}
          <a href="{% url 'teacher_detail' t.id %}" style="background:#f0f2f5;color:#555;border:none;border-radius:8px;padding:4px 10px;font-size:.73rem;font-weight:600;text-decoration:none"><i class="fas fa-eye"></i></a>
        </div>
        {% endfor %}
      </div>
    </div>
    {% empty %}
    <div class="wti-card mb-3">
      <div class="wti-card-body text-center py-4 text-muted">
        <i class="fas fa-chalkboard-teacher" style="font-size:2.5rem;color:#ddd"></i>
        <p class="mt-2" style="font-size:.85rem">No approved teachers yet</p>
      </div>
    </div>
    {% endfor %}

    <!-- Today's Timetable -->
    <div class="wti-card">
      <div class="wti-card-header">
        <h5><i class="fas fa-calendar-day"></i> Today's Timetable — {{ today }}</h5>
        <a href="{% url 'admin_timetable' %}" class="btn-outline-gold" style="font-size:.78rem">Manage</a>
      </div>
      <div style="padding:0">
        <div class="table-responsive">
          <table class="wti-table">
            <thead><tr><th>Time</th><th>Subject</th><th>Teacher</th><th>Type</th></tr></thead>
            <tbody>
              {% for e in today_timetable %}
              <tr>
                <td style="font-size:.8rem;color:#888;white-space:nowrap">{{ e.start_time|time:"H:i" }} – {{ e.end_time|time:"H:i" }}</td>
                <td>{% if e.is_break %}<span class="text-muted"><i class="fas fa-coffee me-1"></i>{{ e.subject }}</span>{% else %}<strong>{{ e.subject }}</strong>{% endif %}</td>
                <td style="font-size:.82rem">{{ e.teacher.full_name|default:"—" }}</td>
                <td>{% if not e.is_break %}<span class="status-badge {{ e.course_type }}" style="font-size:.7rem">{{ e.get_course_type_display|default:"—" }}</span>{% endif %}</td>
              </tr>
              {% empty %}<tr><td colspan="4" class="text-center text-muted py-3" style="font-size:.85rem">No timetable for today</td></tr>{% endfor %}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <!-- Right: QR + Attendance + Notifications -->
  <div class="col-lg-4">
    <!-- QR Codes -->
    <div class="wti-card mb-3">
      <div class="wti-card-header">
        <h5><i class="fas fa-qrcode"></i> Active QR Codes</h5>
        <a href="{% url 'generate_qr' %}" class="btn-outline-gold" style="font-size:.78rem">Manage</a>
      </div>
      <div style="padding:1rem">
        {% if school_qr %}
        <div style="text-align:center;margin-bottom:1rem;padding-bottom:1rem;border-bottom:1px solid #f0f2f5">
          <div style="font-size:.75rem;font-weight:700;color:#003087;text-transform:uppercase;letter-spacing:1px;margin-bottom:.5rem"><i class="fas fa-school me-1"></i>School Attendance QR</div>
          {% if school_qr.qr_image %}<img src="{{ school_qr.qr_image.url }}" style="max-width:130px;border-radius:8px;border:2px solid #003087">{% endif %}
          <div style="font-size:.72rem;color:#888;margin-top:.4rem">Valid until {{ school_qr.valid_until }}</div>
          <a href="{% url 'qr_detail' school_qr.id %}" style="font-size:.75rem;color:#003087;text-decoration:none;font-weight:600">View Full <i class="fas fa-external-link-alt ms-1"></i></a>
        </div>
        {% endif %}
        {% if lesson_qr %}
        <div style="text-align:center">
          <div style="font-size:.75rem;font-weight:700;color:#28a745;text-transform:uppercase;letter-spacing:1px;margin-bottom:.5rem"><i class="fas fa-book me-1"></i>Lesson QR</div>
          {% if lesson_qr.qr_image %}<img src="{{ lesson_qr.qr_image.url }}" style="max-width:130px;border-radius:8px;border:2px solid #28a745">{% endif %}
          <div style="font-size:.72rem;color:#888;margin-top:.4rem">Valid until {{ lesson_qr.valid_until }}</div>
          <a href="{% url 'qr_detail' lesson_qr.id %}" style="font-size:.75rem;color:#28a745;text-decoration:none;font-weight:600">View Full <i class="fas fa-external-link-alt ms-1"></i></a>
        </div>
        {% endif %}
        {% if not school_qr and not lesson_qr %}
        <div style="text-align:center;padding:1rem;color:#888;font-size:.83rem">
          <i class="fas fa-qrcode" style="font-size:2rem;color:#ddd"></i>
          <p class="mt-2">No QR codes generated yet</p>
          <a href="{% url 'generate_qr' %}" class="btn-gold" style="font-size:.82rem">Generate QR</a>
        </div>
        {% endif %}
      </div>
    </div>

    <!-- Today's Attendance Summary -->
    <div class="wti-card mb-3">
      <div class="wti-card-header">
        <h5><i class="fas fa-clipboard-check"></i> Today's Attendance</h5>
        <a href="{% url 'admin_attendance' %}" class="btn-outline-gold" style="font-size:.78rem">Full View</a>
      </div>
      <div style="padding:0">
        {% for att in today_att %}
        <div style="display:flex;align-items:center;gap:.7rem;padding:.7rem 1.2rem;border-bottom:1px solid #f8f9fa">
          <div style="width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#003087,#0047b3);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:.75rem;flex-shrink:0">{{ att.teacher.user.first_name|first|upper }}{{ att.teacher.user.last_name|first|upper }}</div>
          <div style="flex:1;min-width:0">
            <div style="font-size:.82rem;font-weight:600;color:#001f5c;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ att.teacher.full_name }}</div>
            <small style="color:#888">In: {{ att.check_in_time|default:"—" }}</small>
          </div>
          <div style="display:flex;flex-direction:column;gap:2px;align-items:flex-end">
            {% if att.school_status == 'present' %}<span style="background:rgba(40,167,69,.1);color:#28a745;font-size:.65rem;font-weight:700;padding:2px 7px;border-radius:10px">Present</span>{% else %}<span style="background:rgba(220,53,69,.1);color:#dc3545;font-size:.65rem;font-weight:700;padding:2px 7px;border-radius:10px">Absent</span>{% endif %}
            {% if att.lesson_status == 'done' %}<span style="background:rgba(0,48,135,.1);color:#003087;font-size:.65rem;font-weight:700;padding:2px 7px;border-radius:10px">Lesson Done</span>{% else %}<span style="background:rgba(255,193,7,.15);color:#856404;font-size:.65rem;font-weight:700;padding:2px 7px;border-radius:10px">Lesson Pending</span>{% endif %}
          </div>
        </div>
        {% empty %}<div style="padding:1.5rem;text-align:center;color:#888;font-size:.83rem">No attendance records yet today</div>{% endfor %}
      </div>
    </div>

    <!-- Pending Approvals -->
    {% if pending_teachers %}
    <div class="wti-card mb-3">
      <div class="wti-card-header">
        <h5><i class="fas fa-user-clock"></i> Pending Approvals</h5>
        <span style="background:#ffc107;color:#000;font-size:.7rem;font-weight:700;padding:3px 8px;border-radius:20px">{{ pending_teachers.count }}</span>
      </div>
      <div style="padding:0">
        {% for t in pending_teachers %}
        <div style="display:flex;align-items:center;gap:.7rem;padding:.7rem 1.2rem;border-bottom:1px solid #f8f9fa">
          <div style="width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#f5a623,#e8920a);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:.75rem;flex-shrink:0">{{ t.user.first_name|first|upper }}{{ t.user.last_name|first|upper }}</div>
          <div style="flex:1"><div style="font-size:.82rem;font-weight:600">{{ t.full_name }}</div><small style="color:#888">{{ t.get_course_type_display }}</small></div>
          <a href="{% url 'approve_teacher' t.id %}" style="background:#28a745;color:#fff;border:none;border-radius:8px;padding:4px 10px;font-size:.73rem;font-weight:600;text-decoration:none">Approve</a>
        </div>
        {% endfor %}
      </div>
    </div>
    {% endif %}

    <!-- Recent Notifications -->
    <div class="wti-card">
      <div class="wti-card-header"><h5><i class="fas fa-bell"></i> Recent Activity</h5></div>
      <div style="padding:0;max-height:250px;overflow-y:auto">
        {% for n in recent_notifs %}
        <div style="padding:.8rem 1.2rem;border-bottom:1px solid #f8f9fa">
          <div style="font-size:.82rem;font-weight:600;color:#001f5c">{{ n.title }}</div>
          <div style="font-size:.75rem;color:#888">{{ n.message|truncatechars:55 }}</div>
          <div style="font-size:.68rem;color:#aaa;margin-top:.2rem">{{ n.created_at|timesince }} ago</div>
        </div>
        {% empty %}<div style="padding:1.5rem;text-align:center;color:#888;font-size:.83rem">No recent activity</div>{% endfor %}
      </div>
    </div>
  </div>
</div>
{% endblock %}
"""
with open('templates/admin/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(T)
print('admin dashboard written')
