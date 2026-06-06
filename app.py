import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance, ImageFilter
import io
import numpy as np
import math
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import zipfile
import datetime

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Photo Booth dan Cetak Foto",
    page_icon="📸",
    layout="wide",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background: #0f0f0f; }
    .stApp { background: #0f0f0f; }
    section[data-testid="stSidebar"] { background: #1a1a1a; }
    h1 { color: #f5c518 !important; font-family: 'Courier New', monospace; }
    h2, h3 { color: #e0e0e0 !important; }
    .template-card {
        background: #1e1e1e;
        border: 2px solid #333;
        border-radius: 12px;
        padding: 12px;
        text-align: center;
        margin: 6px 0;
        cursor: pointer;
        transition: border-color 0.2s;
    }
    .template-card:hover { border-color: #f5c518; }
    .template-card.selected { border-color: #f5c518; background: #2a2a1a; }
    .preview-label {
        background: #f5c518;
        color: #000;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 8px;
    }
    div[data-testid="stButton"] > button {
        background: #f5c518 !important;
        color: #000 !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
    }
    div[data-testid="stButton"] > button:hover {
        background: #d4a800 !important;
    }
    .info-box {
        background: #1e2a1e;
        border-left: 4px solid #4caf50;
        padding: 10px 16px;
        border-radius: 4px;
        color: #ccc;
        font-size: 13px;
        margin: 8px 0;
    }
    .filter-label {
        color: #aaa;
        font-size: 12px;
        text-align: center;
        margin-top: 4px;
    }
    .filter-active {
        color: #f5c518;
        font-weight: bold;
        font-size: 12px;
        text-align: center;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ── Template definitions ───────────────────────────────────────────────────────
TEMPLATES = {
    "pas_foto_2x3": {
        "name": "Pas Foto 2×3",
        "w": 2.0, "h": 3.0,
        "cols": 4, "rows": 4,
        "desc": "4×4 = 16 foto\nUkuran 2×3 cm",
        "icon": "🪪",
        "bg_color": (255, 255, 255),
        "border": 0,
        "style": "pasfoto",
    },
    "pas_foto_3x4": {
        "name": "Pas Foto 3×4",
        "w": 3.0, "h": 4.0,
        "cols": 3, "rows": 3,
        "desc": "3×3 = 9 foto\nUkuran 3×4 cm",
        "icon": "🪪",
        "bg_color": (255, 255, 255),
        "border": 0,
        "style": "pasfoto",
    },
    "pas_foto_4x6": {
        "name": "Pas Foto 4×6",
        "w": 4.0, "h": 6.0,
        "cols": 2, "rows": 2,
        "desc": "2×2 = 4 foto\nUkuran 4×6 cm",
        "icon": "📷",
        "bg_color": (255, 255, 255),
        "border": 0,
        "style": "pasfoto",
    },
    "strip_polaroid": {
        "name": "Strip Polaroid",
        "w": 6.0, "h": 4.5,
        "cols": 1, "rows": 4,
        "desc": "1×4 strip\nGaya polaroid klasik",
        "icon": "🎞️",
        "bg_color": (245, 240, 230),
        "border": 15,
        "style": "polaroid",
    },
    "photobooth_grid": {
        "name": "Photo Booth Grid",
        "w": 5.0, "h": 4.0,
        "cols": 2, "rows": 2,
        "desc": "2×2 grid\nGaya photo booth",
        "icon": "🎠",
        "bg_color": (20, 20, 20),
        "border": 8,
        "style": "booth",
    },
    "filmstrip": {
        "name": "Film Strip",
        "w": 5.5, "h": 4.0,
        "cols": 1, "rows": 5,
        "desc": "1×5 strip\nGaya roll film",
        "icon": "🎬",
        "bg_color": (10, 10, 10),
        "border": 10,
        "style": "film",
    },
    "wallet_print": {
        "name": "Wallet Print",
        "w": 6.35, "h": 8.89,
        "cols": 2, "rows": 3,
        "desc": "2×3 = 6 foto\nUkuran kartu (wallet)",
        "icon": "💳",
        "bg_color": (255, 255, 255),
        "border": 4,
        "style": "wallet",
    },
    "studio_print": {
        "name": "Studio Print",
        "w": 7.0, "h": 9.5,
        "cols": 2, "rows": 2,
        "desc": "2×2 = 4 foto\nGaya photo booth studio",
        "icon": "🏪",
        "bg_color": (255, 255, 255),
        "border": 6,
        "style": "studio",
    },
}

# ── Photo Filter / Tema definitions ───────────────────────────────────────────
FILTERS = {
    "normal": {
        "name": "Normal",
        "icon": "🌟",
        "desc": "Foto asli tanpa filter",
    },
    "grayscale": {
        "name": "Hitam Putih",
        "icon": "⬛",
        "desc": "Classic B&W",
    },
    "vintage": {
        "name": "Vintage",
        "icon": "🟤",
        "desc": "Hangat & klasik",
    },
    "cool": {
        "name": "Cool Blue",
        "icon": "🔵",
        "desc": "Tone dingin kebiruan",
    },
    "warm": {
        "name": "Golden Hour",
        "icon": "🟡",
        "desc": "Warm sunset tone",
    },
    "faded": {
        "name": "Faded",
        "icon": "🌫️",
        "desc": "Low contrast dreamy",
    },
    "vivid": {
        "name": "Vivid",
        "icon": "🌈",
        "desc": "Saturasi tinggi, pop!",
    },
    "sepia": {
        "name": "Sepia",
        "icon": "☕",
        "desc": "Coklat antik",
    },
    "noir": {
        "name": "Noir",
        "icon": "🎭",
        "desc": "High-contrast B&W",
    },
    "pastel": {
        "name": "Pastel",
        "icon": "🌸",
        "desc": "Soft & dreamy pastel",
    },
    "neon": {
        "name": "Neon",
        "icon": "💜",
        "desc": "Cyberpunk neon vibe",
    },
    "film_grain": {
        "name": "Film Grain",
        "icon": "📼",
        "desc": "Analog film texture",
    },
}

def apply_filter(img: Image.Image, filter_key: str) -> Image.Image:
    """Apply visual filter/theme to a PIL image."""
    img = img.convert("RGB")
    arr = np.array(img, dtype=np.float32)

    if filter_key == "normal":
        return img

    elif filter_key == "grayscale":
        gray = img.convert("L").convert("RGB")
        return gray

    elif filter_key == "vintage":
        # Warm tones, slight fade, vignette
        arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.1 + 15, 0, 255)   # R up
        arr[:, :, 1] = np.clip(arr[:, :, 1] * 0.95 + 5, 0, 255)   # G slight
        arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.75, 0, 255)        # B down
        result = Image.fromarray(arr.astype(np.uint8))
        # Reduce contrast slightly for vintage fade
        enhancer = ImageEnhance.Contrast(result)
        result = enhancer.enhance(0.85)
        enhancer = ImageEnhance.Brightness(result)
        result = enhancer.enhance(1.05)
        return result

    elif filter_key == "cool":
        arr[:, :, 0] = np.clip(arr[:, :, 0] * 0.85, 0, 255)        # R down
        arr[:, :, 1] = np.clip(arr[:, :, 1] * 0.95, 0, 255)        # G slight
        arr[:, :, 2] = np.clip(arr[:, :, 2] * 1.15 + 10, 0, 255)   # B up
        result = Image.fromarray(arr.astype(np.uint8))
        enhancer = ImageEnhance.Color(result)
        return enhancer.enhance(1.1)

    elif filter_key == "warm":
        arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.15 + 20, 0, 255)  # R up
        arr[:, :, 1] = np.clip(arr[:, :, 1] * 1.05 + 10, 0, 255)  # G slight
        arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.80, 0, 255)        # B down
        result = Image.fromarray(arr.astype(np.uint8))
        enhancer = ImageEnhance.Brightness(result)
        return enhancer.enhance(1.08)

    elif filter_key == "faded":
        # Low contrast + lifted blacks
        arr = np.clip(arr * 0.75 + 40, 0, 255)
        result = Image.fromarray(arr.astype(np.uint8))
        enhancer = ImageEnhance.Color(result)
        result = enhancer.enhance(0.7)
        return result

    elif filter_key == "vivid":
        result = img.copy()
        enhancer = ImageEnhance.Color(result)
        result = enhancer.enhance(1.8)
        enhancer = ImageEnhance.Contrast(result)
        result = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Sharpness(result)
        return enhancer.enhance(1.3)

    elif filter_key == "sepia":
        gray = np.array(img.convert("L"), dtype=np.float32)
        r = np.clip(gray * 1.1 + 20, 0, 255)
        g = np.clip(gray * 0.9 + 10, 0, 255)
        b = np.clip(gray * 0.7, 0, 255)
        sepia_arr = np.stack([r, g, b], axis=2).astype(np.uint8)
        return Image.fromarray(sepia_arr)

    elif filter_key == "noir":
        gray = img.convert("L").convert("RGB")
        enhancer = ImageEnhance.Contrast(gray)
        result = enhancer.enhance(1.8)
        enhancer = ImageEnhance.Brightness(result)
        return enhancer.enhance(0.9)

    elif filter_key == "pastel":
        # Desaturate + lighten + warm
        enhancer = ImageEnhance.Color(img)
        result = enhancer.enhance(0.6)
        arr2 = np.array(result, dtype=np.float32)
        arr2 = np.clip(arr2 * 0.85 + 50, 0, 255)
        result = Image.fromarray(arr2.astype(np.uint8))
        # Slight pink cast
        a = np.array(result, dtype=np.float32)
        a[:, :, 0] = np.clip(a[:, :, 0] + 8, 0, 255)
        a[:, :, 2] = np.clip(a[:, :, 2] + 5, 0, 255)
        return Image.fromarray(a.astype(np.uint8))

    elif filter_key == "neon":
        # High contrast, push blues & magentas
        arr[:, :, 0] = np.clip(arr[:, :, 0] * 0.7, 0, 255)         # R down
        arr[:, :, 1] = np.clip(arr[:, :, 1] * 0.6, 0, 255)         # G down
        arr[:, :, 2] = np.clip(arr[:, :, 2] * 1.4 + 30, 0, 255)    # B way up
        result = Image.fromarray(arr.astype(np.uint8))
        enhancer = ImageEnhance.Contrast(result)
        result = enhancer.enhance(1.5)
        # Purple tint in highlights
        a = np.array(result, dtype=np.float32)
        bright_mask = (a.mean(axis=2) > 128).astype(np.float32)
        a[:, :, 0] = np.clip(a[:, :, 0] + bright_mask * 30, 0, 255)
        return Image.fromarray(a.astype(np.uint8))

    elif filter_key == "film_grain":
        # Slight warm tone + noise
        arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.05 + 5, 0, 255)
        arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.92, 0, 255)
        # Add grain
        h, w = arr.shape[:2]
        grain = np.random.normal(0, 12, (h, w, 3)).astype(np.float32)
        arr = np.clip(arr + grain, 0, 255)
        result = Image.fromarray(arr.astype(np.uint8))
        enhancer = ImageEnhance.Contrast(result)
        return enhancer.enhance(0.95)

    return img

# ── Helpers ────────────────────────────────────────────────────────────────────
DPI = 300
CM_TO_PX = DPI / 2.54

def cm_to_px(val):
    return int(val * CM_TO_PX)

def fit_crop(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    img = img.convert("RGB")
    iw, ih = img.size
    ratio = max(target_w / iw, target_h / ih)
    new_w, new_h = int(iw * ratio), int(ih * ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    x = (new_w - target_w) // 2
    y = (new_h - target_h) // 2
    return img.crop((x, y, x + target_w, y + target_h))

def add_polaroid_frame(img: Image.Image, border_px: int, tpl: dict) -> Image.Image:
    style = tpl["style"]
    bg = tpl["bg_color"]
    pw, ph = img.size

    if style == "polaroid":
        frame_w = pw + border_px * 2
        frame_h = ph + border_px * 2 + int(border_px * 2.5)
        frame = Image.new("RGB", (frame_w, frame_h), bg)
        frame.paste(img, (border_px, border_px))
        return frame

    elif style == "film":
        frame_w = pw + border_px * 2
        frame_h = ph + border_px * 2
        frame = Image.new("RGB", (frame_w, frame_h), bg)
        draw = ImageDraw.Draw(frame)
        hole_w, hole_h = max(4, border_px // 2), max(8, border_px)
        hole_x_left = border_px // 4
        hole_x_right = frame_w - border_px // 4 - hole_w
        for yi in range(3):
            y_pos = border_px + (ph // 3) * yi + ph // 6 - hole_h // 2
            for hx in [hole_x_left, hole_x_right]:
                draw.rounded_rectangle(
                    [hx, y_pos, hx + hole_w, y_pos + hole_h],
                    radius=2, fill=(40, 40, 40)
                )
        frame.paste(img, (border_px, border_px))
        return frame

    elif style in ("booth", "wallet"):
        frame_w = pw + border_px * 2
        frame_h = ph + border_px * 2
        frame = Image.new("RGB", (frame_w, frame_h), bg)
        frame.paste(img, (border_px, border_px))
        return frame

    else:
        return img

def build_studio_sheet(photo: Image.Image, tpl: dict, filter_key: str,
                        studio_name: str = "Photo Booth Studio",
                        studio_sub: str = "NEW WAVE PHOTO STUDIO") -> Image.Image:
    """Build oh!shoot-style studio print with logo text top & bottom."""
    cols, rows = tpl["cols"], tpl["rows"]
    photo_w_px = cm_to_px(tpl["w"])
    photo_h_px = cm_to_px(tpl["h"])
    gap_px     = cm_to_px(0.25)
    margin_px  = cm_to_px(0.5)

    filtered = apply_filter(photo, filter_key)
    cell = fit_crop(filtered, photo_w_px, photo_h_px)
    cell_w, cell_h = cell.size

    # Logo area heights
    logo_top_h    = cm_to_px(1.4)
    logo_bottom_h = cm_to_px(1.8)

    sheet_w = margin_px * 2 + cell_w * cols + gap_px * (cols - 1)
    sheet_h = (margin_px * 2 + cell_h * rows + gap_px * (rows - 1)
               + logo_top_h + logo_bottom_h)

    sheet = Image.new("RGB", (sheet_w, sheet_h), (255, 255, 255))
    draw  = ImageDraw.Draw(sheet)

    # ── Top logo area ──────────────────────────────────────────────────────────
    top_text_y = logo_top_h // 2
    try:
        font_logo = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                                        int(cm_to_px(0.55)))
        font_sub  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                                        int(cm_to_px(0.25)))
    except Exception:
        font_logo = ImageFont.load_default()
        font_sub  = font_logo

    # Studio name top-center
    bbox = draw.textbbox((0, 0), studio_name, font=font_logo)
    tw = bbox[2] - bbox[0]
    draw.text(((sheet_w - tw) // 2, top_text_y - (bbox[3]-bbox[1])//2 - int(cm_to_px(0.1))),
              studio_name, fill=(180, 40, 40), font=font_logo)

    # ── Paste photo grid ──────────────────────────────────────────────────────
    grid_y_offset = logo_top_h + margin_px
    for r in range(rows):
        for c in range(cols):
            x = margin_px + c * (cell_w + gap_px)
            y = grid_y_offset + r * (cell_h + gap_px)
            # Thin border around each photo
            border_col = (220, 220, 220)
            bp = 3  # border px
            draw.rectangle([x-bp, y-bp, x+cell_w+bp, y+cell_h+bp], outline=border_col, width=bp)
            sheet.paste(cell, (x, y))

    # ── Bottom logo area ──────────────────────────────────────────────────────
    bottom_y = sheet_h - logo_bottom_h
    # Divider line
    draw.line([(margin_px, bottom_y + int(cm_to_px(0.15))),
               (sheet_w - margin_px, bottom_y + int(cm_to_px(0.15)))],
              fill=(220, 220, 220), width=2)

    # Big studio name bottom-center
    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                                       int(cm_to_px(0.7)))
    except Exception:
        font_big = ImageFont.load_default()

    bbox_big = draw.textbbox((0, 0), studio_name, font=font_big)
    bw = bbox_big[2] - bbox_big[0]
    bh = bbox_big[3] - bbox_big[1]
    name_y = bottom_y + int(cm_to_px(0.35))
    draw.text(((sheet_w - bw) // 2, name_y), studio_name, fill=(180, 40, 40), font=font_big)

    # Subtitle
    bbox_sub = draw.textbbox((0, 0), studio_sub, font=font_sub)
    sw2 = bbox_sub[2] - bbox_sub[0]
    draw.text(((sheet_w - sw2) // 2, name_y + bh + int(cm_to_px(0.08))),
              studio_sub, fill=(160, 160, 160), font=font_sub)

    return sheet


def build_sheet(photo: Image.Image, tpl: dict, filter_key: str = "normal") -> Image.Image:
    cols, rows = tpl["cols"], tpl["rows"]
    photo_w_px = cm_to_px(tpl["w"])
    photo_h_px = cm_to_px(tpl["h"])
    border_px  = tpl["border"]
    style      = tpl["style"]
    bg         = tpl["bg_color"]

    # Apply filter first
    filtered_photo = apply_filter(photo, filter_key)

    cell_img = fit_crop(filtered_photo, photo_w_px, photo_h_px)
    if style != "pasfoto":
        cell_img = add_polaroid_frame(cell_img, border_px, tpl)

    cell_w, cell_h = cell_img.size
    margin_px = cm_to_px(0.3)
    gap_px    = cm_to_px(0.1) if style == "pasfoto" else cm_to_px(0.2)

    sheet_w = margin_px * 2 + cell_w * cols + gap_px * (cols - 1)
    sheet_h = margin_px * 2 + cell_h * rows + gap_px * (rows - 1)

    if style in ("film", "polaroid"):
        sheet_bg = bg
    else:
        sheet_bg = (255, 255, 255)

    sheet = Image.new("RGB", (sheet_w, sheet_h), sheet_bg)

    for r in range(rows):
        for c in range(cols):
            x = margin_px + c * (cell_w + gap_px)
            y = margin_px + r * (cell_h + gap_px)
            sheet.paste(cell_img, (x, y))

    return sheet

def sheet_to_bytes(sheet: Image.Image, fmt="JPEG") -> bytes:
    buf = io.BytesIO()
    if fmt == "JPEG":
        sheet.save(buf, format="JPEG", quality=95, dpi=(DPI, DPI))
    else:
        sheet.save(buf, format="PNG", dpi=(DPI, DPI))
    return buf.getvalue()

def sheet_to_pdf(sheet: Image.Image, tpl: dict) -> bytes:
    img_bytes = sheet_to_bytes(sheet, "JPEG")
    buf = io.BytesIO()
    ONE_CM = 28.35

    sw, sh = sheet.size
    if sw > sh:
        pagesize = (A4[1], A4[0])
    else:
        pagesize = A4

    c = rl_canvas.Canvas(buf, pagesize=pagesize)
    pw, ph = pagesize

    margin = 0.5 * ONE_CM
    avail_w = pw - 2 * margin
    avail_h = ph - 2 * margin
    scale = min(avail_w / sw, avail_h / sh)
    draw_w = sw * scale
    draw_h = sh * scale
    x_off = (pw - draw_w) / 2
    y_off = (ph - draw_h) / 2

    img_reader = ImageReader(io.BytesIO(img_bytes))
    c.drawImage(img_reader, x_off, y_off, draw_w, draw_h)

    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.6, 0.6, 0.6)
    ts = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    c.drawString(margin, margin * 0.4, f"Photo Booth Print  •  {tpl['name']}  •  {ts}")

    c.save()
    return buf.getvalue()

def preview_thumbnail(sheet: Image.Image, max_px=600) -> Image.Image:
    w, h = sheet.size
    ratio = min(max_px / w, max_px / h)
    return sheet.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

def make_filter_thumb(photo: Image.Image, filter_key: str, size: int = 300) -> Image.Image:
    """Generate a square thumbnail with the given filter applied.
    Filter is applied BEFORE downscaling to preserve quality."""
    w, h = photo.size
    # Center crop to square at original resolution
    side = min(w, h)
    x = (w - side) // 2
    y = (h - side) // 2
    cropped = photo.crop((x, y, x + side, y + side))
    # Apply filter at full crop resolution first
    filtered = apply_filter(cropped, filter_key)
    # Then downscale cleanly
    return filtered.resize((size, size), Image.LANCZOS)


# ── AR Camera Component ────────────────────────────────────────────────────────
import streamlit.components.v1 as components
import base64

def get_ar_camera_html():
    return """<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#111; font-family:'Courier New',monospace; color:#eee; }
#wrap {
  position:relative; width:100%; max-width:520px; margin:0 auto;
}
#video {
  width:100%; display:block; border-radius:10px;
  transform:scaleX(-1);
}
/* Motion indicator bar */
#motionBar {
  width:100%; height:6px; background:#222; border-radius:3px;
  margin-top:6px; overflow:hidden;
}
#motionFill {
  height:100%; width:0%; background:#f5c518;
  transition:width 0.1s; border-radius:3px;
}
/* Countdown overlay */
#countdownOverlay {
  position:absolute; top:0; left:0; width:100%; height:100%;
  display:flex; align-items:center; justify-content:center;
  pointer-events:none; opacity:0;
  border-radius:10px;
}
#countdownNum {
  font-size:clamp(72px,20vw,120px); font-weight:900;
  color:#f5c518; text-shadow:0 0 30px rgba(245,197,24,0.8),0 2px 8px rgba(0,0,0,0.9);
  font-family:'Courier New',monospace;
}
/* Flash */
#flash {
  position:absolute; top:0; left:0; width:100%; height:100%;
  background:white; border-radius:10px; opacity:0; pointer-events:none;
  transition:opacity 0.25s;
}
/* Controls */
#controls {
  display:flex; gap:8px; margin-top:8px;
  justify-content:center; align-items:center;
}
#captureBtn {
  background:#f5c518; color:#000; border:none; border-radius:50%;
  width:64px; height:64px; font-size:26px; cursor:pointer; font-weight:bold;
  box-shadow:0 0 0 4px #333; transition:transform 0.1s;
  flex-shrink:0;
}
#captureBtn:active { transform:scale(0.88); }
.tbtn {
  background:#1e1e1e; color:#aaa; border:1.5px solid #444;
  border-radius:8px; padding:6px 10px; font-size:12px; cursor:pointer;
}
.tbtn.on { background:#1e1e0a; color:#f5c518; border-color:#f5c518; }
/* Status */
#status {
  text-align:center; font-size:12px; color:#888;
  margin-top:5px; min-height:18px; letter-spacing:0.4px;
}
/* Preview */
#previewBox {
  margin-top:10px; text-align:center; display:none;
}
#previewImg {
  max-width:100%; border-radius:8px; border:2px solid #f5c518;
}
#previewBox p { font-size:11px; color:#aaa; margin:5px 0; }
#savedMsg { font-size:13px; color:#00e676; margin:6px 0; font-weight:700; }
#retakeBtn {
  width:100%; background:#1e1e1e; color:#f5c518; border:1.5px solid #f5c518;
  border-radius:8px; padding:10px; font-size:13px; font-weight:700;
  cursor:pointer; margin-top:6px;
}
</style>
</head>
<body>
<div id="wrap">
  <video id="video" autoplay playsinline muted></video>
  <div id="countdownOverlay"><span id="countdownNum">3</span></div>
  <div id="flash"></div>
</div>

<div id="motionBar"><div id="motionFill"></div></div>

<div id="controls">
  <button class="tbtn on" id="autoBtn" onclick="toggleAuto()">🤏 Auto Snap</button>
  <button id="captureBtn" onclick="startCapture()">📸</button>
  <button class="tbtn" id="timerBtn" onclick="toggleTimer()">⏱️ Timer 3s</button>
</div>
<div id="status">Memulai kamera...</div>

<div id="previewBox">
  <p id="savedMsg">✅ Foto tersimpan otomatis!</p>
  <img id="previewImg" src="" alt="preview">
  <button id="retakeBtn" onclick="retake()">🔄 Ambil Ulang Foto</button>
</div>

<script>
const video     = document.getElementById('video');
const flash     = document.getElementById('flash');
const motionFill= document.getElementById('motionFill');
const cdOverlay = document.getElementById('countdownOverlay');
const cdNum     = document.getElementById('countdownNum');
const statusEl  = document.getElementById('status');
const previewBox= document.getElementById('previewBox');
const previewImg= document.getElementById('previewImg');

let autoSnap   = true;   // auto snap on motion
let timerMode  = false;  // manual 3s timer before snap
let capturing  = false;  // countdown in progress
let previewMode= false;
let capturedUrl= null;

// ── Toggle buttons ────────────────────────────────────────────────────────────
function toggleAuto() {
  autoSnap = !autoSnap;
  document.getElementById('autoBtn').classList.toggle('on', autoSnap);
  if (!autoSnap) { motionFill.style.width = '0%'; }
  statusEl.textContent = autoSnap
    ? '🤏 Auto snap aktif — gerakkan tangan!'
    : 'Manual mode — tap 📸 untuk foto';
}
function toggleTimer() {
  timerMode = !timerMode;
  document.getElementById('timerBtn').classList.toggle('on', timerMode);
  statusEl.textContent = timerMode ? '⏱️ Timer 3s aktif' : 'Timer off';
}

// ── Camera ────────────────────────────────────────────────────────────────────
navigator.mediaDevices.getUserMedia({
  video:{ facingMode:'user', width:{ideal:1280}, height:{ideal:720} },
  audio:false
}).then(stream => {
  video.srcObject = stream;
  video.onloadedmetadata = () => {
    initMotion();
    statusEl.textContent = '🤏 Auto snap aktif — gerakkan tangan!';
  };
}).catch(() => {
  statusEl.textContent = '❌ Kamera tidak dapat diakses';
});

// ── Motion detection ──────────────────────────────────────────────────────────
let prevFrame   = null;
let motionScore = 0;
let motionHoldFrames = 0;     // frames motion stays high
const MOTION_THRESHOLD = 18;  // pixel diff threshold per channel
const MOTION_TRIGGER   = 0.06; // 6% of pixels must move
const HOLD_FRAMES      = 8;   // frames motion must persist before trigger

const motionCanvas = document.createElement('canvas');
const motionCtx    = motionCanvas.getContext('2d', { willReadFrequently:true });
const SAMPLE_W = 160, SAMPLE_H = 90; // low-res for perf

function initMotion() {
  motionCanvas.width  = SAMPLE_W;
  motionCanvas.height = SAMPLE_H;
  requestAnimationFrame(motionLoop);
}

function motionLoop() {
  requestAnimationFrame(motionLoop);
  if (previewMode || capturing) return;
  if (video.readyState < 2) return;

  // Draw current frame low-res
  motionCtx.drawImage(video, 0, 0, SAMPLE_W, SAMPLE_H);
  const curr = motionCtx.getImageData(0, 0, SAMPLE_W, SAMPLE_H).data;

  if (!prevFrame) {
    prevFrame = new Uint8ClampedArray(curr);
    return;
  }

  // Compare frames
  let diffPixels = 0;
  const total = SAMPLE_W * SAMPLE_H;
  for (let i = 0; i < curr.length; i += 4) {
    const dr = Math.abs(curr[i]   - prevFrame[i]);
    const dg = Math.abs(curr[i+1] - prevFrame[i+1]);
    const db = Math.abs(curr[i+2] - prevFrame[i+2]);
    if ((dr + dg + db) / 3 > MOTION_THRESHOLD) diffPixels++;
  }

  // Copy current to prev
  prevFrame.set(curr);

  const ratio = diffPixels / total;
  // Smooth score
  motionScore = motionScore * 0.7 + ratio * 0.3;
  motionFill.style.width = Math.min(100, motionScore * 800) + '%';

  // Color bar: green when triggered, yellow otherwise
  if (motionScore > MOTION_TRIGGER) {
    motionFill.style.background = '#00e676';
    motionHoldFrames++;
  } else {
    motionFill.style.background = '#f5c518';
    motionHoldFrames = 0;
  }

  // Trigger auto snap
  if (autoSnap && motionHoldFrames >= HOLD_FRAMES && !capturing) {
    motionHoldFrames = 0;
    startCapture();
  }

  // Status
  if (!capturing) {
    if (motionScore > MOTION_TRIGGER) {
      statusEl.textContent = '✋ Gerakan terdeteksi...';
    } else {
      statusEl.textContent = autoSnap
        ? '🤏 Gerakkan tangan untuk snap otomatis'
        : '📸 Tap tombol untuk foto';
    }
  }
}

// ── Capture flow ──────────────────────────────────────────────────────────────
function startCapture() {
  if (capturing || previewMode) return;
  if (timerMode) {
    runCountdown(3);
  } else {
    doSnap();
  }
}

function runCountdown(n) {
  if (n <= 0) { doSnap(); return; }
  capturing = true;
  cdNum.textContent = n;
  cdOverlay.style.opacity = '1';
  cdNum.style.transform = 'scale(1.3)';
  cdNum.style.transition = 'transform 0.15s';
  setTimeout(() => { cdNum.style.transform = 'scale(1)'; }, 150);
  statusEl.textContent = `📸 Bersiap... ${n}`;
  setTimeout(() => runCountdown(n - 1), 1000);
}

function doSnap() {
  cdOverlay.style.opacity = '0';
  capturing = false;

  // Flash
  flash.style.transition = '';
  flash.style.opacity = '1';
  setTimeout(() => {
    flash.style.transition = 'opacity 0.3s';
    flash.style.opacity = '0';
  }, 60);

  // Capture to canvas
  const cap = document.createElement('canvas');
  cap.width  = video.videoWidth  || 1280;
  cap.height = video.videoHeight || 720;
  const cc = cap.getContext('2d');
  // Mirror to match selfie preview
  cc.translate(cap.width, 0);
  cc.scale(-1, 1);
  cc.drawImage(video, 0, 0, cap.width, cap.height);

  capturedUrl = cap.toDataURL('image/jpeg', 0.93);

  // Langsung kirim ke Streamlit — auto simpan
  window.parent.postMessage({ type:'PHOTO_CAPTURED', dataUrl: capturedUrl }, '*');

  // Tampilkan preview + tombol ambil ulang
  previewImg.src = capturedUrl;
  previewBox.style.display = 'block';
  previewMode = true;
  statusEl.textContent = '✅ Foto tersimpan otomatis!';
}

function retake() {
  capturedUrl = null;
  previewBox.style.display = 'none';
  previewMode = false;
  prevFrame   = null;
  statusEl.textContent = '🤏 Gerakkan tangan untuk snap otomatis';
}
</script>
</body>
</html>"""

# ── Session state ──────────────────────────────────────────────────────────────
if "photo" not in st.session_state:
    st.session_state.photo = None
if "selected_tpl" not in st.session_state:
    st.session_state.selected_tpl = "pas_foto_2x3"
if "selected_filter" not in st.session_state:
    st.session_state.selected_filter = "normal"
if "collage_photos" not in st.session_state:
    st.session_state.collage_photos = []
if "collage_layout" not in st.session_state:
    st.session_state.collage_layout = "grid"
if "collage_filter" not in st.session_state:
    st.session_state.collage_filter = "normal"
if "studio_name" not in st.session_state:
    st.session_state.studio_name = "oh! shoot"
if "studio_sub" not in st.session_state:
    st.session_state.studio_sub = "NEW WAVE PHOTO STUDIO"

# ── UI ─────────────────────────────────────────────────────────────────────────
st.markdown("# 📸 Photo Booth Cetak")
st.divider()

tab_photobooth, tab_collage = st.tabs(["📸 Photo Booth", "🖼️ Collage"])

with tab_photobooth:
 st.markdown("*Ambil foto → Pilih tema → Pilih template → Download PDF / JPG*")

 col_left, col_right = st.columns([1, 1.4], gap="large")

# ── LEFT: Foto input + Filter + Template picker ───────────────────────────────
with col_left:
    st.markdown("### 1. Ambil / Upload Foto")

    input_mode = st.radio("Sumber foto", ["📷 Webcam", "📁 Upload File"], horizontal=True, label_visibility="collapsed")

    if input_mode == "📷 Webcam":
        # ── AR Camera preview ─────────────────────────────────────────────────
        components.html(get_ar_camera_html(), height=620, scrolling=False)

        # ── JS bridge: receive postMessage from AR iframe ─────────────────────
        # Uses a reliable relay: AR iframe → parent postMessage →
        # sibling relay iframe → Streamlit session via URL hash trick
        components.html("""
        <script>
        window.addEventListener('message', function(e) {
          if (!e.data || e.data.type !== 'PHOTO_CAPTURED') return;
          const dataUrl = e.data.dataUrl;
          // Store in sessionStorage so Streamlit can poll it
          try { sessionStorage.setItem('photo_captured', dataUrl); } catch(err){}
          // Also try injecting into the st.text_area below
          try {
            const allTA = window.parent.document.querySelectorAll('textarea');
            for (const ta of allTA) {
              if (ta.getAttribute('aria-label') === 'cam_bridge_ta') {
                const nv = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value');
                nv.set.call(ta, dataUrl);
                ta.dispatchEvent(new Event('input', {bubbles:true}));
                break;
              }
            }
          } catch(err) {}
        });
        </script>
        """, height=0)

        raw_b64 = st.text_area("cam_bridge_ta", key="cam_bridge_ta",
                                label_visibility="collapsed", height=68)
        if raw_b64 and raw_b64.strip().startswith("data:image"):
            try:
                header, b64data = raw_b64.strip().split(",", 1)
                img_bytes = base64.b64decode(b64data)
                st.session_state.photo = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                st.success("✅ Foto dari kamera berhasil disimpan!")
            except Exception:
                pass
            st.session_state["cam_bridge"] = ""
            st.success("✅ Foto berhasil diambil!")
            st.rerun()
    else:
        uploaded = st.file_uploader(
            "Upload foto (JPG, PNG)",
            type=["jpg", "jpeg", "png", "webp"],
            label_visibility="visible",
        )
        if uploaded:
            # File upload: tidak perlu mirror, sudah benar orientasinya
            st.session_state.photo = Image.open(uploaded)
            st.success("✅ Foto berhasil diupload!")

    if st.session_state.photo:
        with st.expander("👁️ Lihat foto asli", expanded=False):
            st.image(st.session_state.photo, use_container_width=True)

    # ── FILTER / TEMA PICKER ─────────────────────────────────────────────────
    if st.session_state.photo is not None:
        st.divider()
        st.markdown("### 2. Pilih Tema / Filter")

        photo = st.session_state.photo
        current_filter = st.session_state.selected_filter
        filter_keys = list(FILTERS.keys())

        # Tampilkan thumbnail grid per 4 kolom
        THUMB_COLS = 4
        for row_start in range(0, len(filter_keys), THUMB_COLS):
            row_keys = filter_keys[row_start : row_start + THUMB_COLS]
            cols_thumb = st.columns(THUMB_COLS)
            for i, fkey in enumerate(row_keys):
                fdata = FILTERS[fkey]
                is_active = (current_filter == fkey)
                thumb = make_filter_thumb(photo, fkey, size=100)

                with cols_thumb[i]:
                    st.image(thumb, use_container_width=True)
                    if st.button(
                        f"{fdata['icon']}",
                        key=f"filter_{fkey}",
                        use_container_width=True,
                        type="primary" if is_active else "secondary",
                        help=f"{fdata['name']} — {fdata['desc']}",
                    ):
                        st.session_state.selected_filter = fkey
                        st.rerun()
                    label_html = f'<div class="{"filter-active" if is_active else "filter-label"}">{fdata["name"]}</div>'
                    st.markdown(label_html, unsafe_allow_html=True)

        # Show active filter info
        active_f = FILTERS[current_filter]
        st.markdown(f"""
        <div class="info-box">
        Filter aktif: <b>{active_f['icon']} {active_f['name']}</b> — {active_f['desc']}
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### 3. Pilih Template" if st.session_state.photo else "### 2. Pilih Template")

    tpl_keys = list(TEMPLATES.keys())
    for i in range(0, len(tpl_keys), 2):
        c1, c2 = st.columns(2)
        for j, col in enumerate([c1, c2]):
            if i + j < len(tpl_keys):
                key = tpl_keys[i + j]
                tpl = TEMPLATES[key]
                selected = st.session_state.selected_tpl == key
                with col:
                    if st.button(
                        f"{tpl['icon']} {tpl['name']}\n{tpl['desc']}",
                        key=f"tpl_{key}",
                        use_container_width=True,
                        type="primary" if selected else "secondary",
                    ):
                        st.session_state.selected_tpl = key
                        st.rerun()

# ── RIGHT: Preview + Download ──────────────────────────────────────────────────
with col_right:
    st.markdown("### 4. Preview & Download" if st.session_state.photo else "### 3. Preview & Download")

    tpl_key = st.session_state.selected_tpl
    tpl = TEMPLATES[tpl_key]
    current_filter = st.session_state.selected_filter
    active_f = FILTERS[current_filter]

    st.markdown(f"""
    <div class="info-box">
    <b>{tpl['icon']} {tpl['name']}</b> &nbsp;|&nbsp;
    Ukuran foto: <b>{tpl['w']}×{tpl['h']} cm</b> &nbsp;|&nbsp;
    Susunan: <b>{tpl['cols']}×{tpl['rows']}</b> &nbsp;|&nbsp;
    Tema: <b>{active_f['icon']} {active_f['name']}</b>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.photo is None:
        st.markdown("""
        <div style="background:#1a1a1a; border:2px dashed #444; border-radius:12px;
                    height:340px; display:flex; align-items:center; justify-content:center;
                    color:#666; font-size:16px; text-align:center; padding:20px;">
            📷<br><br>Belum ada foto.<br>Ambil atau upload foto dulu di panel kiri.
        </div>
        """, unsafe_allow_html=True)
    else:
        # Studio name inputs (only show for studio_print)
        if tpl_key == "studio_print":
            scol1, scol2 = st.columns(2)
            with scol1:
                sn = st.text_input("🏪 Nama Studio", value=st.session_state.studio_name,
                                   key="studio_name_input", max_chars=30)
                st.session_state.studio_name = sn
            with scol2:
                ss = st.text_input("📝 Tagline", value=st.session_state.studio_sub,
                                   key="studio_sub_input", max_chars=40)
                st.session_state.studio_sub = ss

        with st.spinner("⚙️ Membuat layout..."):
            if tpl_key == "studio_print":
                sheet = build_studio_sheet(
                    st.session_state.photo, tpl, current_filter,
                    st.session_state.studio_name,
                    st.session_state.studio_sub,
                )
            else:
                sheet = build_sheet(st.session_state.photo, tpl, current_filter)
            thumb = preview_thumbnail(sheet, max_px=700)

        # Before/After toggle
        show_before = st.toggle("👁️ Lihat tanpa filter (before/after)", value=False)

        if show_before:
            if tpl_key == "studio_print":
                sheet_before = build_studio_sheet(
                    st.session_state.photo, tpl, "normal",
                    st.session_state.studio_name, st.session_state.studio_sub)
            else:
                sheet_before = build_sheet(st.session_state.photo, tpl, "normal")
            thumb_before = preview_thumbnail(sheet_before, max_px=700)
            bcol1, bcol2 = st.columns(2)
            with bcol1:
                st.markdown('<div class="preview-label">BEFORE (Normal)</div>', unsafe_allow_html=True)
                st.image(thumb_before, use_container_width=True)
            with bcol2:
                st.markdown(f'<div class="preview-label">AFTER ({active_f["name"]})</div>', unsafe_allow_html=True)
                st.image(thumb, use_container_width=True)
        else:
            st.markdown(f'<div class="preview-label">PREVIEW — {active_f["icon"]} {active_f["name"]}</div>', unsafe_allow_html=True)
            st.image(thumb, use_container_width=True, caption=f"{tpl['name']} · {active_f['name']} — siap cetak di kertas foto A4")

        st.divider()
        st.markdown("### 5. Download")

        d1, d2 = st.columns(2)

        with d1:
            jpg_bytes = sheet_to_bytes(sheet, "JPEG")
            st.download_button(
                label="⬇️ Download JPG",
                data=jpg_bytes,
                file_name=f"photobooth_{tpl_key}_{current_filter}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
                mime="image/jpeg",
                use_container_width=True,
            )

        with d2:
            pdf_bytes = sheet_to_pdf(sheet, tpl)
            st.download_button(
                label="⬇️ Download PDF",
                data=pdf_bytes,
                file_name=f"photobooth_{tpl_key}_{current_filter}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        st.divider()
        if st.button("📦 Download SEMUA Template (ZIP)", use_container_width=True):
            with st.spinner("Membuat semua template..."):
                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    for k, t in TEMPLATES.items():
                        s = build_sheet(st.session_state.photo, t, current_filter)
                        jpg = sheet_to_bytes(s, "JPEG")
                        pdf = sheet_to_pdf(s, t)
                        zf.writestr(f"{k}_{current_filter}.jpg", jpg)
                        zf.writestr(f"{k}_{current_filter}.pdf", pdf)
                zip_buf.seek(0)
            st.download_button(
                label="⬇️ Download ZIP",
                data=zip_buf.getvalue(),
                file_name=f"photobooth_all_{current_filter}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",
                use_container_width=True,
            )


with tab_collage:
    st.markdown("*Upload beberapa foto → Pilih layout → Atur tema → Download*")

    # ── Collage helpers ───────────────────────────────────────────────────────
    COLLAGE_LAYOUTS = {
        "grid":    {"name": "Grid",          "icon": "⊞",  "desc": "Kotak-kotak sama besar"},
        "magazine":{"name": "Layout Majalah","icon": "📰", "desc": "1 foto besar + beberapa kecil"},
        "strip":   {"name": "Strip",         "icon": "🎞️", "desc": "Foto berjajar horizontal"},
        "mosaic":  {"name": "Mosaic",        "icon": "🔲", "desc": "Variasi ukuran acak"},
    }

    def build_collage_grid(photos, fkeys, canvas_w=2480, canvas_h=3508):
        """Grid: equal-size cells, auto cols/rows."""
        n = len(photos)
        if n == 0: return None
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)
        pad = 30
        cell_w = (canvas_w - pad*(cols+1)) // cols
        cell_h = (canvas_h - pad*(rows+1)) // rows
        sheet = Image.new("RGB", (canvas_w, canvas_h), (255,255,255))
        for i, (ph, fk) in enumerate(zip(photos, fkeys)):
            r, c = divmod(i, cols)
            x = pad + c*(cell_w+pad)
            y = pad + r*(cell_h+pad)
            cell = fit_crop(apply_filter(ph, fk), cell_w, cell_h)
            sheet.paste(cell, (x, y))
        return sheet

    def build_collage_magazine(photos, fkeys, canvas_w=2480, canvas_h=3508):
        """Magazine: first photo big top, rest small bottom row."""
        n = len(photos)
        if n == 0: return None
        pad = 30
        sheet = Image.new("RGB", (canvas_w, canvas_h), (240,240,240))
        if n == 1:
            big_h = canvas_h - pad*2
            cell = fit_crop(apply_filter(photos[0], fkeys[0]), canvas_w-pad*2, big_h)
            sheet.paste(cell, (pad, pad))
        else:
            big_h = int((canvas_h - pad*3) * 0.62)
            small_h = canvas_h - big_h - pad*3
            # big photo
            big = fit_crop(apply_filter(photos[0], fkeys[0]), canvas_w-pad*2, big_h)
            sheet.paste(big, (pad, pad))
            # small row
            small_n = n - 1
            small_w = (canvas_w - pad*(small_n+1)) // small_n
            for i, (ph, fk) in enumerate(zip(photos[1:], fkeys[1:])):
                x = pad + i*(small_w+pad)
                y = big_h + pad*2
                cell = fit_crop(apply_filter(ph, fk), small_w, small_h)
                sheet.paste(cell, (x, y))
        return sheet

    def build_collage_strip(photos, fkeys, canvas_w=3508, canvas_h=2480):
        """Horizontal strip — landscape."""
        n = len(photos)
        if n == 0: return None
        pad = 30
        cell_w = (canvas_w - pad*(n+1)) // n
        cell_h = canvas_h - pad*2
        sheet = Image.new("RGB", (canvas_w, canvas_h), (20,20,20))
        for i, (ph, fk) in enumerate(zip(photos, fkeys)):
            x = pad + i*(cell_w+pad)
            cell = fit_crop(apply_filter(ph, fk), cell_w, cell_h)
            sheet.paste(cell, (x, pad))
        return sheet

    def build_collage_mosaic(photos, fkeys, canvas_w=2480, canvas_h=3508):
        """Mosaic: varied sizes based on index pattern."""
        n = len(photos)
        if n == 0: return None
        pad = 20
        sheet = Image.new("RGB", (canvas_w, canvas_h), (255,255,255))

        # Predefined mosaic slot ratios (x%, y%, w%, h%) for up to 6 photos
        SLOTS = [
            [(0,0,1,1)],                                           # 1 photo
            [(0,0,.5,1),(.5,0,.5,1)],                             # 2
            [(0,0,.6,1),(.6,0,.4,.5),(.6,.5,.4,.5)],             # 3
            [(0,0,.5,.6),(.5,0,.5,.6),(0,.6,.5,.4),(.5,.6,.5,.4)], # 4
            [(0,0,.6,.55),(.6,0,.4,.55),(0,.55,.33,.45),(.33,.55,.34,.45),(.67,.55,.33,.45)], # 5
            [(0,0,.5,.5),(.5,0,.5,.5),(0,.5,.33,.5),(.33,.5,.34,.5),(.67,.5,.33,.5),(.0,.5,.33,.5)], # 6
        ]
        slots = SLOTS[min(n,6)-1]
        uw = canvas_w - pad
        uh = canvas_h - pad

        for i, (ph, fk) in enumerate(zip(photos[:6], fkeys[:6])):
            if i >= len(slots): break
            sx, sy, sw, sh = slots[i]
            x = int(pad/2 + sx*uw)
            y = int(pad/2 + sy*uh)
            w = max(1, int(sw*uw - pad))
            h = max(1, int(sh*uh - pad))
            cell = fit_crop(apply_filter(ph, fk), w, h)
            sheet.paste(cell, (x, y))
        return sheet

    def build_collage(photos, fkeys, layout):
        if layout == "grid":     return build_collage_grid(photos, fkeys)
        if layout == "magazine": return build_collage_magazine(photos, fkeys)
        if layout == "strip":    return build_collage_strip(photos, fkeys)
        if layout == "mosaic":   return build_collage_mosaic(photos, fkeys)
        return None

    # ── Collage UI ────────────────────────────────────────────────────────────
    cc_left, cc_right = st.columns([1, 1.4], gap="large")

    with cc_left:
        st.markdown("### 1. Upload Foto (maks 6)")
        uploaded_collage = st.file_uploader(
            "Upload foto untuk collage",
            type=["jpg","jpeg","png","webp"],
            accept_multiple_files=True,
            key="collage_uploader",
            label_visibility="visible",
        )
        if uploaded_collage:
            new_photos = [Image.open(f).convert("RGB") for f in uploaded_collage[:6]]
            st.session_state.collage_photos = new_photos
            st.success(f"✅ {len(new_photos)} foto diupload!")

        if st.session_state.collage_photos:
            st.markdown(f"**{len(st.session_state.collage_photos)} foto aktif**")
            thumb_cols = st.columns(min(len(st.session_state.collage_photos), 3))
            for i, ph in enumerate(st.session_state.collage_photos):
                with thumb_cols[i % 3]:
                    t = ph.copy()
                    t.thumbnail((120, 120))
                    st.image(t, use_container_width=True, caption=f"Foto {i+1}")

            if st.button("🗑️ Hapus Semua Foto", key="clear_collage"):
                st.session_state.collage_photos = []
                st.rerun()

        st.divider()
        st.markdown("### 2. Pilih Layout")
        for lk, lv in COLLAGE_LAYOUTS.items():
            is_sel = st.session_state.collage_layout == lk
            if st.button(
                f"{lv['icon']} {lv['name']} — {lv['desc']}",
                key=f"clayout_{lk}",
                use_container_width=True,
                type="primary" if is_sel else "secondary",
            ):
                st.session_state.collage_layout = lk
                st.rerun()

        st.divider()
        st.markdown("### 3. Tema per Foto")
        st.caption("Setiap foto bisa punya filter berbeda, atau pakai satu filter untuk semua.")

        # Global filter
        global_fk = st.selectbox(
            "Filter semua foto sekaligus",
            options=list(FILTERS.keys()),
            format_func=lambda k: f"{FILTERS[k]['icon']} {FILTERS[k]['name']}",
            key="collage_global_filter",
        )
        apply_all = st.button("✅ Terapkan ke Semua", key="apply_all_filter")

        n_photos = len(st.session_state.collage_photos)
        if "collage_fkeys" not in st.session_state or len(st.session_state.collage_fkeys) != n_photos:
            st.session_state.collage_fkeys = ["normal"] * n_photos
        if apply_all:
            st.session_state.collage_fkeys = [global_fk] * n_photos
            st.rerun()

        if n_photos > 0:
            st.markdown("**Filter individual:**")
            for i in range(n_photos):
                fk = st.selectbox(
                    f"Foto {i+1}",
                    options=list(FILTERS.keys()),
                    index=list(FILTERS.keys()).index(st.session_state.collage_fkeys[i]),
                    format_func=lambda k: f"{FILTERS[k]['icon']} {FILTERS[k]['name']}",
                    key=f"cfk_{i}",
                )
                st.session_state.collage_fkeys[i] = fk

    with cc_right:
        st.markdown("### 4. Preview & Download")

        if not st.session_state.collage_photos:
            st.markdown("""
            <div style="background:#1a1a1a; border:2px dashed #444; border-radius:12px;
                        height:340px; display:flex; align-items:center; justify-content:center;
                        color:#666; font-size:16px; text-align:center; padding:20px;">
                🖼️<br><br>Belum ada foto.<br>Upload minimal 1 foto dulu di panel kiri.
            </div>
            """, unsafe_allow_html=True)
        else:
            layout_info = COLLAGE_LAYOUTS[st.session_state.collage_layout]
            st.markdown(f"""
            <div class="info-box">
            <b>{layout_info['icon']} {layout_info['name']}</b> &nbsp;|&nbsp;
            {len(st.session_state.collage_photos)} foto &nbsp;|&nbsp;
            Resolusi: <b>300 DPI</b>
            </div>
            """, unsafe_allow_html=True)

            fkeys = st.session_state.get("collage_fkeys", ["normal"]*len(st.session_state.collage_photos))

            with st.spinner("⚙️ Membuat collage..."):
                collage_sheet = build_collage(
                    st.session_state.collage_photos,
                    fkeys,
                    st.session_state.collage_layout,
                )

            if collage_sheet:
                thumb_c = preview_thumbnail(collage_sheet, max_px=700)
                st.markdown('<div class="preview-label">PREVIEW COLLAGE</div>', unsafe_allow_html=True)
                st.image(thumb_c, use_container_width=True,
                         caption=f"{layout_info['name']} — {len(st.session_state.collage_photos)} foto")

                st.divider()
                st.markdown("### 5. Download")
                dc1, dc2 = st.columns(2)
                with dc1:
                    cjpg = sheet_to_bytes(collage_sheet, "JPEG")
                    st.download_button(
                        label="⬇️ Download JPG",
                        data=cjpg,
                        file_name=f"collage_{st.session_state.collage_layout}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
                        mime="image/jpeg",
                        use_container_width=True,
                    )
                with dc2:
                    cpdf = sheet_to_pdf(collage_sheet, {"name": f"Collage {layout_info['name']}", "w":21,"h":29.7,"cols":1,"rows":1})
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=cpdf,
                        file_name=f"collage_{st.session_state.collage_layout}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )


# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style="text-align:center; color:#555; font-size:12px;">
Photo Booth Cetak — Output resolusi 300 DPI, siap cetak di kertas foto A4<br>
Template: Pas Foto 2×3 · 3×4 · 4×6 · Strip Polaroid · Photo Booth Grid · Film Strip · Wallet Print<br>
Filter: Normal · Hitam Putih · Vintage · Cool Blue · Golden Hour · Faded · Vivid · Sepia · Noir · Pastel · Neon · Film Grain
</div>
""", unsafe_allow_html=True)

# ── Tombol Interaktif Kejutan untuk Zizah ─────────────────────────────────────────
if st.button("👉 Klik bentar, Zah..."):
    
    # 1. Mainkan Efek Suara Gemericik Air Kali (Autoplay Aktif)
    st.audio("https://www.soundjay.com/nature/sounds/river-1.mp3", format="audio/mp3", autoplay=True)
    
    # 2. Tampilkan Gambar Screenshot Chat HRD Polos
    st.image(
        "https://i.postimg.cc/2Sc9t3vH/Screenshot-20260604-150953.png", 
        use_container_width=True
    )
    
    st.write("")
    
    # 3. Tampilkan Kalimat Polos Cerita Lu
    st.write("Zah, di atas itu bukti obrolan gua sama Pak Ageng (Recruiter HTC Global Services). Gua sengaja pajang di sini biar lu tahu semuanya secara terbuka. Gua rela ngambil langkah sejauh ini, nembus tantangan baru ke Jakarta, karena gua pengen nyari finansial yang lebih baik. Gua pengen berjuang di tempat yang bener-bener ngehargai hasil kerja keras gua.")
    
    st.write("Tapi dari skrip ini gua mau lu tahu, lu gak usah khawatir, gua gabakal lupain lu, Zah. Gua kagum banget sama lu. Lu itu wanita mandiri, tipe cewek yang susah buat dideketin, dan jujur... cewek kayak lu yang emang gua cari selama ini.")
    
    st.write("Sekarang bukannya gua menghilang atau ngejauh. Tapi setiap kali lu bales DM gua, gua sengaja mikir berkali-kali dulu mau bales apa. Biar apa? Biar lu gak marah, dan biar obrolan kita tuh bisa nambah asik ke depannya.")
    
    # Bagian cerita apes yang udah disinkronkan:
    st.write("Inget masalah kemarin? Apesnya lu gara-gara salah transfer, eh apesnya gua juga pas ngirim matcha malah nyangkut ditahan di security wkwk. Gara-gara drama sama-sama apes itu, gua mikir... emang kita kayaknya gabisa dipisah-pisahin, Zah. ❤️")
    
    st.write("Nanti gua di Jakarta sendirian, tapi entah kenapa di pikiran gua nama lu terus yang lewat. Nomor gua masih sama kok, aktif terus 24 jam. Jadi kalau lu mau ninggalin pesan di aplikasi ini atau mau ngabarin langsung, pintu gua selalu kebuka. Tenang aja, urusan matcha yang gagal kemarin tetep bakal gua ganti dan kirim lagi nanti, ntar gua DM lu lagi ya, wkwk.")
    
    st.write("Doain gua ya, kalo masih ada kesempatan gua bakal prioritasin lu jadi nomor satu, tapi kalo bukan lu gua berdoa semoga yang gak itu tetap lu wkwkw")
