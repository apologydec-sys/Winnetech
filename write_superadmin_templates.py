import os

os.makedirs('templates/superadmin', exist_ok=True)

# ── Super Admin Dashboard ──────────────────────────────────────────────────────
dashboard = r"""{% extends 'admin/base_admin.html' %}
{% load static %}
{% block title %}Super Admin — WTI{% endblock %}
{% block page_title %}Super Admin Control Panel{% endblock %}

{% block content %}
<div class="row g-3 mb-4">
  <div class="col-6 col-md-3">
    <div class="stat-card">
      <div class="stat-icon blue"><i class="fas fa-user-shield"></i></div>
      <div class="stat-info"><h3>{{ total_admins }}</h3><p>Total Admins</p></div>
    </div>
  </div>
  <div class="col-6 col-md-3">
    <div class="stat-card">
      <div class="stat-icon gold"><i class="fas fa-chalkboard-teacher"></i></div>
      <div class="stat-info"><h3>{{ total_teachers }}</h3><p>Total Teachers</p></div>
    </div>
  </div>
</div>

<div class="wti-card">
  <div class="wti-card-header">
    <h5><i class="fas fa-user-shield"></i> Admin Accounts</h5>
    <a href="{% url 'superadmin_create_admin' %}" class="btn-gold px-3 py-2 rounded-3" style="font-size:.85rem">
      <i class="fas fa-plus me-1"></i> Create Admin
    </a>
  </div>
  <div class="wti-card-body p-0">
    <div class="table-responsive">
      <table class="wti-table">
        <thead>
          <tr><th>Admin</th><th>Username</th><th>Email</th><th>Role</th><th>Actions</th></tr>
        </thead>
        <tbody>
          {% for a in admins %}
          <tr>
            <td>
              <div class="d-flex align-items-center gap-2">
                <div class="teacher-avatar" style="background:linear-gradient(135deg,#003087,#0047b3)">
                  {{ a.first_name|first|upper }}{{ a.last_name|first|upper }}
                </div>
                <div>
                  <div style="font-weight:600;font-size:.88rem">{{ a.get_full_name|default:a.username }}</div>
                  <small class="text-muted">{{ a.email }}</small>
                </div>
              </div>
            </td>
            <td><code>{{ a.username }}</code></td>
            <td style="font-size:.82rem">{{ a.email }}</td>
            <td>
              {% try %}{% if a.admin_profile.role == 'superadmin' %}
                <span class="status-badge" style="background:rgba(0,48,135,.12);color:#003087"><i class="fas fa-crown me-1"></i>Super Admin</span>
              {% else %}
                <span class="status-badge approved"><i class="fas fa-user-shield me-1"></i>Admin</span>
              {% endif %}{% except %}
                <span class="status-badge approved">Admin</span>
              {% endtry %}
            </td>
            <td>
              {% if a != request.user %}
              <a href="{% url 'superadmin_delete_admin' a.id %}" class="btn btn-sm btn-danger rounded-pill" style="font-size:.75rem">
                <i class="fas fa-trash me-1"></i>Delete
              </a>
              {% else %}
              <span class="text-muted" style="font-size:.78rem">You</span>
              {% endif %}
            </td>
          </tr>
          {% empty %}
          <tr><td colspan="5" class="text-center text-muted py-4">No admins found</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
{% endblock %}
"""

