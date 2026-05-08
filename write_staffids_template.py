T1 = """{% extends 'superadmin/base_superadmin.html' %}
{% block title %}Staff ID Registry — WTI{% endblock %}
{% block page_title %}Teacher Staff ID Registry{% endblock %}
{% block nav_staffids %}active{% endblock %}
{% block content %}
<div class="sa-card">
  <div class="sa-card-header">
    <h5><i class="fas fa-id-card"></i> All Teacher Staff IDs ({{ teachers.count }})</h5>
    <input type="text" id="srch" class="form-control" placeholder="Search..." style="width:200px;font-size:.83rem"
           oninput="document.querySelectorAll('#tbl tbody tr').forEach(r=>r.style.display=r.textContent.toLowerCase().includes(this.value.toLowerCase())?'':'none')">
  </div>
  <div style="overflow-x:auto">
    <table id="tbl" style="width:100%;border-collapse:collapse">
      <thead>
        <tr style="background:#f8f9fa">
          <th style="padding:.8rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#666;border-bottom:2px solid #e8ecf0">#</th>
          <th style="padding:.8rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#666;border-bottom:2px solid #e8ecf0">Staff ID</th>
          <th style="padding:.8rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#666;border-bottom:2px solid #e8ecf0">Full Name</th>
          <th style="padding:.8rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#666;border-bottom:2px solid #e8ecf0">Subject</th>
          <th style="padding:.8rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#666;border-bottom:2px solid #e8ecf0">Type</th>
          <th style="padding:.8rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#666;border-bottom:2px solid #e8ecf0">Status</th>
          <th style="padding:.8rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#666;border-bottom:2px solid #e8ecf0">Joined</th>
        </tr>
      </thead>
      <tbody>
        {% for t in teachers %}
        <tr style="border-bottom:1px solid #f0f2f5">
          <td style="padding:.8rem 1rem;color:#888;font-size:.8rem">{{ forloop.counter }}</td>
          <td style="padding:.8rem 1rem">
            <code style="background:#e8f0fe;color:#003087;padding:3px 10px;border-radius:6px;font-size:.85rem;font-weight:700">{{ t.staff_id }}</code>
          </td>
          <td style="padding:.8rem 1rem">
            <div style="display:flex;align-items:center;gap:.6rem">
              <div style="width:32px;height:32px;border-radius:50%;background:linear-gradient(135deg,#003087,#0047b3);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:.75rem;flex-shrink:0;overflow:hidden">
                {% if t.profile_photo %}<img src="{{ t.profile_photo.url }}" style="width:100%;height:100%;object-fit:cover">{% else %}{{ t.user.first_name|first|upper }}{{ t.user.last_name|first|upper }}{% endif %}
              </div>
              <div>
                <div style="font-weight:600;font-size:.87rem;color:#001f5c">{{ t.full_name }}</div>
                <small style="color:#888">{{ t.user.email }}</small>
              </div>
            </div>
          </td>
          <td style="padding:.8rem 1rem;font-size:.82rem">{{ t.preferred_subject|title }}</td>
          <td style="padding:.8rem 1rem">
            <span style="background:rgba(0,48,135,.1);color:#003087;font-size:.7rem;font-weight:600;padding:3px 8px;border-radius:20px">{{ t.get_course_type_display }}</span>
          </td>
          <td style="padding:.8rem 1rem">
            {% if t.is_approved %}
              <span style="background:rgba(40,167,69,.1);color:#28a745;font-size:.7rem;font-weight:600;padding:3px 8px;border-radius:20px"><i class="fas fa-check-circle me-1"></i>Active</span>
            {% else %}
              <span style="background:rgba(255,193,7,.15);color:#856404;font-size:.7rem;font-weight:600;padding:3px 8px;border-radius:20px"><i class="fas fa-clock me-1"></i>Pending</span>
            {% endif %}
          </td>
          <td style="padding:.8rem 1rem;font-size:.8rem;color:#888">{{ t.date_joined|date:"M d, Y" }}</td>
        </tr>
        {% empty %}
        <tr><td colspan="7" style="text-align:center;padding:2rem;color:#888;font-size:.85rem">No teachers registered yet</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
"""

