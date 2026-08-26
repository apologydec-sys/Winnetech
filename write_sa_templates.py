import os

# ── Superadmin Dashboard ──────────────────────────────────────────────────────
with open('templates/superadmin/dashboard.html', 'w', encoding='utf-8') as f:
    f.write("""{% extends 'superadmin/base_superadmin.html' %}
{% block title %}Super Admin Dashboard — WTI{% endblock %}
{% block page_title %}Dashboard{% endblock %}
{% block nav_dash %}active{% endblock %}
{% block content %}
<div class="row g-3 mb-4">
  <div class="col-6 col-md-3"><div class="sa-stat"><div class="sa-stat-icon blue"><i class="fas fa-user-shield"></i></div><div><h3>{{ total_admins }}</h3><p>Total Admins</p></div></div></div>
  <div class="col-6 col-md-3"><div class="sa-stat"><div class="sa-stat-icon orange"><i class="fas fa-chalkboard-teacher"></i></div><div><h3>{{ total_teachers }}</h3><p>Total Teachers</p></div></div></div>
  <div class="col-6 col-md-3"><div class="sa-stat"><div class="sa-stat-icon red"><i class="fas fa-clock"></i></div><div><h3>{{ pending_count }}</h3><p>Pending Approval</p></div></div></div>
  <div class="col-6 col-md-3"><div class="sa-stat"><div class="sa-stat-icon green"><i class="fas fa-user-check"></i></div><div><h3>{{ present_today }}</h3><p>Present Today</p></div></div></div>
</div>
<div class="row g-3">
  <div class="col-lg-6">
    <div class="sa-card">
      <div class="sa-card-header"><h5><i class="fas fa-user-shield"></i> Admin Accounts</h5><a href="{% url 'superadmin_admins' %}" style="font-size:.8rem;color:#003087;text-decoration:none">View All</a></div>
      <div style="padding:0">
        {% for a in admins %}
        <div style="display:flex;align-items:center;gap:.8rem;padding:.8rem 1.2rem;border-bottom:1px solid #f0f2f5;">
          <div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#003087,#0047b3);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:.8rem;flex-shrink:0;">{{ a.first_name|first|upper }}{{ a.last_name|first|upper }}</div>
          <div style="flex:1"><div style="font-size:.85rem;font-weight:600;color:#001f5c">{{ a.get_full_name|default:a.username }}</div><small style="color:#888">{{ a.username }}</small></div>
          {% if a.admin_profile.role == 'superadmin' %}<span style="background:rgba(0,48,135,.1);color:#003087;font-size:.7rem;font-weight:700;padding:3px 10px;border-radius:20px"><i class="fas fa-crown me-1"></i>Super</span>
          {% else %}<span style="background:rgba(40,167,69,.1);color:#28a745;font-size:.7rem;font-weight:700;padding:3px 10px;border-radius:20px">Admin</span>{% endif %}
        </div>
        {% empty %}<div style="padding:1.5rem;text-align:center;color:#888;font-size:.85rem">No admins</div>{% endfor %}
      </div>
    </div>
  </div>
  <div class="col-lg-6">
    <div class="sa-card">
      <div class="sa-card-header"><h5><i class="fas fa-clock"></i> Pending Teacher Approvals</h5><a href="{% url 'superadmin_teachers' %}" style="font-size:.8rem;color:#003087;text-decoration:none">View All</a></div>
      <div style="padding:0">
        {% for t in pending %}
        <div style="display:flex;align-items:center;gap:.8rem;padding:.8rem 1.2rem;border-bottom:1px solid #f0f2f5;">
          <div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#f5a623,#e8920a);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:.8rem;flex-shrink:0;">{{ t.user.first_name|first|upper }}{{ t.user.last_name|first|upper }}</div>
          <div style="flex:1"><div style="font-size:.85rem;font-weight:600;color:#001f5c">{{ t.full_name }}</div><small style="color:#888">{{ t.get_course_type_display }}</small></div>
          <a href="{% url 'superadmin_approve_teacher' t.id %}" style="background:#28a745;color:#fff;border:none;border-radius:8px;padding:4px 12px;font-size:.75rem;font-weight:600;text-decoration:none">Approve</a>
        </div>
        {% empty %}<div style="padding:1.5rem;text-align:center;color:#888;font-size:.85rem"><i class="fas fa-check-circle" style="color:#28a745;font-size:1.5rem"></i><p class="mt-2">All teachers approved!</p></div>{% endfor %}
      </div>
    </div>
  </div>
</div>
{% endblock %}
""")

