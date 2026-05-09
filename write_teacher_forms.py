import os

DEPT_SUBJECTS_JS = """
var DS={
  information_technology:[['computer_system_servicing','Computer System & Servicing'],['workshop_practice_power','Workshop Practice & Power Mgmt'],['networking_data_comm','Networking & Data Communication']],
  plumbing:[['plumbing_general','Plumbing (General)'],['plumbing_installation','Plumbing Installation'],['plumbing_maintenance','Plumbing Maintenance']],
  electricals:[['electrical_installation','Electrical Installation'],['electrical_maintenance','Electrical Maintenance'],['electrical_wiring','Electrical Wiring']],
  welding_fabrication:[['welding_fabrication','Welding & Fabrication'],['metal_work','Metal Work']],
  fashion:[['fashion_design','Fashion Design'],['garment_construction','Garment Construction'],['textile_studies','Textile Studies']],
  catering:[['catering_general','Catering (General)'],['food_beverage','Food & Beverage'],['hospitality','Hospitality Management']],
  mechanical_engineering:[['mechanical_engineering','Mechanical Engineering'],['machine_maintenance','Machine Maintenance']],
  auto_mechanics:[['auto_mechanics','Auto Mechanics'],['auto_electrical','Auto Electrical']],
  building_construction:[['building_construction','Building & Construction'],['masonry','Masonry'],['carpentry','Carpentry']]
};
function pickType(t){
  document.getElementById('hct').value=t;
  document.getElementById('hs').value='';
  document.getElementById('hd').value='';
  document.getElementById('tc_el').classList.toggle('pk',t==='core');
  document.getElementById('tc_dp').classList.toggle('pk',t==='departmental');
  document.getElementById('elSec').style.display=t==='core'?'block':'none';
  document.getElementById('dpSec').style.display=t==='departmental'?'block':'none';
  document.getElementById('subjGrid').style.display='none';
}
function pickSubj(val,el){
  document.querySelectorAll('#elSec .sc').forEach(function(e){e.classList.remove('pk');});
  el.classList.add('pk');
  document.getElementById('hs').value=val;
}
function pickDept(val,el){
  document.querySelectorAll('#deptGrid .sc').forEach(function(e){e.classList.remove('pk');});
  el.classList.add('pk');
  document.getElementById('hd').value=val;
  document.getElementById('hs').value='';
  var subs=DS[val]||[];
  document.getElementById('subjList').innerHTML=subs.map(function(s){
    return '<div class="col-md-4 col-6"><div class="sc" onclick="pickDS(\\''+s[0]+'\\',this)"><i class=\\"fas fa-circle\\" style=\\"font-size:.4rem;color:#f5a623\\"></i>'+s[1]+'</div></div>';
  }).join('');
  document.getElementById('subjGrid').style.display='block';
}
function pickDS(val,el){
  document.querySelectorAll('#subjList .sc').forEach(function(e){e.classList.remove('pk');});
  el.classList.add('pk');
  document.getElementById('hs').value=val;
}
"""