# ── Create Admin ───────────────────────────────────────────────────────────────
create_admin = r"""{% extends 'admin/base_admin.html' %}
{% load static %}
{% block title %}Create Admin — WTI{% endblock %}
{% block page_title %}Create New Admin{% endblock %}

{% block content %}
<div class="row justify-content-center">
<div class="col-lg-6">
  <div class="wti-card">
    <div class="wti-card-header" style="background:linear-gradient(135deg,#003087,#0047b3)">
      <h5 style="color:#fff"><i class="fas fa-user-plus me-2"></i>Create Admin Account</h5>
    </div>
    <div class="wti-card-body">
      {% if error %}
      <div class="alert alert-danger" style="font-size:.83rem;border-radius:10px">
        <i class="fas fa-exclamation-circle me-2"></i>{{ error }}
      </div>
      {% endif %}
      <form method="post" novalidate>
        {% csrf_token %}
        <div class="row g-3">
          <div class="col-md-6">
            <label class="form-label">First Name</label>
            <input type="text" name="first_name" class="form-control" placeholder="First Name">
          </div>
          <div class="col-md-6">
            <label class="form-label">Last Name</label>
            <input type="text" name="last_name" class="form-control" placeholder="Last Name">
          </div>
          <div class="col-12">
            <label class="form-label">Email</label>
            <input type="email" name="email" class="form-control" placeholder="Email Address">
          </div>
          <div class="col-12">
            <label class="form-label">Username *</label>
            <input type="text" name="username" class="form-control" placeholder="Choose a username" required>
          </div>
          <div class="col-12">
            <label class="form-label">Password *</label>
            <input type="password" name="password" class="form-control" placeholder="Set a password" required>
          </div>
          <div class="col-12">
            <div class="alert alert-info" style="font-size:.8rem;border-radius:10px;margin:0">
              <i class="fas fa-info-circle me-1"></i>
              This admin will have access to manage teachers, attendance, timetables and notifications.
            </div>
          </div>
        </div>
        <div class="d-flex gap-2 mt-4">
          <a href="{% url 'superadmin_dashboard' %}" class="btn btn-outline-secondary rounded-3 px-4">Cancel</a>
          <button type="submit" class="btn-gold rounded-3 px-4 py-2">
            <i class="fas fa-user-plus me-2"></i>Create Admin
          </button>
        </div>
      </form>
    </div>
  </div>
</div>
</div>
{% endblock %}
"""

# ── Confirm Delete Admin ───────────────────────────────────────────────────────
confirm_delete = r"""{% extends 'admin/base_admin.html' %}
{% load static %}
{% block title %}Delete Admin — WTI{% endblock %}
{% block page_title %}Delete Admin{% endblock %}

{% block content %}
<div class="row justify-content-center">
<div class="col-lg-5">
  <div class="wti-card">
    <div class="wti-card-header" style="background:linear-gradient(135deg,#dc3545,#c82333)">
      <h5 style="color:#fff"><i class="fas fa-exclamation-triangle me-2"></i>Confirm Delete Admin</h5>
    </div>
    <div class="wti-card-body text-center py-4">
      <div style="width:80px;height:80px;background:rgba(220,53,69,.1);border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 1.5rem">
        <i class="fas fa-user-times" style="font-size:2rem;color:#dc3545"></i>
      </div>
      <h5 style="font-weight:700;color:#0a1628">Delete {{ admin_user.get_full_name|default:admin_user.username }}?</h5>
      <p class="text-muted" style="font-size:.85rem">Username: <strong>{{ admin_user.username }}</strong></p>
      <div class="alert alert-danger" style="font-size:.82rem;border-radius:10px;text-align:left">
        <i class="fas fa-exclamation-circle me-2"></i>
        This will permanently delete this admin account. All their actions will remain in the system but they will lose access.
      </div>
      <div class="d-flex gap-3 justify-content-center mt-3">
        <a href="{% url 'superadmin_dashboard' %}" class="btn btn-outline-secondary rounded-3 px-4">
          <i class="fas fa-arrow-left me-2"></i>Cancel
        </a>
        <form method="post" style="display:inline">
          {% csrf_token %}
          <button type="submit" class="btn btn-danger rounded-3 px-4" style="font-weight:700">
            <i class="fas fa-trash me-2"></i>Yes, Delete Admin
          </button>
        </form>
      </div>
    </div>
  </div>
</div>
</div>
{% endblock %}
"""

with open('templates/superadmin/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(dashboard)
with open('templates/superadmin/create_admin.html', 'w', encoding='utf-8') as f:
    f.write(create_admin)
with open('templates/superadmin/confirm_delete_admin.html', 'w', encoding='utf-8') as f:
    f.write(confirm_delete)

print('All superadmin templates written')