# ── Superadmin Admins ─────────────────────────────────────────────────────────
with open('templates/superadmin/admins.html', 'w', encoding='utf-8') as f:
    f.write("""{% extends 'superadmin/base_superadmin.html' %}
{% block title %}Manage Admins — WTI{% endblock %}
{% block page_title %}Manage Admin Accounts{% endblock %}
{% block nav_admins %}active{% endblock %}
{% block content %}
<div class="sa-card">
  <div class="sa-card-header">
    <h5><i class="fas fa-user-shield"></i> All Admin Accounts ({{ admins.count }})</h5>
    <a href="{% url 'superadmin_create_admin' %}" style="background:linear-gradient(135deg,#003087,#0047b3);color:#fff;border:none;border-radius:10px;padding:.5rem 1.2rem;font-size:.83rem;font-weight:700;text-decoration:none"><i class="fas fa-plus me-1"></i> Create Admin</a>
  </div>
  <div style="overflow-x:auto">
    <table style="width:100%;border-collapse:collapse">
      <thead><tr style="background:#f8f9fa">
        <th style="padding:.8rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#666;border-bottom:2px solid #e8ecf0">Admin</th>
        <th style="padding:.8rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#666;border-bottom:2px solid #e8ecf0">Username</th>
        <th style="padding:.8rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#666;border-bottom:2px solid #e8ecf0">Email</th>
        <th style="padding:.8rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#666;border-bottom:2px solid #e8ecf0">Role</th>
        <th style="padding:.8rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#666;border-bottom:2px solid #e8ecf0">Action</th>
      </tr></thead>
      <tbody>
        {% for a in admins %}
        <tr style="border-bottom:1px solid #f0f2f5">
          <td style="padding:.9rem 1rem">
            <div style="display:flex;align-items:center;gap:.7rem">
              <div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#003087,#0047b3);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:.8rem;flex-shrink:0">{{ a.first_name|first|upper }}{{ a.last_name|first|upper }}</div>
              <div><div style="font-weight:600;font-size:.87rem">{{ a.get_full_name|default:a.username }}</div></div>
            </div>
          </td>
          <td style="padding:.9rem 1rem"><code style="font-size:.82rem">{{ a.username }}</code></td>
          <td style="padding:.9rem 1rem;font-size:.82rem;color:#666">{{ a.email|default:"—" }}</td>
          <td style="padding:.9rem 1rem">
            {% if a.admin_profile.role == 'superadmin' %}
              <span style="background:rgba(0,48,135,.1);color:#003087;font-size:.72rem;font-weight:700;padding:4px 12px;border-radius:20px"><i class="fas fa-crown me-1"></i>Super Admin</span>
            {% else %}
              <span style="background:rgba(40,167,69,.1);color:#28a745;font-size:.72rem;font-weight:700;padding:4px 12px;border-radius:20px"><i class="fas fa-user-shield me-1"></i>Admin</span>
            {% endif %}
          </td>
          <td style="padding:.9rem 1rem">
            {% if a != request.user and a.admin_profile.role != 'superadmin' %}
            <a href="{% url 'superadmin_delete_admin' a.id %}" style="background:#dc3545;color:#fff;border:none;border-radius:8px;padding:4px 12px;font-size:.75rem;font-weight:600;text-decoration:none"><i class="fas fa-trash me-1"></i>Delete</a>
            {% else %}<span style="color:#ccc;font-size:.78rem">Protected</span>{% endif %}
          </td>
        </tr>
        {% empty %}<tr><td colspan="5" style="text-align:center;padding:2rem;color:#888;font-size:.85rem">No admins found</td></tr>{% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
""")

# ── Superadmin Create Admin ───────────────────────────────────────────────────
with open('templates/superadmin/create_admin.html', 'w', encoding='utf-8') as f:
    f.write("""{% extends 'superadmin/base_superadmin.html' %}
{% block title %}Create Admin — WTI{% endblock %}
{% block page_title %}Create New Admin{% endblock %}
{% block nav_create %}active{% endblock %}
{% block content %}
<div class="row justify-content-center">
<div class="col-lg-6">
  <div class="sa-card">
    <div class="sa-card-header" style="background:linear-gradient(135deg,#003087,#0047b3)">
      <h5 style="color:#fff"><i class="fas fa-user-plus me-2"></i>Create Admin Account</h5>
    </div>
    <div style="padding:1.5rem">
      {% if error %}<div class="alert alert-danger" style="font-size:.83rem;border-radius:10px"><i class="fas fa-exclamation-circle me-2"></i>{{ error }}</div>{% endif %}
      <form method="post" novalidate>
        {% csrf_token %}
        <div class="row g-3">
          <div class="col-md-6"><label class="form-label">First Name</label><input type="text" name="first_name" class="form-control" placeholder="First Name"></div>
          <div class="col-md-6"><label class="form-label">Last Name</label><input type="text" name="last_name" class="form-control" placeholder="Last Name"></div>
          <div class="col-12"><label class="form-label">Email</label><input type="email" name="email" class="form-control" placeholder="Email Address"></div>
          <div class="col-12"><label class="form-label">Username *</label><input type="text" name="username" class="form-control" placeholder="Choose a username" required></div>
          <div class="col-12"><label class="form-label">Password *</label><input type="password" name="password" class="form-control" placeholder="Set a password" required></div>
          <div class="col-12"><div class="alert alert-info" style="font-size:.8rem;border-radius:10px;margin:0"><i class="fas fa-info-circle me-1"></i>This admin can approve teachers and view teacher lists by department.</div></div>
        </div>
        <div style="display:flex;gap:.8rem;margin-top:1.2rem">
          <a href="{% url 'superadmin_admins' %}" class="btn btn-outline-secondary rounded-3 px-4">Cancel</a>
          <button type="submit" style="background:linear-gradient(135deg,#003087,#0047b3);color:#fff;border:none;border-radius:10px;padding:.6rem 1.5rem;font-weight:700;font-size:.88rem;cursor:pointer"><i class="fas fa-user-plus me-2"></i>Create Admin</button>
        </div>
      </form>
    </div>
  </div>
</div>
</div>
{% endblock %}
""")