PROFILE_FORM_FIELDS = """
      <div class="row g-3">
        <div class="col-md-6">
          <label class="form-label">First Name *</label>
          <input type="text" name="first_name" class="form-control {% if errors.first_name %}is-invalid{% endif %}" value="{{ post.first_name|default:profile.user.first_name }}" required>
          {% if errors.first_name %}<div class="invalid-feedback">{{ errors.first_name }}</div>{% endif %}
        </div>
        <div class="col-md-6">
          <label class="form-label">Last Name *</label>
          <input type="text" name="last_name" class="form-control {% if errors.last_name %}is-invalid{% endif %}" value="{{ post.last_name|default:profile.user.last_name }}" required>
          {% if errors.last_name %}<div class="invalid-feedback">{{ errors.last_name }}</div>{% endif %}
        </div>
        <div class="col-md-6">
          <label class="form-label">Email</label>
          <input type="email" name="email" class="form-control" value="{{ post.email|default:profile.user.email }}">
        </div>
        <div class="col-md-6">
          <label class="form-label">Phone *</label>
          <input type="tel" name="phone" class="form-control {% if errors.phone %}is-invalid{% endif %}" value="{{ post.phone|default:profile.phone }}" required>
          {% if errors.phone %}<div class="invalid-feedback">{{ errors.phone }}</div>{% endif %}
        </div>
        <div class="col-md-6">
          <label class="form-label">Gender *</label>
          <select name="gender" class="form-select {% if errors.gender %}is-invalid{% endif %}" required>
            <option value="">-- Select --</option>
            {% for val,label in genders %}
            <option value="{{ val }}" {% if post.gender == val or profile.gender == val %}selected{% endif %}>{{ label }}</option>
            {% endfor %}
          </select>
          {% if errors.gender %}<div class="invalid-feedback">{{ errors.gender }}</div>{% endif %}
        </div>
        <div class="col-md-6">
          <label class="form-label">Date of Birth</label>
          <input type="date" name="date_of_birth" class="form-control" value="{{ post.date_of_birth|default:profile.date_of_birth }}">
        </div>
        <div class="col-12">
          <label class="form-label">Residential Address *</label>
          <textarea name="address" class="form-control {% if errors.address %}is-invalid{% endif %}" rows="2" required>{{ post.address|default:profile.address }}</textarea>
          {% if errors.address %}<div class="invalid-feedback">{{ errors.address }}</div>{% endif %}
        </div>
        <div class="col-md-6">
          <label class="form-label">Qualification *</label>
          <select name="qualification" class="form-select {% if errors.qualification %}is-invalid{% endif %}" required>
            <option value="">-- Select --</option>
            {% for val,label in qualifications %}
            <option value="{{ val }}" {% if post.qualification == val or profile.qualification == val %}selected{% endif %}>{{ label }}</option>
            {% endfor %}
          </select>
          {% if errors.qualification %}<div class="invalid-feedback">{{ errors.qualification }}</div>{% endif %}
        </div>
        <div class="col-md-6">
          <label class="form-label">Years of Experience</label>
          <input type="number" name="years_of_experience" class="form-control" min="0" value="{{ post.years_of_experience|default:profile.years_of_experience }}">
        </div>
        <div class="col-12">
          <label class="form-label">Specialization *</label>
          <input type="text" name="specialization" class="form-control {% if errors.specialization %}is-invalid{% endif %}" value="{{ post.specialization|default:profile.specialization }}" required>
          {% if errors.specialization %}<div class="invalid-feedback">{{ errors.specialization }}</div>{% endif %}
        </div>
        <div class="col-12">
          <label class="form-label">Previous School</label>
          <input type="text" name="previous_school" class="form-control" value="{{ post.previous_school|default:profile.previous_school }}">
        </div>
        <div class="col-12">
          <label class="form-label">Professional Bio</label>
          <textarea name="bio" class="form-control" rows="2">{{ post.bio|default:profile.bio }}</textarea>
        </div>
        <div class="col-md-6">
          <label class="form-label">Emergency Contact</label>
          <input type="text" name="emergency_contact" class="form-control" value="{{ post.emergency_contact|default:profile.emergency_contact }}">
        </div>
        <div class="col-md-6">
          <label class="form-label">Emergency Phone</label>
          <input type="tel" name="emergency_phone" class="form-control" value="{{ post.emergency_phone|default:profile.emergency_phone }}">
        </div>
      </div>

      <!-- Course Type & Subject -->
      <hr class="my-3">
      <h6 style="font-weight:700;color:#003087;margin-bottom:1rem"><i class="fas fa-book-open me-2"></i>Course Preference</h6>
      <input type="hidden" name="course_type" id="hct" value="{{ post.course_type|default:profile.course_type }}">
      <input type="hidden" name="preferred_subject" id="hs" value="{{ post.preferred_subject|default:profile.preferred_subject }}">
      <input type="hidden" name="department" id="hd" value="{{ post.department|default:profile.department }}">
      {% if errors.course_type or errors.preferred_subject %}
      <div class="alert alert-danger" style="font-size:.82rem;border-radius:10px"><i class="fas fa-exclamation-circle me-2"></i>Please select a course type and subject.</div>
      {% endif %}
      <div class="row g-2 mb-3">
        <div class="col-6">
          <div class="tc {% if post.course_type == 'core' or profile.course_type == 'core' %}pk{% endif %}" id="tc_el" onclick="pickType('core')" style="border:2px solid #e8ecf0;border-radius:12px;padding:1rem;cursor:pointer;text-align:center;transition:all .2s">
            <i class="fas fa-book" style="font-size:1.5rem;display:block;margin-bottom:.3rem;color:#00d4ff"></i>
            <div class="fw-bold" style="font-size:.88rem">Core Subjects</div>
          </div>
        </div>
        <div class="col-6">
          <div class="tc {% if post.course_type == 'departmental' or profile.course_type == 'departmental' %}pk{% endif %}" id="tc_dp" onclick="pickType('departmental')" style="border:2px solid #e8ecf0;border-radius:12px;padding:1rem;cursor:pointer;text-align:center;transition:all .2s">
            <i class="fas fa-tools" style="font-size:1.5rem;display:block;margin-bottom:.3rem;color:#f5a623"></i>
            <div class="fw-bold" style="font-size:.88rem">Departmental</div>
          </div>
        </div>
      </div>
      <div id="elSec" style="display:{% if post.course_type == 'core' or profile.course_type == 'core' %}block{% else %}none{% endif %}">
        <label class="form-label fw-bold">Select Subject *</label>
        <div class="row g-2">
          {% for val,label in elective_subjects %}
          <div class="col-md-4 col-6"><div class="sc {% if post.preferred_subject == val or profile.preferred_subject == val %}pk{% endif %}" onclick="pickSubj('{{ val }}',this)" style="border:2px solid #e8ecf0;border-radius:10px;padding:.55rem .9rem;cursor:pointer;font-size:.82rem;display:flex;align-items:center;gap:.5rem;transition:all .2s">{{ label }}</div></div>
          {% endfor %}
        </div>
      </div>
      <div id="dpSec" style="display:{% if post.course_type == 'departmental' or profile.course_type == 'departmental' %}block{% else %}none{% endif %}">
        <label class="form-label fw-bold">Select Department *</label>
        <div class="row g-2 mb-3" id="deptGrid">
          {% for val,label in dept_choices %}
          <div class="col-md-4 col-6"><div class="sc {% if post.department == val or profile.department == val %}pk{% endif %}" onclick="pickDept('{{ val }}',this)" style="border:2px solid #e8ecf0;border-radius:10px;padding:.55rem .9rem;cursor:pointer;font-size:.82rem;display:flex;align-items:center;gap:.5rem;transition:all .2s">{{ label }}</div></div>
          {% endfor %}
        </div>
        <div id="subjGrid" style="display:{% if profile.department %}block{% else %}none{% endif %}">
          <label class="form-label fw-bold">Select Subject *</label>
          <div class="row g-2" id="subjList"></div>
        </div>
      </div>

      <!-- Documents -->
      <hr class="my-3">
      <h6 style="font-weight:700;color:#003087;margin-bottom:1rem"><i class="fas fa-file-upload me-2"></i>Documents (Optional)</h6>
      <div class="row g-3">
        <div class="col-md-6">
          <label class="form-label">Profile Photo</label>
          <input type="file" name="profile_photo" class="form-control" accept="image/*">
          {% if profile.profile_photo %}<small class="text-muted">Current: {{ profile.profile_photo.name|truncatechars:30 }}</small>{% endif %}
        </div>
        <div class="col-md-6">
          <label class="form-label">CV / Resume</label>
          <input type="file" name="cv_document" class="form-control" accept=".pdf,.doc,.docx">
        </div>
        <div class="col-md-6">
          <label class="form-label">Certificate</label>
          <input type="file" name="certificate_document" class="form-control" accept=".pdf,.jpg,.jpeg,.png">
        </div>
        <div class="col-md-6">
          <label class="form-label">National ID / Passport</label>
          <input type="file" name="id_document" class="form-control" accept=".pdf,.jpg,.jpeg,.png">
        </div>
      </div>
"""

