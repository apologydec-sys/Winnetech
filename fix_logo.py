import os, glob

OLD = "ChatGPT Image Apr 28, 2026, 10_01_09 AM.png"
NEW = "wti_logo.png"

# Fix in all templates EXCEPT the slideshow (welcome.html uses old images for slideshow)
files = glob.glob('templates/**/*.html', recursive=True)
count = 0
for f in files:
    content = open(f, encoding='utf-8').read()
    # Replace logo references (in img src for brand/logo circles)
    # But NOT the slideshow background-image references
    new_content = content
    # Replace in img tags
    new_content = new_content.replace(
        f"images/{OLD}",
        f"images/{NEW}"
    )
    if new_content != content:
        open(f, 'w', encoding='utf-8').write(new_content)
        count += 1
        print(f'  Fixed: {f}')

# Now restore slideshow images in welcome.html (they should stay as original)
wf = 'templates/welcome.html'
wc = open(wf, encoding='utf-8').read()
# The slideshow uses all 5 images - restore them
from_img = "images/wti_logo.png"
to_img = f"images/{OLD}"
# Only restore in background-image style attributes (slideshow)
import re
def restore_slideshow(m):
    return m.group(0).replace(from_img, to_img)
wc_new = re.sub(r"background-image:url\('[^']*'\)", restore_slideshow, wc)
if wc_new != wc:
    open(wf, 'w', encoding='utf-8').write(wc_new)
    print('  Restored slideshow images in welcome.html')

print(f'\nDone: {count} files updated with WTI logo')
