import os

# ── Admin Department View ─────────────────────────────────────────────────────
with open('templates/admin/department_view.html', 'w', encoding='utf-8') as f:
    f.write("""{% extends 'admin/base_admin.html' %}
{% load static %}
{% block title %}{{ dept_name }} — WTI Admin{% endblock %}
{% block page_title %}{{ dept_name }}{% endblock %}
{% block nav_teachers %}active{% endblock %}

{% block content %}
<!-- Stats -->
<div class="row g-3 mb-4">
  <div class="col-4">
    <div class="stat-card"><div class="stat-icon gold"><i class="fas fa-chalkboard-teacher"></i></div>
    <div class="stat-info"><h3>{{ total }}</h3><p>Total Teachers</p></div></div>
  </div>
  <div class="col-4">
    <div class="stat-card"><div class="stat-icon green"><i class="fas fa-user-check"></i></div>
    <div class="stat-info"><h3>{{ present }}</h3><p>Present Today</p></div></div>
  </div>
  <div class="col-4">
    <div class="stat-card"><div class="stat-icon blue"><i class="fas fa-book"></i></div>
    <div class="stat-info"><h3>{{ lesson_done }}</h3><p>Lesson Done</p></div></div>
  </div>
</div>

<div class="wti-card">
  <div class="wti-card-header">
    <h5><i class="fas fa-building"></i> {{ dept_name }} — Teachers ({{ today }})</h5>
    <a href="{% url 'admin_dashboard' %}" style="font-size:.8rem;color:#003087;text-decoration:none"><i class="fas fa-arrow-left me-1"></i> Back</a>
  </div>
  <div style="overflow-x:auto">
    <table class="wti-table">
      <thead>
        <tr>
          <th>Teacher</th>
          <th>Staff ID</th>
          <th>Subject</th>
          <th>School Status</th>
          <th>Check In</th>
          <th>Lesson Status</th>
          <th>Lesson Done</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        {% for d in teacher_data %}
        <tr>
          <td>
            <div style="display:flex;align-items:center;gap:.7rem">
              <div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#003087,#0047b3);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:.8rem;flex-shrink:0;overflow:hidden">
                {% if d.teacher.profile_photo %}<img src="{{ d.teacher.profile_photo.url }}" style="width:100%;height:100%;object-fit:cover">{% else %}{{ d.teacher.user.first_name|first|upper }}{{ d.teacher.user.last_name|first|upper }}{% endif %}
              </div>
              <div>
                <div style="font-weight:600;font-size:.87rem;color:#001f5c">{{ d.teacher.full_name }}</div>
                <small style="color:#888">{{ d.teacher.user.email }}</small>
              </div>
            </div>
          </td>
          <td><code style="font-size:.8rem">{{ d.teacher.staff_id }}</code></td>
          <td style="font-size:.82rem">{{ d.teacher.preferred_subject|title }}</td>
          <td>
            {% if d.school_status == 'present' %}
              <span style="background:rgba(40,167,69,.1);color:#28a745;font-size:.72rem;font-weight:700;padding:3px 10px;border-radius:20px"><i class="fas fa-check-circle me-1"></i>Present</span>
            {% else %}
              <span style="background:rgba(220,53,69,.1);color:#dc3545;font-size:.72rem;font-weight:700;padding:3px 10px;border-radius:20px"><i class="fas fa-times-circle me-1"></i>Absent</span>
            {% endif %}
          </td>
          <td style="font-size:.82rem;color:#666">{{ d.check_in|default:"—" }}</td>
          <td>
            {% if d.lesson_status == 'done' %}
              <span style="background:rgba(0,48,135,.1);color:#003087;font-size:.72rem;font-weight:700;padding:3px 10px;border-radius:20px"><i class="fas fa-book me-1"></i>Done</span>
            {% else %}
              <span style="background:rgba(255,193,7,.15);color:#856404;font-size:.72rem;font-weight:700;padding:3px 10px;border-radius:20px"><i class="fas fa-clock me-1"></i>Pending</span>
            {% endif %}
          </td>
          <td style="font-size:.82rem;color:#666">{{ d.lesson_done|default:"—" }}</td>
          <td>
            <a href="{% url 'teacher_detail' d.teacher.id %}" style="background:#f0f2f5;color:#555;border:none;border-radius:8px;padding:4px 10px;font-size:.73rem;font-weight:600;text-decoration:none"><i class="fas fa-eye me-1"></i>Profile</a>
          </td>
        </tr>
        {% empty %}
        <tr><td colspan="8" style="text-align:center;padding:2rem;color:#888;font-size:.85rem">No teachers in this department</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
""")

