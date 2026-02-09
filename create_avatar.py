"""Generate a bot avatar in Главстрой СПб brand style (blue + white)."""

from PIL import Image, ImageDraw, ImageFont
import os

SIZE = 640
OUT = os.path.join(os.path.dirname(__file__), "avatar.png")

img = Image.new("RGB", (SIZE, SIZE), "#1565C0")  # Главстрой blue
draw = ImageDraw.Draw(img)

# Background gradient effect — darker at bottom
for y in range(SIZE):
    alpha = int(255 * (1 - y / SIZE * 0.35))
    r = int(0x15 * alpha / 255)
    g = int(0x65 * alpha / 255)
    b = int(0xC0 * alpha / 255)
    draw.line([(0, y), (SIZE, y)], fill=(r, g, b))

# Building silhouettes
buildings = [
    # (x, width, height)
    (40, 80, 280),
    (130, 60, 220),
    (200, 90, 340),
    (300, 70, 260),
    (380, 85, 310),
    (475, 65, 240),
    (550, 70, 200),
]

base_y = SIZE - 60

for bx, bw, bh in buildings:
    # Building body
    draw.rectangle([bx, base_y - bh, bx + bw, base_y], fill="#0D47A1")
    # Windows
    win_w, win_h = 12, 14
    cols = max(1, (bw - 16) // (win_w + 8))
    rows = max(1, (bh - 20) // (win_h + 12))
    for row in range(rows):
        for col in range(cols):
            wx = bx + 10 + col * (win_w + 8)
            wy = base_y - bh + 15 + row * (win_h + 12)
            # Some windows lit, some dark
            if (row + col) % 3 != 0:
                color = "#FFF9C4"  # warm light
            else:
                color = "#1A237E"  # dark
            draw.rectangle([wx, wy, wx + win_w, wy + win_h], fill=color)

# Ground
draw.rectangle([0, base_y, SIZE, SIZE], fill="#0D47A1")

# Crane silhouette
crane_x = 460
crane_base = base_y - 200
draw.rectangle([crane_x, crane_base - 180, crane_x + 6, crane_base], fill="#BBDEFB")  # mast
draw.rectangle([crane_x - 80, crane_base - 180, crane_x + 100, crane_base - 174], fill="#BBDEFB")  # boom
draw.line([(crane_x + 3, crane_base - 180), (crane_x - 80, crane_base - 160)], fill="#BBDEFB", width=2)  # cable
draw.line([(crane_x + 3, crane_base - 180), (crane_x + 100, crane_base - 160)], fill="#BBDEFB", width=2)

# Main text — bot icon / hard hat emoji area
# Draw a white hard hat shape
hat_cx, hat_cy = SIZE // 2, 200
# Hat brim
draw.ellipse([hat_cx - 90, hat_cy - 20, hat_cx + 90, hat_cy + 30], fill="white")
# Hat dome
draw.ellipse([hat_cx - 65, hat_cy - 70, hat_cx + 65, hat_cy + 5], fill="white")
# Hat stripe
draw.rectangle([hat_cx - 55, hat_cy - 30, hat_cx + 55, hat_cy - 20], fill="#1565C0")

# Text: "ГС" on the hat
try:
    font_big = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
except OSError:
    font_big = ImageFont.load_default()

draw.text((hat_cx - 22, hat_cy - 65), "ГС", fill="#1565C0", font=font_big)

# Bot name text at bottom
try:
    font_name = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
    font_sub = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
except OSError:
    font_name = ImageFont.load_default()
    font_sub = ImageFont.load_default()

# "ГЛАВСТРОЙ" text
text1 = "ГЛАВСТРОЙ"
bbox1 = draw.textbbox((0, 0), text1, font=font_name)
tw1 = bbox1[2] - bbox1[0]
draw.text(((SIZE - tw1) // 2, base_y + 2), text1, fill="white", font=font_name)

# "САНКТ-ПЕТЕРБУРГ" subtitle
text2 = "САНКТ-ПЕТЕРБУРГ"
bbox2 = draw.textbbox((0, 0), text2, font=font_sub)
tw2 = bbox2[2] - bbox2[0]
draw.text(((SIZE - tw2) // 2, base_y + 34), text2, fill="#90CAF9", font=font_sub)

img.save(OUT, "PNG", quality=95)
print(f"Avatar saved: {OUT}")
