"""
Auto thumbnail generator — professional YouTube style.
Bold text + gradient background + visual elements.
"""
import os
import textwrap
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]

COLOR_SCHEMES = [
    {"bg_top": "#1a0533", "bg_bot": "#0d0221", "text": "#FFFFFF", "accent": "#FF3CAC", "border": "#FF3CAC"},
    {"bg_top": "#0F2027", "bg_bot": "#203A43", "text": "#FFFFFF", "accent": "#00F5A0", "border": "#00F5A0"},
    {"bg_top": "#1a1a2e", "bg_bot": "#16213e", "text": "#FFFFFF", "accent": "#FFD60A", "border": "#FFD60A"},
    {"bg_top": "#200122", "bg_bot": "#6f0000", "text": "#FFFFFF", "accent": "#FF6B6B", "border": "#FF6B6B"},
    {"bg_top": "#0f0c29", "bg_bot": "#302b63", "text": "#FFFFFF", "accent": "#00D2FF", "border": "#00D2FF"},
    {"bg_top": "#1D2B64", "bg_bot": "#F8CDDA", "text": "#1a1a1a", "accent": "#FF6B35", "border": "#FF6B35"},
]


def _font(size: int):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _hex_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _gradient_bg(img: Image.Image, top: str, bot: str):
    draw = ImageDraw.Draw(img)
    w, h = img.size
    tc = _hex_rgb(top)
    bc = _hex_rgb(bot)
    for y in range(h):
        r = int(tc[0] + (bc[0] - tc[0]) * y / h)
        g = int(tc[1] + (bc[1] - tc[1]) * y / h)
        b = int(tc[2] + (bc[2] - tc[2]) * y / h)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def _add_glow_circle(img: Image.Image, accent: str):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = img.size
    ac = _hex_rgb(accent)
    draw.ellipse([(w*0.5, h*0.3), (w*1.3, h*1.3)],
                 fill=(ac[0], ac[1], ac[2], 18))
    draw.ellipse([(-w*0.2, -h*0.2), (w*0.5, h*0.5)],
                 fill=(ac[0], ac[1], ac[2], 12))
    glow = overlay.filter(ImageFilter.GaussianBlur(60))
    img.paste(Image.alpha_composite(
        img.convert("RGBA"), glow).convert("RGB"))


def _draw_text_block(draw, lines, font_big, font_sm,
                     w, h, text_color, accent, is_short):
    tc = _hex_rgb(text_color)
    ac = _hex_rgb(accent)
    line_h_big = int(font_big.size * 1.2)
    line_h_sm = int(font_sm.size * 1.2)
    total_h = 0
    for i, ln in enumerate(lines):
        total_h += line_h_big if i < 2 else line_h_sm
    total_h += 20 * (len(lines) - 1)
    y = int(h * 0.42) - total_h // 2
    for i, ln in enumerate(lines):
        font = font_big if i < 2 else font_sm
        lh = line_h_big if i < 2 else line_h_sm
        bbox = draw.textbbox((0, 0), ln, font=font)
        lw = bbox[2] - bbox[0]
        x = (w - lw) / 2
        for ox, oy in [(4, 4), (3, 3), (2, 2)]:
            draw.text((x + ox, y + oy), ln, font=font, fill=(0, 0, 0))
        color = ac if i == 0 else tc
        draw.text((x, y), ln, font=font, fill=color)
        y += lh + 8


def _add_border(draw, w, h, accent, thickness=12):
    ac = _hex_rgb(accent)
    for i in range(thickness):
        draw.rectangle([(i, i), (w-1-i, h-1-i)], outline=ac)


def _add_top_label(draw, w, accent):
    ac = _hex_rgb(accent)
    label_font = _font(32)
    label = "⚡ AI FACTS ⚡"
    bbox = draw.textbbox((0, 0), label, font=label_font)
    lw = bbox[2] - bbox[0]
    x = (w - lw) / 2
    pad = 16
    draw.rounded_rectangle(
        [(x - pad, 18), (x + lw + pad, 18 + 44)],
        radius=22, fill=(*ac, 220)
    )
    draw.text((x, 22), label, font=label_font, fill=(0, 0, 0))


def make_thumbnail(title: str, hook_text: str, kind: str, out_path: str) -> str:
    W, H = (1280, 720) if kind == "long" else (1080, 1920)
    scheme = random.choice(COLOR_SCHEMES)
    img = Image.new("RGB", (W, H))
    _gradient_bg(img, scheme["bg_top"], scheme["bg_bot"])
    _add_glow_circle(img, scheme["accent"])
    draw = ImageDraw.Draw(img)
    display = hook_text if hook_text else title
    display = display.upper().replace("#SHORTS", "").replace("#SHORT", "").strip()
    if kind == "long":
        fsize_big = int(W * 0.082)
        fsize_sm = int(W * 0.062)
        max_chars = 16
    else:
        fsize_big = int(W * 0.10)
        fsize_sm = int(W * 0.076)
        max_chars = 13
    font_big = _font(fsize_big)
    font_sm = _font(fsize_sm)
    words = display.split()
    lines = []
    line = ""
    for word in words:
        test = (line + " " + word).strip()
        if len(test) <= max_chars:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    lines = lines[:4]
    if lines:
        font_big_h = fsize_big * 1.2
        font_sm_h = fsize_sm * 1.2
        total_h = sum(
            font_big_h if i < 2 else font_sm_h
            for i in range(len(lines))
        ) + 20 * (len(lines) - 1)
        y_center = int(H * 0.42)
        box_y1 = int(y_center - total_h/2 - 30)
        box_y2 = int(y_center + total_h/2 + 30)
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rounded_rectangle(
            [(W * 0.04, box_y1), (W * 0.96, box_y2)],
            radius=20,
            fill=(0, 0, 0, 130)
        )
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)
    _draw_text_block(draw, lines, font_big, font_sm,
                     W, H, scheme["text"], scheme["accent"],
                     kind == "short")
    _add_border(draw, W, H, scheme["accent"], thickness=14)
    _add_top_label(draw, W, scheme["accent"])
    img.save(out_path, "JPEG", quality=95)
    return out_path