# Update department_view.html to show Core Subjects by individual subject
T2 = """{% extends 'admin/base_admin.html' %}
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

{% if is_core %}
<!-- Core Subjects: group by individual subject -->
{% regroup teacher_data by teacher.preferred_subject as subject_groups %}
{% for group in subject_groups %}
<div class="wti-card mb-3">
  <div class="wti-card-header">
    <h5><i class="fas fa-book-open"></i> {{ group.grouper|title }}</h5>
    <span style="background:rgba(0,48,135,.1);color:#003087;font-size:.72rem;font-weight:700;padding:3px 10px;border-radius:20px">{{ group.list|length }} Teacher{{ group.list|length|pluralize }}</span>
  </div>
  <div style="overflow-x:auto">
    <table class="wti-table">
      <thead><tr><th>Teacher</th><th>Staff ID</th><th>School</th><th>Check In</th><th>Lesson</th><th>Done At</th><th>Action</th></tr></thead>
      <tbody>
        {% for d in group.list %}
        <tr>
          <td>
            <div style="display:flex;align-items:center;gap:.7rem">
              <div style="width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,#003087,#0047b3);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:.78rem;flex-shrink:0;overflow:hidden">
                {% if d.teacher.profile_photo %}<img src="{{ d.teacher.profile_photo.url }}" style="width:100%;height:100%;object-fit:cover">{% else %}{{ d.teacher.user.first_name|first|upper }}{{ d.teacher.user.last_name|first|upper }}{% endif %}
              </div>
              <div><div style="font-weight:600;font-size:.85rem;color:#001f5c">{{ d.teacher.full_name }}</div><small style="color:#888">{{ d.teacher.user.email }}</small></div>
            </div>
          </td>
          <td><code style="font-size:.8rem;background:#e8f0fe;color:#003087;padding:2px 8px;border-radius:5px">{{ d.teacher.staff_id }}</code></td>
          <td>{% if d.school_status == 'present' %}<span style="background:rgba(40,167,69,.1);color:#28a745;font-size:.7rem;font-weight:700;padding:3px 8px;border-radius:20px"><i class="fas fa-check-circle me-1"></i>Present</span>{% else %}<span style="background:rgba(220,53,69,.1);color:#dc3545;font-size:.7rem;font-weight:700;padding:3px 8px;border-radius:20px"><i class="fas fa-times-circle me-1"></i>Absent</span>{% endif %}</td>
          <td style="font-size:.82rem;color:#666">{{ d.check_in|default:"—" }}</td>
          <td>{% if d.lesson_status == 'done' %}<span style="background:rgba(0,48,135,.1);color:#003087;font-size:.7rem;font-weight:700;padding:3px 8px;border-radius:20px"><i class="fas fa-book me-1"></i>Done</span>{% else %}<span style="background:rgba(255,193,7,.15);color:#856404;font-size:.7rem;font-weight:700;padding:3px 8px;border-radius:20px"><i class="fas fa-clock me-1"></i>Pending</span>{% endif %}</td>
          <td style="font-size:.82rem;color:#666">{{ d.lesson_done|default:"—" }}</td>
          <td><a href="{% url 'teacher_detail' d.teacher.id %}" style="background:#f0f2f5;color:#555;border:none;border-radius:8px;padding:4px 10px;font-size:.73rem;font-weight:600;text-decoration:none"><i class="fas fa-eye"></i></a></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% empty %}
<div class="wti-card"><div class="wti-card-body text-center py-4 text-muted"><i class="fas fa-book" style="font-size:2rem;color:#ddd"></i><p class="mt-2" style="font-size:.85rem">No Core Subject teachers yet</p></div></div>
{% endfor %}

{% else %}
<!-- Departmental: single table -->
<div class="wti-card">
  <div class="wti-card-header">
    <h5><i class="fas fa-building"></i> {{ dept_name }} — Teachers ({{ today }})</h5>
    <a href="{% url 'admin_dashboard' %}" style="font-size:.8rem;color:#003087;text-decoration:none"><i class="fas fa-arrow-left me-1"></i> Back</a>
  </div>
  <div style="overflow-x:auto">
    <table class="wti-table">
      <thead><tr><th>Teacher</th><th>Staff ID</th><th>Subject</th><th>School</th><th>Check In</th><th>Lesson</th><th>Done At</th><th>Action</th></tr></thead>
      <tbody>
        {% for d in teacher_data %}
        <tr>
          <td>
            <div style="display:flex;align-items:center;gap:.7rem">
              <div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#003087,#0047b3);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:.8rem;flex-shrink:0;overflow:hidden">
                {% if d.teacher.profile_photo %}<img src="{{ d.teacher.profile_photo.url }}" style="width:100%;height:100%;object-fit:cover">{% else %}{{ d.teacher.user.first_name|first|upper }}{{ d.teacher.user.last_name|first|upper }}{% endif %}
              </div>
              <div><div style="font-weight:600;font-size:.87rem;color:#001f5c">{{ d.teacher.full_name }}</div><small style="color:#888">{{ d.teacher.user.email }}</small></div>
            </div>
          </td>
          <td><code style="font-size:.8rem;background:#e8f0fe;color:#003087;padding:2px 8px;border-radius:5px">{{ d.teacher.staff_id }}</code></td>
          <td style="font-size:.82rem">{{ d.teacher.preferred_subject|title }}</td>
          <td>{% if d.school_status == 'present' %}<span style="background:rgba(40,167,69,.1);color:#28a745;font-size:.7rem;font-weight:700;padding:3px 8px;border-radius:20px"><i class="fas fa-check-circle me-1"></i>Present</span>{% else %}<span style="background:rgba(220,53,69,.1);color:#dc3545;font-size:.7rem;font-weight:700;padding:3px 8px;border-radius:20px"><i class="fas fa-times-circle me-1"></i>Absent</span>{% endif %}</td>
          <td style="font-size:.82rem;color:#666">{{ d.check_in|default:"—" }}</td>
          <td>{% if d.lesson_status == 'done' %}<span style="background:rgba(0,48,135,.1);color:#003087;font-size:.7rem;font-weight:700;padding:3px 8px;border-radius:20px"><i class="fas fa-book me-1"></i>Done</span>{% else %}<span style="background:rgba(255,193,7,.15);color:#856404;font-size:.7rem;font-weight:700;padding:3px 8px;border-radius:20px"><i class="fas fa-clock me-1"></i>Pending</span>{% endif %}</td>
          <td style="font-size:.82rem;color:#666">{{ d.lesson_done|default:"—" }}</td>
          <td><a href="{% url 'teacher_detail' d.teacher.id %}" style="background:#f0f2f5;color:#555;border:none;border-radius:8px;padding:4px 10px;font-size:.73rem;font-weight:600;text-decoration:none"><i class="fas fa-eye"></i></a></td>
        </tr>
        {% empty %}
        <tr><td colspan="8" style="text-align:center;padding:2rem;color:#888;font-size:.85rem">No teachers in this department</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endif %}
{% endblock %}
"""

with open('templates/superadmin/staff_ids.html', 'w', encoding='utf-8') as f:
    f.write(T1)
with open('templates/admin/department_view.html', 'w', encoding='utf-8') as f:
    f.write(T2)
print('staff_ids.html and department_view.html written')
