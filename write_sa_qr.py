src = open('templates/admin/qr_generate.html', encoding='utf-8').read()
dst = src.replace('admin/base_admin.html', 'superadmin/base_superadmin.html')
open('templates/superadmin/qr_generate.html', 'w', encoding='utf-8').write(dst)
print('superadmin qr_generate.html written')