# ── Complete Profile (first login) ────────────────────────────────────────────
T_COMPLETE = """{% extends 'base.html' %}
{% load static %}
{% block title %}Complete Your Profile — WTI{% endblock %}
{% block extra_css %}
<style>
body{font-family:'Poppins',sans-serif;background:linear-gradient(135deg,#001f5c,#003087);min-height:100vh;padding:2rem 1rem;}
.cp-card{background:#fff;border-radius:20px;padding:2rem;max-width:820px;margin:0 auto;box-shadow:0 20px 60px rgba(0,0,0,.3);}
.cp-header{text-align:center;margin-bottom:1.5rem;padding-bottom:1rem;border-bottom:2px solid #e8f0fe;}
.cp-header img{width:60px;height:60px;border-radius:50%;border:3px solid #003087;object-fit:contain;background:#fff;padding:3px;margin-bottom:.5rem;}
.cp-header h4{font-weight:800;color:#003087;margin:0;}
.cp-header p{color:#888;font-size:.82rem;margin:.3rem 0 0;}
.form-control,.form-select{border:2px solid #e8ecf0;border-radius:10px;padding:.55rem .9rem;font-size:.88rem;}
.form-control:focus,.form-select:focus{border-color:#003087;box-shadow:0 0 0 3px rgba(0,48,135,.12);outline:none;}
.form-control.is-invalid{border-color:#dc3545;}
.form-label{font-size:.8rem;font-weight:600;color:#555;margin-bottom:.3rem;}
.sc:hover,.sc.pk{border-color:#f5a623!important;background:rgba(245,166,35,.08);}
.sc.pk{font-weight:600;}
.tc:hover,.tc.pk{border-color:#003087!important;background:rgba(0,48,135,.05);}
.btn-submit{background:linear-gradient(135deg,#003087,#0047b3);color:#fff;border:none;border-radius:10px;padding:.7rem 2rem;font-weight:700;font-size:.9rem;cursor:pointer;width:100%;}
</style>
{% endblock %}
{% block body %}
<div class="cp-card">
  <div class="cp-header">
    <img src="{% static 'images/logo.png' %}" alt="WTI">
    <h4>Welcome! Complete Your Profile</h4>
    <p>Staff ID: <strong style="color:#003087">{{ profile.staff_id }}</strong> — Please fill in your details to continue</p>
  </div>
  {% if messages %}{% for m in messages %}<div class="alert alert-{{ m.tags }}" style="font-size:.83rem;border-radius:10px">{{ m }}</div>{% endfor %}{% endif %}
  <form method="post" enctype="multipart/form-data" novalidate>
    {% csrf_token %}
    """ + PROFILE_FORM_FIELDS + """
    <div class="mt-4">
      <button type="submit" class="btn-submit"><i class="fas fa-check-circle me-2"></i>Complete Profile & Continue</button>
    </div>
  </form>
</div>
<script>""" + DEPT_SUBJECTS_JS + """
// Restore state
(function(){
  var ct=document.getElementById('hct').value;
  var dept=document.getElementById('hd').value;
  if(ct){pickType(ct);}
  if(dept){var el=document.querySelector('#deptGrid .sc[onclick*="'+dept+'"]');if(el)pickDept(dept,el);}
})();
</script>
{% endblock %}
"""