# ── Superadmin Teachers ───────────────────────────────────────────────────────
with open('templates/superadmin/teachers.html', 'w', encoding='utf-8') as f:
    f.write("""{% extends 'superadmin/base_superadmin.html' %}
{% block title %}All Teachers — WTI{% endblock %}
{% block page_title %}All Teachers{% endblock %}
{% block nav_teachers %}active{% endblock %}
{% block content %}
<div class="sa-card">
  <div class="sa-card-header">
    <h5><i class="fas fa-chalkboard-teacher"></i> All Teachers ({{ teachers.count }})</h5>
    <input type="text" id="srch" class="form-control" placeholder="Search..." style="width:200px;font-size:.83rem" oninput="document.querySelectorAll('#tbl tbody tr').forEach(r=>r.style.display=r.textContent.toLowerCase().includes(this.value.toLowerCase())?'':'none')">
  </div>
  <div style="overflow-x:auto">
    <table id="tbl" style="width:100%;border-collapse:collapse">
      <thead><tr style="background:#f8f9fa">
        <th style="padding:.8rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#666;border-bottom:2px solid #e8ecf0">Teacher</th>
        <th style="padding:.8rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#666;border-bottom:2px solid #e8ecf0">Staff ID</th>
        <th style="padding:.8rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#666;border-bottom:2px solid #e8ecf0">Type</th>
        <th style="padding:.8rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#666;border-bottom:2px solid #e8ecf0">Status</th>
        <th style="padding:.8rem 1rem;font-size:.72rem;font-weight:700;text-transform:uppercase;color:#666;border-bottom:2px solid #e8ecf0">Actions</th>
      </tr></thead>
      <tbody>
        {% for t in teachers %}
        <tr style="border-bottom:1px solid #f0f2f5">
          <td style="padding:.9rem 1rem">
            <div style="display:flex;align-items:center;gap:.7rem">
              <div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#f5a623,#e8920a);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:.8rem;flex-shrink:0;overflow:hidden">
                {% if t.profile_photo %}<img src="{{ t.profile_photo.url }}" style="width:100%;height:100%;object-fit:cover">{% else %}{{ t.user.first_name|first|upper }}{{ t.user.last_name|first|upper }}{% endif %}
              </div>
              <div><div style="font-weight:600;font-size:.87rem">{{ t.full_name }}</div><small style="color:#888">{{ t.user.email }}</small></div>
            </div>
          </td>
          <td style="padding:.9rem 1rem"><code style="font-size:.82rem">{{ t.staff_id }}</code></td>
          <td style="padding:.9rem 1rem"><span style="background:rgba(0,48,135,.1);color:#003087;font-size:.72rem;font-weight:600;padding:3px 10px;border-radius:20px">{{ t.get_course_type_display }}</span></td>
          <td style="padding:.9rem 1rem">
            {% if t.is_approved %}<span style="background:rgba(40,167,69,.1);color:#28a745;font-size:.72rem;font-weight:600;padding:3px 10px;border-radius:20px"><i class="fas fa-check-circle me-1"></i>Approved</span>
            {% else %}<span style="background:rgba(255,193,7,.15);color:#856404;font-size:.72rem;font-weight:600;padding:3px 10px;border-radius:20px"><i class="fas fa-clock me-1"></i>Pending</span>{% endif %}
          </td>
          <td style="padding:.9rem 1rem">
            <div style="display:flex;gap:.4rem">
              {% if not t.is_approved %}<a href="{% url 'superadmin_approve_teacher' t.id %}" style="background:#28a745;color:#fff;border:none;border-radius:8px;padding:4px 10px;font-size:.73rem;font-weight:600;text-decoration:none"><i class="fas fa-check"></i></a>{% endif %}
              <a href="{% url 'superadmin_delete_teacher' t.id %}" style="background:#dc3545;color:#fff;border:none;border-radius:8px;padding:4px 10px;font-size:.73rem;font-weight:600;text-decoration:none"><i class="fas fa-trash"></i></a>
            </div>
          </td>
        </tr>
        {% empty %}<tr><td colspan="5" style="text-align:center;padding:2rem;color:#888;font-size:.85rem">No teachers registered</td></tr>{% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
""")

