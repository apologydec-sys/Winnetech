"""
Generate PWA icons from the school image.
Run: python generate_icons.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'winnitech.settings')
django.setup()

from PIL import Image, ImageDraw, ImageFont
import os

ICONS_DIR = os.path.join('static', 'icons')
os.makedirs(ICONS_DIR, exist_ok=True)

SOURCE_IMAGE = os.path.join('static', 'images', 'ChatGPT Image Apr 28, 2026, 10_01_09 AM.png')

SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

def create_icon(size):
    """Create a PWA icon at the given size."""
    # Try to use the school image
    if os.path.exists(SOURCE_IMAGE):
        try:
            img = Image.open(SOURCE_IMAGE).convert('RGBA')
            # Create a square canvas with gold background
            canvas = Image.new('RGBA', (size, size), (10, 22, 40, 255))  # dark blue bg
            
            # Resize source image to fit
            img_size = int(size * 0.75)
            img = img.resize((img_size, img_size), Image.LANCZOS)
            
            # Center the image
            offset = (size - img_size) // 2
            canvas.paste(img, (offset, offset), img if img.mode == 'RGBA' else None)
            
            # Add gold border circle
            draw = ImageDraw.Draw(canvas)
            border = 3
            draw.ellipse(
                [border, border, size - border, size - border],
                outline=(245, 166, 35, 255),
                width=max(2, size // 40)
            )
            
            # Convert to RGB for PNG
            final = Image.new('RGB', (size, size), (10, 22, 40))
            final.paste(canvas, mask=canvas.split()[3] if canvas.mode == 'RGBA' else None)
            return final
        except Exception as e:
            print(f'  Warning: Could not process source image: {e}')
    
    # Fallback: create a simple icon with WTI text
    img = Image.new('RGB', (size, size), (10, 22, 40))
    draw = ImageDraw.Draw(img)
    
    # Gold circle background
    padding = size // 8
    draw.ellipse(
        [padding, padding, size - padding, size - padding],
        fill=(245, 166, 35)
    )
    
    # WTI text
    text = 'WTI'
    font_size = size // 4
    try:
        font = ImageFont.truetype('arial.ttf', font_size)
    except:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) // 2
    y = (size - text_h) // 2
    draw.text((x, y), text, fill=(10, 22, 40), font=font)
    
    return img

print('🎨 Generating PWA icons...')
for size in SIZES:
    icon = create_icon(size)
    path = os.path.join(ICONS_DIR, f'icon-{size}.png')
    icon.save(path, 'PNG', optimize=True)
    print(f'  ✅ icon-{size}.png')

print(f'\n✅ All {len(SIZES)} icons generated in static/icons/')