# ── Update Profile ────────────────────────────────────────────────────────────
T_UPDATE = """{% extends 'teacher/base_teacher.html' %}
{% load static %}
{% block title %}Update Profile — WTI{% endblock %}
{% block page_title %}Update My Profile{% endblock %}
{% block nav_profile %}active{% endblock %}
{% block content %}
<div class="wti-card">
  <div class="wti-card-header">
    <h5><i class="fas fa-user-edit"></i> Update Profile</h5>
  </div>
  <div class="wti-card-body">
    {% if success %}<div class="alert alert-success" style="font-size:.83rem;border-radius:10px"><i class="fas fa-check-circle me-2"></i>{{ success }}</div>{% endif %}
    {% if errors %}<div class="alert alert-danger" style="font-size:.83rem;border-radius:10px"><i class="fas fa-exclamation-circle me-2"></i>Please fix the errors below.</div>{% endif %}
    <form method="post" enctype="multipart/form-data" novalidate>
      {% csrf_token %}
      """ + PROFILE_FORM_FIELDS + """
      <div class="mt-4">
        <button type="submit" class="btn-gold px-4 py-2 rounded-3"><i class="fas fa-save me-2"></i>Save Changes</button>
      </div>
    </form>
  </div>
</div>
<style>
.sc:hover,.sc.pk{border-color:#f5a623!important;background:rgba(245,166,35,.08);}
.sc.pk{font-weight:600;}
.tc:hover,.tc.pk{border-color:#003087!important;background:rgba(0,48,135,.05);}
</style>
<script>""" + DEPT_SUBJECTS_JS + """
(function(){
  var ct=document.getElementById('hct').value;
  var dept=document.getElementById('hd').value;
  if(ct){pickType(ct);}
  if(dept){var el=document.querySelector('#deptGrid .sc[onclick*="'+dept+'"]');if(el)pickDept(dept,el);}
})();
</script>
{% endblock %}
"""