# ── Superadmin Confirm Delete Admin ──────────────────────────────────────────
with open('templates/superadmin/confirm_delete_admin.html', 'w', encoding='utf-8') as f:
    f.write("""{% extends 'superadmin/base_superadmin.html' %}
{% block title %}Delete Admin — WTI{% endblock %}
{% block page_title %}Delete Admin{% endblock %}
{% block content %}
<div class="row justify-content-center"><div class="col-lg-5">
  <div class="sa-card">
    <div class="sa-card-header" style="background:linear-gradient(135deg,#dc3545,#c82333)"><h5 style="color:#fff"><i class="fas fa-exclamation-triangle me-2"></i>Confirm Delete Admin</h5></div>
    <div style="padding:2rem;text-align:center">
      <div style="width:70px;height:70px;background:rgba(220,53,69,.1);border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 1.2rem"><i class="fas fa-user-times" style="font-size:1.8rem;color:#dc3545"></i></div>
      <h5 style="font-weight:700;color:#001f5c">Delete {{ admin_user.get_full_name|default:admin_user.username }}?</h5>
      <p style="color:#888;font-size:.85rem">Username: <strong>{{ admin_user.username }}</strong></p>
      <div class="alert alert-danger" style="font-size:.82rem;border-radius:10px;text-align:left"><i class="fas fa-exclamation-circle me-2"></i>This admin will permanently lose access to the system.</div>
      <div style="display:flex;gap:.8rem;justify-content:center;margin-top:1rem">
        <a href="{% url 'superadmin_admins' %}" class="btn btn-outline-secondary rounded-3 px-4"><i class="fas fa-arrow-left me-2"></i>Cancel</a>
        <form method="post" style="display:inline">{% csrf_token %}<button type="submit" class="btn btn-danger rounded-3 px-4" style="font-weight:700"><i class="fas fa-trash me-2"></i>Yes, Delete</button></form>
      </div>
    </div>
  </div>
</div></div>
{% endblock %}
""")

# ── Superadmin Confirm Delete Teacher ────────────────────────────────────────
with open('templates/superadmin/confirm_delete_teacher.html', 'w', encoding='utf-8') as f:
    f.write("""{% extends 'superadmin/base_superadmin.html' %}
{% block title %}Delete Teacher — WTI{% endblock %}
{% block page_title %}Delete Teacher{% endblock %}
{% block content %}
<div class="row justify-content-center"><div class="col-lg-5">
  <div class="sa-card">
    <div class="sa-card-header" style="background:linear-gradient(135deg,#dc3545,#c82333)"><h5 style="color:#fff"><i class="fas fa-exclamation-triangle me-2"></i>Confirm Delete Teacher</h5></div>
    <div style="padding:2rem;text-align:center">
      <div style="width:70px;height:70px;background:rgba(220,53,69,.1);border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 1.2rem"><i class="fas fa-trash" style="font-size:1.8rem;color:#dc3545"></i></div>
      <h5 style="font-weight:700;color:#001f5c">Delete {{ teacher.full_name }}?</h5>
      <p style="color:#888;font-size:.85rem">Staff ID: <strong>{{ teacher.staff_id }}</strong></p>
      <div class="alert alert-danger" style="font-size:.82rem;border-radius:10px;text-align:left"><i class="fas fa-exclamation-circle me-2"></i>This will permanently delete the teacher and all their records. <strong>Cannot be undone.</strong></div>
      <div style="display:flex;gap:.8rem;justify-content:center;margin-top:1rem">
        <a href="{% url 'superadmin_teachers' %}" class="btn btn-outline-secondary rounded-3 px-4"><i class="fas fa-arrow-left me-2"></i>Cancel</a>
        <form method="post" style="display:inline">{% csrf_token %}<button type="submit" class="btn btn-danger rounded-3 px-4" style="font-weight:700"><i class="fas fa-trash me-2"></i>Yes, Delete</button></form>
      </div>
    </div>
  </div>
</div></div>
{% endblock %}
""")

print('All superadmin templates written')