# ── Admin QR View Only ────────────────────────────────────────────────────────
with open('templates/admin/qr_view.html', 'w', encoding='utf-8') as f:
    f.write("""{% extends 'admin/base_admin.html' %}
{% load static %}
{% block title %}QR Codes — WTI Admin{% endblock %}
{% block page_title %}QR Codes{% endblock %}
{% block nav_qr %}active{% endblock %}

{% block content %}
<div class="alert alert-info" style="font-size:.83rem;border-radius:12px;border-left:4px solid #003087">
  <i class="fas fa-info-circle me-2"></i>
  QR codes are generated by the <strong>Super Admin</strong>. Print and paste them on the classroom wall for teachers to scan.
</div>

<div class="row g-3">
  <!-- School Attendance QRs -->
  <div class="col-lg-6">
    <div class="wti-card">
      <div class="wti-card-header">
        <h5><i class="fas fa-school" style="color:#003087"></i> School Attendance QR</h5>
        <span style="background:rgba(0,48,135,.1);color:#003087;font-size:.72rem;font-weight:700;padding:3px 10px;border-radius:20px">{{ school_qrs.count }}</span>
      </div>
      <div style="padding:0">
        {% for qr in school_qrs %}
        <div style="display:flex;align-items:center;gap:.8rem;padding:.9rem 1.2rem;border-bottom:1px solid #f0f2f5">
          {% if qr.qr_image %}<img src="{{ qr.qr_image.url }}" style="width:55px;height:55px;border-radius:8px;border:2px solid #003087;flex-shrink:0">{% endif %}
          <div style="flex:1">
            <div style="font-weight:600;font-size:.87rem;color:#001f5c">{{ qr.label }}</div>
            <small style="color:#888">Valid: {{ qr.valid_from }} → {{ qr.valid_until }}</small>
          </div>
          {% if qr.is_valid_today %}<span style="background:rgba(40,167,69,.1);color:#28a745;font-size:.7rem;font-weight:700;padding:3px 8px;border-radius:20px">Active</span>
          {% else %}<span style="background:rgba(220,53,69,.1);color:#dc3545;font-size:.7rem;font-weight:700;padding:3px 8px;border-radius:20px">Expired</span>{% endif %}
          <a href="{% url 'qr_detail' qr.id %}" style="background:#003087;color:#fff;border:none;border-radius:8px;padding:4px 10px;font-size:.73rem;font-weight:600;text-decoration:none"><i class="fas fa-eye"></i></a>
        </div>
        {% empty %}
        <div style="padding:2rem;text-align:center;color:#888;font-size:.83rem">
          <i class="fas fa-qrcode" style="font-size:2rem;color:#ddd"></i>
          <p class="mt-2">No school QR codes yet. Ask Super Admin to generate one.</p>
        </div>
        {% endfor %}
      </div>
    </div>
  </div>

  <!-- Lesson QRs -->
  <div class="col-lg-6">
    <div class="wti-card">
      <div class="wti-card-header">
        <h5><i class="fas fa-book" style="color:#28a745"></i> Lesson QR</h5>
        <span style="background:rgba(40,167,69,.1);color:#28a745;font-size:.72rem;font-weight:700;padding:3px 10px;border-radius:20px">{{ lesson_qrs.count }}</span>
      </div>
      <div style="padding:0">
        {% for qr in lesson_qrs %}
        <div style="display:flex;align-items:center;gap:.8rem;padding:.9rem 1.2rem;border-bottom:1px solid #f0f2f5">
          {% if qr.qr_image %}<img src="{{ qr.qr_image.url }}" style="width:55px;height:55px;border-radius:8px;border:2px solid #28a745;flex-shrink:0">{% endif %}
          <div style="flex:1">
            <div style="font-weight:600;font-size:.87rem;color:#001f5c">{{ qr.label }}</div>
            <small style="color:#888">Valid: {{ qr.valid_from }} → {{ qr.valid_until }}</small>
          </div>
          {% if qr.is_valid_today %}<span style="background:rgba(40,167,69,.1);color:#28a745;font-size:.7rem;font-weight:700;padding:3px 8px;border-radius:20px">Active</span>
          {% else %}<span style="background:rgba(220,53,69,.1);color:#dc3545;font-size:.7rem;font-weight:700;padding:3px 8px;border-radius:20px">Expired</span>{% endif %}
          <a href="{% url 'qr_detail' qr.id %}" style="background:#28a745;color:#fff;border:none;border-radius:8px;padding:4px 10px;font-size:.73rem;font-weight:600;text-decoration:none"><i class="fas fa-eye"></i></a>
        </div>
        {% empty %}
        <div style="padding:2rem;text-align:center;color:#888;font-size:.83rem">
          <i class="fas fa-book" style="font-size:2rem;color:#ddd"></i>
          <p class="mt-2">No lesson QR codes yet. Ask Super Admin to generate one.</p>
        </div>
        {% endfor %}
      </div>
    </div>
  </div>
</div>
{% endblock %}
""")

print('department_view.html and qr_view.html written')