# ── Change Password ───────────────────────────────────────────────────────────
T_PASSWORD = """{% extends 'teacher/base_teacher.html' %}
{% load static %}
{% block title %}Change Password — WTI{% endblock %}
{% block page_title %}Change Password{% endblock %}
{% block nav_password %}active{% endblock %}
{% block content %}
<div class="row justify-content-center">
<div class="col-lg-5">
  <div class="wti-card">
    <div class="wti-card-header" style="background:linear-gradient(135deg,#003087,#0047b3)">
      <h5 style="color:#fff"><i class="fas fa-key me-2"></i>Change Password</h5>
    </div>
    <div class="wti-card-body">
      {% if error %}<div class="alert alert-danger" style="font-size:.83rem;border-radius:10px"><i class="fas fa-exclamation-circle me-2"></i>{{ error }}</div>{% endif %}
      {% if success %}<div class="alert alert-success" style="font-size:.83rem;border-radius:10px"><i class="fas fa-check-circle me-2"></i>{{ success }}</div>{% endif %}
      <form method="post" novalidate>
        {% csrf_token %}
        <div class="mb-3">
          <label class="form-label">Current Password *</label>
          <div class="position-relative">
            <input type="password" name="current_password" id="cp" class="form-control" placeholder="Enter current password" required>
            <button type="button" class="btn btn-sm position-absolute end-0 top-50 translate-middle-y me-2 border-0 bg-transparent text-muted" onclick="var e=document.getElementById('cp');e.type=e.type=='password'?'text':'password'"><i class="fas fa-eye"></i></button>
          </div>
        </div>
        <div class="mb-3">
          <label class="form-label">New Password *</label>
          <div class="position-relative">
            <input type="password" name="new_password" id="np" class="form-control" placeholder="Enter new password" required>
            <button type="button" class="btn btn-sm position-absolute end-0 top-50 translate-middle-y me-2 border-0 bg-transparent text-muted" onclick="var e=document.getElementById('np');e.type=e.type=='password'?'text':'password'"><i class="fas fa-eye"></i></button>
          </div>
        </div>
        <div class="mb-4">
          <label class="form-label">Confirm New Password *</label>
          <div class="position-relative">
            <input type="password" name="confirm_password" id="cnp" class="form-control" placeholder="Confirm new password" required>
            <button type="button" class="btn btn-sm position-absolute end-0 top-50 translate-middle-y me-2 border-0 bg-transparent text-muted" onclick="var e=document.getElementById('cnp');e.type=e.type=='password'?'text':'password'"><i class="fas fa-eye"></i></button>
          </div>
        </div>
        <button type="submit" class="btn-gold w-100 py-2 rounded-3"><i class="fas fa-save me-2"></i>Change Password</button>
      </form>
    </div>
  </div>
</div>
</div>
{% endblock %}
"""

