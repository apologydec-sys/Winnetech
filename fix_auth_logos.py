import glob, re

files = [
    'templates/auth/admin_login.html',
    'templates/auth/teacher_login.html',
    'templates/auth/superadmin_login.html',
    'templates/auth/register.html',
    'templates/admin/base_admin.html',
    'templates/superadmin/base_superadmin.html',
    'templates/teacher/base_teacher.html',
]

for f in files:
    try:
        c = open(f, encoding='utf-8').read()
        # Fix auth logo images - object-fit contain + white bg
        c = c.replace(
            'border:3px solid #f5a623;object-fit:cover',
            'border:3px solid #003087;object-fit:contain;background:#fff;padding:3px'
        )
        c = c.replace(
            'border:3px solid var(--gold);object-fit:cover',
            'border:3px solid #003087;object-fit:contain;background:#fff;padding:3px'
        )
        c = c.replace(
            'border:2px solid rgba(255,255,255,.5);object-fit:cover',
            'border:2px solid rgba(255,255,255,.5);object-fit:contain;background:#fff;padding:2px'
        )
        c = c.replace(
            'border:2px solid var(--gold);object-fit:cover',
            'border:2px solid #003087;object-fit:contain;background:#fff;padding:2px'
        )
        open(f, 'w', encoding='utf-8').write(c)
        print(f'Fixed: {f}')
    except FileNotFoundError:
        print(f'Not found: {f}')

print('Done')