# ── Admin Create Teacher (simplified) ────────────────────────────────────────
T_CREATE = """{% extends 'admin/base_admin.html' %}
{% load static %}
{% block title %}Add Teacher — WTI{% endblock %}
{% block page_title %}Add New Teacher{% endblock %}
{% block nav_teachers %}active{% endblock %}
{% block content %}
<div class="row justify-content-center">
<div class="col-lg-6">
  <div class="wti-card">
    <div class="wti-card-header" style="background:linear-gradient(135deg,#003087,#0047b3)">
      <h5 style="color:#fff"><i class="fas fa-user-plus me-2"></i>Create Teacher Account</h5>
    </div>
    <div class="wti-card-body">
      {% if error %}<div class="alert alert-danger" style="font-size:.83rem;border-radius:10px"><i class="fas fa-exclamation-circle me-2"></i>{{ error }}</div>{% endif %}
      {% if success %}<div class="alert alert-success" style="font-size:.83rem;border-radius:10px">{{ success }}</div>{% endif %}
      <div class="alert alert-info" style="font-size:.82rem;border-radius:10px">
        <i class="fas fa-info-circle me-2"></i>
        <strong>Admin creates Staff ID + Password only.</strong> The teacher will complete their full profile on first login.
      </div>
      <form method="post" novalidate>
        {% csrf_token %}
        <div class="row g-3">
          <div class="col-12">
            <label class="form-label">Staff ID * <small style="color:#888;font-weight:400">(teacher's login ID)</small></label>
            <input type="text" name="staff_id" class="form-control" placeholder="e.g. WTI0001"
                   style="text-transform:uppercase;font-weight:700;letter-spacing:1px;font-size:1rem"
                   oninput="this.value=this.value.toUpperCase()" required autofocus>
            <small class="text-muted" style="font-size:.72rem">Must be unique. Teacher uses this to login.</small>
          </div>
          <div class="col-md-6">
            <label class="form-label">First Name <small style="color:#888">(optional)</small></label>
            <input type="text" name="first_name" class="form-control" placeholder="First Name">
          </div>
          <div class="col-md-6">
            <label class="form-label">Last Name <small style="color:#888">(optional)</small></label>
            <input type="text" name="last_name" class="form-control" placeholder="Last Name">
          </div>
          <div class="col-12">
            <label class="form-label">Password * <small style="color:#888;font-weight:400">(teacher's login password)</small></label>
            <div class="position-relative">
              <input type="text" name="password" id="pw" class="form-control" placeholder="Set a password" required
                     style="font-weight:600;letter-spacing:1px">
            </div>
            <small class="text-muted" style="font-size:.72rem">Minimum 4 characters. Share this with the teacher securely.</small>
          </div>
        </div>
        <div class="d-flex gap-2 mt-4">
          <a href="{% url 'admin_teachers' %}" class="btn btn-outline-secondary rounded-3 px-4">Cancel</a>
          <button type="submit" style="background:linear-gradient(135deg,#003087,#0047b3);color:#fff;border:none;border-radius:10px;padding:.6rem 1.5rem;font-weight:700;font-size:.88rem;cursor:pointer;flex:1">
            <i class="fas fa-user-plus me-2"></i>Create Teacher Account
          </button>
        </div>
      </form>
    </div>
  </div>
</div>
</div>
{% endblock %}
"""

with open('templates/teacher/complete_profile.html', 'w', encoding='utf-8') as f:
    f.write(T_COMPLETE)
with open('templates/teacher/update_profile.html', 'w', encoding='utf-8') as f:
    f.write(T_UPDATE)
with open('templates/teacher/change_password.html', 'w', encoding='utf-8') as f:
    f.write(T_PASSWORD)
with open('templates/admin/create_teacher.html', 'w', encoding='utf-8') as f:
    f.write(T_CREATE)

print('All 4 templates written')
