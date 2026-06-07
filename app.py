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
    "frame_classic": {
        "name": "Classic Polaroid",
        "w": 8.0, "h": 9.5,
        "cols": 1, "rows": 1,
        "desc": "1 foto\nFrame polaroid putih klasik",
        "icon": "🟦",
        "bg_color": (255, 255, 255),
        "border": 0,
        "style": "frame_classic",
    },
    "frame_strip3": {
        "name": "Strip Frame 3",
        "w": 6.5, "h": 5.0,
        "cols": 1, "rows": 3,
        "desc": "1×3 strip\nFrame putih soft polaroid",
        "icon": "🎞️",
        "bg_color": (255, 255, 255),
        "border": 0,
        "style": "frame_strip3",
    },
    "frame_grid4": {
        "name": "Grid Frame 2×2",
        "w": 7.0, "h": 7.0,
        "cols": 2, "rows": 2,
        "desc": "2×2 grid\nFrame putih aesthetic",
        "icon": "⊞",
        "bg_color": (255, 255, 255),
        "border": 0,
        "style": "frame_grid4",
    },
    "frame_pink": {
        "name": "Pink Girly",
        "w": 8.0, "h": 9.5,
        "cols": 1, "rows": 1,
        "desc": "1 foto\nFrame pink pastel cute",
        "icon": "🌸",
        "bg_color": (255, 220, 230),
        "border": 0,
        "style": "frame_pink",
    },
    "frame_dark": {
        "name": "Dark Aesthetic",
        "w": 8.0, "h": 9.5,
        "cols": 1, "rows": 1,
        "desc": "1 foto\nFrame hitam moody",
        "icon": "🖤",
        "bg_color": (20, 20, 20),
        "border": 0,
        "style": "frame_dark",
    },
    "romance_filmstrip": {
        "name": "💕 Filmstrip Memories",
        "w": 5.5, "h": 4.0,
        "cols": 3, "rows": 1,
        "desc": "3 foto horizontal\nFilmstrip romantis",
        "icon": "🎞️",
        "bg_color": (255, 245, 240),
        "border": 0,
        "style": "romance_filmstrip",
    },
    "romance_destined": {
        "name": "💗 Destined Together",
        "w": 7.0, "h": 9.5,
        "cols": 1, "rows": 1,
        "desc": "1 foto\nFrame ornamen romantis",
        "icon": "💗",
        "bg_color": (255, 248, 245),
        "border": 0,
        "style": "romance_destined",
    },
    "romance_keepsake": {
        "name": "💛 Keepsake",
        "w": 10.0, "h": 6.0,
        "cols": 3, "rows": 1,
        "desc": "3 foto horizontal\nGaya keepsake vintage",
        "icon": "💛",
        "bg_color": (255, 250, 235),
        "border": 0,
        "style": "romance_keepsake",
    },
    "romance_lovenotes": {
        "name": "💌 Love Notes",
        "w": 7.5, "h": 9.5,
        "cols": 1, "rows": 1,
        "desc": "1 foto\nAmplop surat cinta",
        "icon": "💌",
        "bg_color": (255, 248, 240),
        "border": 0,
        "style": "romance_lovenotes",
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

def build_frame_sheet(photo: Image.Image, tpl: dict, filter_key: str) -> Image.Image:
    """Build polaroidbooth-style framed print with decorative borders."""
    style = tpl["style"]
    bg    = tpl["bg_color"]
    DPI_  = 300
    CM_   = DPI_ / 2.54

    def cm(v): return int(v * CM_)

    filtered = apply_filter(photo, filter_key)

    if style == "frame_classic":
        # White polaroid: thick bottom border, thin sides/top
        pw, ph = cm(tpl["w"]), cm(tpl["h"])
        pad_side   = cm(0.6)
        pad_top    = cm(0.6)
        pad_bottom = cm(1.8)  # classic polaroid thick bottom
        inner_w = pw - pad_side * 2
        inner_h = ph - pad_top - pad_bottom
        cell = fit_crop(filtered, inner_w, inner_h)
        sheet = Image.new("RGB", (pw, ph), bg)
        sheet.paste(cell, (pad_side, pad_top))
        return sheet

    elif style == "frame_strip3":
        # 3 vertical strips with white frame each
        cols, rows = 1, 3
        pw = cm(tpl["w"])
        pad_side   = cm(0.5)
        pad_top    = cm(0.4)
        pad_bottom = cm(1.2)
        gap        = cm(0.35)
        cell_w = pw - pad_side * 2
        total_cell_h = cm(tpl["h"]) * rows
        sheet_h = pad_top + rows * (total_cell_h // rows) + gap * (rows - 1) * 2 + pad_bottom + cm(0.5)
        cell_h = (sheet_h - pad_top - pad_bottom - gap * (rows - 1)) // rows
        sheet = Image.new("RGB", (pw, sheet_h), bg)
        draw = ImageDraw.Draw(sheet)
        for i in range(rows):
            y = pad_top + i * (cell_h + gap)
            cell = fit_crop(filtered, cell_w, cell_h)
            # Thin shadow border
            draw.rectangle([pad_side-2, y-2, pad_side+cell_w+2, y+cell_h+2],
                           outline=(200,200,200), width=1)
            sheet.paste(cell, (pad_side, y))
        return sheet

    elif style == "frame_grid4":
        # 2x2 grid with white frame
        pw, ph = cm(tpl["w"] * 1.2), cm(tpl["h"] * 1.2)
        pad    = cm(0.55)
        gap    = cm(0.3)
        cell_w = (pw - pad * 2 - gap) // 2
        cell_h = (ph - pad * 2 - gap) // 2
        sheet = Image.new("RGB", (pw, ph), bg)
        draw = ImageDraw.Draw(sheet)
        for r in range(2):
            for c in range(2):
                x = pad + c * (cell_w + gap)
                y = pad + r * (cell_h + gap)
                cell = fit_crop(filtered, cell_w, cell_h)
                draw.rectangle([x-2, y-2, x+cell_w+2, y+cell_h+2],
                               outline=(210,210,210), width=1)
                sheet.paste(cell, (x, y))
        return sheet

    elif style == "frame_pink":
        pw, ph = cm(tpl["w"]), cm(tpl["h"])
        pad_side   = cm(0.7)
        pad_top    = cm(0.7)
        pad_bottom = cm(2.2)
        inner_w = pw - pad_side * 2
        inner_h = ph - pad_top - pad_bottom
        cell = fit_crop(filtered, inner_w, inner_h)
        sheet = Image.new("RGB", (pw, ph), bg)
        draw = ImageDraw.Draw(sheet)
        # Decorative dots border
        dot_col = (255, 170, 195)
        for i in range(0, pw, cm(0.6)):
            draw.ellipse([i-3, 3, i+3, 9], fill=dot_col)
            draw.ellipse([i-3, ph-9, i+3, ph-3], fill=dot_col)
        for i in range(0, ph, cm(0.6)):
            draw.ellipse([3, i-3, 9, i+3], fill=dot_col)
            draw.ellipse([pw-9, i-3, pw-3, i+3], fill=dot_col)
        sheet.paste(cell, (pad_side, pad_top))
        # Hearts deco at bottom
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", cm(0.45))
        except Exception:
            font = ImageFont.load_default()
        hearts = "♥  ♥  ♥  ♥  ♥"
        bbox = draw.textbbox((0,0), hearts, font=font)
        tx = (pw - (bbox[2]-bbox[0])) // 2
        ty = ph - pad_bottom // 2 - (bbox[3]-bbox[1]) // 2
        draw.text((tx, ty), hearts, fill=(220, 100, 140), font=font)
        return sheet

    elif style == "frame_dark":
        pw, ph = cm(tpl["w"]), cm(tpl["h"])
        pad_side   = cm(0.6)
        pad_top    = cm(0.6)
        pad_bottom = cm(1.8)
        inner_w = pw - pad_side * 2
        inner_h = ph - pad_top - pad_bottom
        cell = fit_crop(filtered, inner_w, inner_h)
        sheet = Image.new("RGB", (pw, ph), bg)
        draw = ImageDraw.Draw(sheet)
        # Gold thin border
        draw.rectangle([pad_side-4, pad_top-4,
                         pad_side+inner_w+4, pad_top+inner_h+4],
                        outline=(180, 140, 0), width=2)
        sheet.paste(cell, (pad_side, pad_top))
        # Bottom text
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", cm(0.32))
        except Exception:
            font = ImageFont.load_default()
        label = "✦  CAPTURED  ✦"
        bbox = draw.textbbox((0,0), label, font=font)
        tx = (pw - (bbox[2]-bbox[0])) // 2
        ty = ph - pad_bottom // 2 - (bbox[3]-bbox[1]) // 2
        draw.text((tx, ty), label, fill=(180, 140, 0), font=font)
        return sheet

    # ── Romance frames ────────────────────────────────────────────────────────
    elif style == "romance_filmstrip":
        # Filmstrip Memories: 3 photos horizontal, film border, floral accents text
        DPI_ = 300; CM_ = DPI_ / 2.54
        def cm2(v): return int(v * CM_)
        pw = cm2(18.0); ph = cm2(9.0)
        bg_col = (255, 245, 240)
        sheet = Image.new("RGB", (pw, ph), bg_col)
        draw = ImageDraw.Draw(sheet)

        # Film strip dark bar top and bottom
        strip_h = cm2(0.7)
        draw.rectangle([0, 0, pw, strip_h], fill=(80, 45, 25))
        draw.rectangle([0, ph - strip_h, pw, ph], fill=(80, 45, 25))

        # Film holes
        hole_w, hole_h = cm2(0.25), cm2(0.35)
        hole_y_top = (strip_h - hole_h) // 2
        hole_y_bot = ph - strip_h + (strip_h - hole_h) // 2
        for hx in range(cm2(0.3), pw - cm2(0.2), cm2(0.9)):
            draw.rounded_rectangle([hx, hole_y_top, hx+hole_w, hole_y_top+hole_h], radius=3, fill=(220, 195, 160))
            draw.rounded_rectangle([hx, hole_y_bot, hx+hole_w, hole_y_bot+hole_h], radius=3, fill=(220, 195, 160))

        # 3 photo cells
        cell_margin = cm2(0.4)
        cell_gap = cm2(0.3)
        content_y = strip_h + cm2(0.2)
        content_h = ph - strip_h * 2 - cm2(0.4)
        total_cell_w = pw - cell_margin * 2 - cell_gap * 2
        cell_w_each = total_cell_w // 3
        for i in range(3):
            cx = cell_margin + i * (cell_w_each + cell_gap)
            cell_img = fit_crop(filtered, cell_w_each, content_h)
            draw.rectangle([cx-2, content_y-2, cx+cell_w_each+2, content_y+content_h+2], outline=(120, 80, 50), width=2)
            sheet.paste(cell_img, (cx, content_y))

        # Bottom text area
        try:
            font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", cm2(0.38))
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", cm2(0.25))
        except Exception:
            font_big = font_small = ImageFont.load_default()

        texts = [("OUR FAV MOMENTS", (120, 50, 50), font_big, ph - strip_h + cm2(0.1)),]
        for txt, col, fnt, ty in texts:
            bbox = draw.textbbox((0,0), txt, font=fnt)
            tx = (pw - (bbox[2]-bbox[0])) // 2
            if ty + bbox[3] - bbox[1] < ph:
                draw.text((tx, ty), txt, fill=col, font=fnt)
        return sheet

    elif style == "romance_destined":
        DPI_ = 300; CM_ = DPI_ / 2.54
        def cm2(v): return int(v * CM_)
        pw, ph = cm2(tpl["w"]), cm2(tpl["h"])
        bg_col = (255, 248, 245)
        sheet = Image.new("RGB", (pw, ph), bg_col)
        draw = ImageDraw.Draw(sheet)

        # Ornate border — double rectangle with gold/rose
        brd = cm2(0.4)
        draw.rectangle([brd, brd, pw-brd, ph-brd], outline=(200, 160, 100), width=3)
        draw.rectangle([brd+8, brd+8, pw-brd-8, ph-brd-8], outline=(230, 180, 150), width=1)

        # Corner hearts
        for cx, cy in [(brd+cm2(0.1), brd+cm2(0.1)), (pw-brd-cm2(0.5), brd+cm2(0.1)),
                       (brd+cm2(0.1), ph-brd-cm2(0.5)), (pw-brd-cm2(0.5), ph-brd-cm2(0.5))]:
            draw.text((cx, cy), "♥", fill=(200, 100, 120), font=ImageFont.load_default())

        # Title top
        pad_top = cm2(1.2)
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf", cm2(0.5))
            font_sub   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", cm2(0.28))
        except Exception:
            font_title = font_sub = ImageFont.load_default()

        title = "Destined Together"
        tb = draw.textbbox((0,0), title, font=font_title)
        draw.text(((pw - (tb[2]-tb[0]))//2, cm2(0.5)), title, fill=(170, 80, 100), font=font_title)

        # Heart icon
        draw.text(((pw - cm2(0.5))//2, cm2(1.1)), "♥", fill=(200, 100, 120), font=font_title)

        # Photo cell
        pad_side = cm2(1.2)
        cell_top = cm2(2.0)
        cell_bot_margin = cm2(2.2)
        inner_w = pw - pad_side * 2
        inner_h = ph - cell_top - cell_bot_margin
        cell_img = fit_crop(filtered, inner_w, inner_h)
        draw.rectangle([pad_side-3, cell_top-3, pad_side+inner_w+3, cell_top+inner_h+3],
                       outline=(200, 160, 100), width=3)
        sheet.paste(cell_img, (pad_side, cell_top))

        # Bottom text
        bottom_y = cell_top + inner_h + cm2(0.2)
        sub_texts = ["US AGAINST THE WORLD", "♥", "FOR: [Crush Name]"]
        sub_cols  = [(130, 70, 80), (200, 100, 120), (120, 90, 100)]
        for i, (txt, col) in enumerate(zip(sub_texts, sub_cols)):
            fnt = font_sub if i != 1 else font_title
            bb = draw.textbbox((0,0), txt, font=fnt)
            tx = (pw - (bb[2]-bb[0])) // 2
            draw.text((tx, bottom_y + i*cm2(0.4)), txt, fill=col, font=fnt)
        return sheet

    elif style == "romance_keepsake":
        DPI_ = 300; CM_ = DPI_ / 2.54
        def cm2(v): return int(v * CM_)
        pw = cm2(tpl["w"]); ph = cm2(tpl["h"])
        bg_col = (255, 250, 235)
        sheet = Image.new("RGB", (pw, ph), bg_col)
        draw = ImageDraw.Draw(sheet)

        # Warm border
        draw.rectangle([cm2(0.2), cm2(0.2), pw-cm2(0.2), ph-cm2(0.2)],
                       outline=(210, 160, 80), width=3)

        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", cm2(0.55))
            font_sub   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", cm2(0.3))
            font_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", cm2(0.28))
        except Exception:
            font_title = font_sub = font_label = ImageFont.load_default()

        # KEEPSAKE title top right
        tb = draw.textbbox((0,0), "KEEPSAKE", font=font_title)
        draw.text((pw - (tb[2]-tb[0]) - cm2(0.5), cm2(0.35)), "KEEPSAKE", fill=(180, 100, 60), font=font_title)
        draw.text((pw - (tb[2]-tb[0]) - cm2(0.5) + 5, cm2(0.35)+2), "♥", fill=(200, 80, 80), font=font_sub)

        # 3 photo cells with YOU / ME / TOGETHER labels
        labels_top = ["YOU.", "ME.", ""]
        labels_bot = ["YOU.", "TOGETHER.", "OUR STORY"]
        cell_gap = cm2(0.35)
        cell_margin_x = cm2(0.5)
        cell_margin_y = cm2(1.0)
        cell_bot_margin = cm2(1.5)
        content_h = ph - cell_margin_y - cell_bot_margin
        total_w = pw - cell_margin_x * 2 - cell_gap * 2
        cell_w_each = total_w // 3

        label_colors = [(200, 80, 60), (180, 120, 50), (150, 80, 80)]
        for i in range(3):
            cx = cell_margin_x + i * (cell_w_each + cell_gap)
            # slight size variation for aesthetic
            cell_offset = cm2(0.3) if i % 2 == 1 else 0
            ch = content_h - cell_offset
            cell_img = fit_crop(filtered, cell_w_each, ch)
            # colored frame per cell
            frame_cols = [(210, 100, 60), (190, 150, 60), (200, 100, 100)]
            draw.rectangle([cx-3, cell_margin_y+cell_offset-3, cx+cell_w_each+3, cell_margin_y+cell_offset+ch+3],
                           outline=frame_cols[i], width=3)
            sheet.paste(cell_img, (cx, cell_margin_y + cell_offset))

            # Labels
            if labels_top[i]:
                ltb = draw.textbbox((0,0), labels_top[i], font=font_label)
                draw.text((cx, cell_margin_y + cell_offset - cm2(0.4)),
                          labels_top[i], fill=label_colors[i], font=font_label)
            if labels_bot[i]:
                draw.text((cx, cell_margin_y + cell_offset + ch + cm2(0.05)),
                          labels_bot[i], fill=label_colors[i], font=font_label)

        # Bottom credits
        draw.text((cm2(0.5), ph - cm2(1.2)), "FOR: MY SPECIAL SOMEONE", fill=(160, 100, 70), font=font_sub)
        draw.text((pw//2 - cm2(1), ph - cm2(1.2)), "PERFECT MATCH", fill=(180, 130, 50), font=font_label)
        return sheet

    elif style == "romance_lovenotes":
        DPI_ = 300; CM_ = DPI_ / 2.54
        def cm2(v): return int(v * CM_)
        pw, ph = cm2(tpl["w"]), cm2(tpl["h"])
        bg_col = (255, 248, 240)
        sheet = Image.new("RGB", (pw, ph), bg_col)
        draw = ImageDraw.Draw(sheet)

        # Envelope background shape
        env_top = cm2(3.5)
        env_col = (245, 225, 200)
        # Envelope body
        draw.rectangle([cm2(0.4), env_top, pw-cm2(0.4), ph-cm2(0.4)], fill=env_col, outline=(200, 160, 110), width=2)
        # Envelope flap (triangle on top)
        flap_pts = [(cm2(0.4), env_top), (pw//2, env_top + cm2(2.0)), (pw-cm2(0.4), env_top)]
        draw.polygon(flap_pts, fill=(235, 210, 175), outline=(200, 160, 110))

        # Wax seal circle
        seal_x = pw//2 - cm2(0.6)
        seal_y = env_top + cm2(0.8)
        seal_r = cm2(0.6)
        draw.ellipse([seal_x, seal_y, seal_x+seal_r*2, seal_y+seal_r*2], fill=(160, 60, 60), outline=(130, 40, 40), width=2)
        draw.text((seal_x + seal_r - cm2(0.15), seal_y + seal_r - cm2(0.25)), "♥", fill=(255, 200, 200), font=ImageFont.load_default())

        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", cm2(0.65))
            font_sub   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", cm2(0.28))
            font_note  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf", cm2(0.22))
        except Exception:
            font_title = font_sub = font_note = ImageFont.load_default()

        # LOVE NOTES title top
        draw.text((cm2(0.3), cm2(0.35)), "LOVE NOTES", fill=(180, 60, 80), font=font_title)
        draw.text((pw - cm2(1.5), cm2(0.4)), "♥", fill=(200, 100, 120), font=font_title)

        # Arrow decoration
        draw.line([(cm2(0.5), cm2(1.3)), (pw - cm2(0.5), cm2(1.3))], fill=(200, 140, 100), width=2)
        draw.text((pw//2 - cm2(0.3), cm2(1.0)), "→", fill=(180, 120, 80), font=font_sub)

        # Photo cell inside envelope
        pad_side = cm2(0.9)
        photo_top = env_top + cm2(2.0)
        photo_bot_margin = cm2(2.2)
        inner_w = pw - pad_side * 2
        inner_h = ph - photo_top - photo_bot_margin
        if inner_h > 0 and inner_w > 0:
            cell_img = fit_crop(filtered, inner_w, inner_h)
            draw.rectangle([pad_side-3, photo_top-3, pad_side+inner_w+3, photo_top+inner_h+3],
                           outline=(200, 140, 100), width=3)
            sheet.paste(cell_img, (pad_side, photo_top))

        # Italic love note text lines (decorative)
        note_lines = ["Love is more than", "you can think of", "but two..."]
        for i, line in enumerate(note_lines):
            draw.text((cm2(0.5), ph - cm2(1.8) + i * cm2(0.35)), line, fill=(180, 140, 120), font=font_note)
            draw.text((pw//2 + cm2(0.2), ph - cm2(1.8) + i * cm2(0.35)), line, fill=(180, 140, 120), font=font_note)

        # Bottom text
        bsub = "I'D PICK YOU EVERY TIME"
        bb = draw.textbbox((0,0), bsub, font=font_sub)
        draw.text(((pw - (bb[2]-bb[0]))//2, ph - cm2(1.0)), bsub, fill=(160, 80, 80), font=font_sub)

        # Arrow bottom
        draw.line([(cm2(0.5), ph - cm2(0.55)), (pw - cm2(0.5), ph - cm2(0.55))], fill=(200, 140, 100), width=2)
        draw.text((cm2(0.5), ph - cm2(0.5)), "→", fill=(180, 120, 80), font=font_sub)
        return sheet

    # fallback
    return build_sheet(photo, tpl, filter_key)


LOGO_FONTS = {
    "Bold (Default)": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "Regular": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "Italic": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
    "Bold Italic": "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
    "Mono": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "Serif": "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
    "Serif Bold": "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf",
    "Serif Italic": "/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf",
}

LOGO_SHAPES = {
    "none": "Tanpa Badge",
    "rectangle": "Kotak",
    "rounded_rect": "Kotak Rounded",
    "ellipse": "Oval/Lingkaran",
    "banner": "Banner Ribbon",
    "diamond": "Berlian",
    "star_badge": "Bintang (notch)",
}

def draw_logo_badge(draw_obj, text, sub_text, x, y, w, h,
                    font_key="Bold (Default)", shape="none",
                    text_color=(180, 40, 40), badge_color=(255, 255, 255),
                    border_color=(200, 200, 200), font_size_px=60, sub_font_size_px=28):
    """Draw a customizable logo badge onto draw at given area."""
    try:
        font_path = LOGO_FONTS.get(font_key, LOGO_FONTS["Bold (Default)"])
        font_main = ImageFont.truetype(font_path, font_size_px)
        font_sub_f = ImageFont.truetype(font_path, sub_font_size_px)
    except Exception:
        font_main = font_sub_f = ImageFont.load_default()

    bb_main = draw_obj.textbbox((0, 0), text, font=font_main)
    text_w = bb_main[2] - bb_main[0]
    text_h = bb_main[3] - bb_main[1]

    bb_sub = draw_obj.textbbox((0, 0), sub_text, font=font_sub_f) if sub_text else (0,0,0,0)
    sub_w = bb_sub[2] - bb_sub[0]
    sub_h = bb_sub[3] - bb_sub[1]

    pad = max(12, font_size_px // 5)
    badge_w = max(text_w, sub_w) + pad * 2
    badge_h = text_h + (sub_h + pad // 2 if sub_text else 0) + pad * 2

    bx = x + (w - badge_w) // 2
    by = y + (h - badge_h) // 2

    if shape == "rectangle":
        draw_obj.rectangle([bx, by, bx+badge_w, by+badge_h], fill=badge_color, outline=border_color, width=3)
    elif shape == "rounded_rect":
        draw_obj.rounded_rectangle([bx, by, bx+badge_w, by+badge_h], radius=badge_h//4,
                                fill=badge_color, outline=border_color, width=3)
    elif shape == "ellipse":
        draw_obj.ellipse([bx, by, bx+badge_w, by+badge_h], fill=badge_color, outline=border_color, width=3)
    elif shape == "banner":
        pts = [(bx, by + badge_h//4), (bx + badge_w//6, by),
               (bx + badge_w*5//6, by), (bx+badge_w, by + badge_h//4),
               (bx+badge_w, by + badge_h*3//4), (bx + badge_w*5//6, by+badge_h),
               (bx + badge_w//6, by+badge_h), (bx, by + badge_h*3//4)]
        draw_obj.polygon(pts, fill=badge_color, outline=border_color)
    elif shape == "diamond":
        mid_x, mid_y = bx + badge_w//2, by + badge_h//2
        draw_obj.polygon([(mid_x, by), (bx+badge_w, mid_y), (mid_x, by+badge_h), (bx, mid_y)],
                    fill=badge_color, outline=border_color)
    elif shape == "star_badge":
        draw_obj.rounded_rectangle([bx, by, bx+badge_w, by+badge_h], radius=8,
                                fill=badge_color, outline=border_color, width=3)
        notch = badge_h // 6
        draw_obj.rectangle([bx - notch, by + badge_h//2 - notch//2,
                         bx + notch, by + badge_h//2 + notch//2], fill=badge_color)
        draw_obj.rectangle([bx + badge_w - notch, by + badge_h//2 - notch//2,
                         bx + badge_w + notch, by + badge_h//2 + notch//2], fill=badge_color)

    tx = x + (w - text_w) // 2
    ty = by + pad
    draw_obj.text((tx, ty), text, fill=text_color, font=font_main)

    if sub_text:
        sx = x + (w - sub_w) // 2
        sy = ty + text_h + pad // 2
        draw_obj.text((sx, sy), sub_text, fill=border_color, font=font_sub_f)


def build_studio_sheet(photo: Image.Image, tpl: dict, filter_key: str,
                        studio_name: str = "Photo Booth Studio",
                        studio_sub: str = "NEW WAVE PHOTO STUDIO",
                        logo_font: str = "Bold (Default)",
                        logo_shape: str = "none",
                        logo_text_color: tuple = (180, 40, 40),
                        logo_badge_color: tuple = (255, 255, 255),
                        logo_border_color: tuple = (200, 200, 200)) -> Image.Image:
    """Build oh!shoot-style studio print with customizable logo top & bottom."""
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
    draw_logo_badge(
        draw, studio_name, "",
        x=0, y=0, w=sheet_w, h=logo_top_h,
        font_key=logo_font, shape=logo_shape,
        text_color=logo_text_color,
        badge_color=logo_badge_color,
        border_color=logo_border_color,
        font_size_px=int(cm_to_px(0.55)),
        sub_font_size_px=int(cm_to_px(0.25)),
    )

    # ── Paste photo grid ──────────────────────────────────────────────────────
    grid_y_offset = logo_top_h + margin_px
    for r in range(rows):
        for c in range(cols):
            x = margin_px + c * (cell_w + gap_px)
            y = grid_y_offset + r * (cell_h + gap_px)
            border_col = (220, 220, 220)
            bp = 3
            draw.rectangle([x-bp, y-bp, x+cell_w+bp, y+cell_h+bp], outline=border_col, width=bp)
            sheet.paste(cell, (x, y))

    # ── Bottom logo area ──────────────────────────────────────────────────────
    bottom_y = sheet_h - logo_bottom_h
    draw.line([(margin_px, bottom_y + int(cm_to_px(0.12))),
               (sheet_w - margin_px, bottom_y + int(cm_to_px(0.12)))],
              fill=(220, 220, 220), width=2)

    draw_logo_badge(
        draw, studio_name, studio_sub,
        x=0, y=bottom_y, w=sheet_w, h=logo_bottom_h,
        font_key=logo_font, shape=logo_shape,
        text_color=logo_text_color,
        badge_color=logo_badge_color,
        border_color=logo_border_color,
        font_size_px=int(cm_to_px(0.65)),
        sub_font_size_px=int(cm_to_px(0.26)),
    )

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

WATERMARK_POSITIONS = {
    "Kanan Bawah": "bottom_right",
    "Kiri Bawah":  "bottom_left",
    "Kanan Atas":  "top_right",
    "Kiri Atas":   "top_left",
    "Tengah":      "center",
}

def add_watermark(sheet: Image.Image, name: str,
                  logo_img=None,
                  position: str = "bottom_right",
                  logo_size_pct: int = 12,
                  opacity: int = 200) -> Image.Image:
    """Watermark dengan teks dan/atau logo gambar di posisi pilihan."""
    has_text = bool(name and name.strip())
    has_logo = logo_img is not None
    if not has_text and not has_logo:
        return sheet

    sheet = sheet.copy().convert("RGBA")
    w, h = sheet.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    mg = int(w * 0.018)

    logo_px = int(w * logo_size_pct / 100) if has_logo else 0
    logo_resized = None
    if has_logo:
        lw, lh = logo_img.size
        scale = logo_px / max(lw, lh)
        logo_resized = logo_img.resize(
            (int(lw * scale), int(lh * scale)), Image.LANCZOS
        ).convert("RGBA")
        r, g, b, a = logo_resized.split()
        a = a.point(lambda v: int(v * opacity / 255))
        logo_resized = Image.merge("RGBA", (r, g, b, a))

    text_w, text_h = 0, 0
    font = None
    if has_text:
        try:
            fs = max(18, int(w * 0.026))
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fs)
        except Exception:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), name, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

    gap = int(w * 0.008)
    total_w = (logo_resized.size[0] if logo_resized else 0) + (gap if has_logo and has_text else 0) + text_w
    total_h = max(logo_resized.size[1] if logo_resized else 0, text_h)

    if position == "bottom_right":
        ax, ay = w - total_w - mg, h - total_h - mg
    elif position == "bottom_left":
        ax, ay = mg, h - total_h - mg
    elif position == "top_right":
        ax, ay = w - total_w - mg, mg
    elif position == "top_left":
        ax, ay = mg, mg
    else:
        ax, ay = (w - total_w) // 2, (h - total_h) // 2

    cur_x = ax
    if logo_resized:
        lw2, lh2 = logo_resized.size
        ly = ay + (total_h - lh2) // 2
        overlay.paste(logo_resized, (cur_x, ly), logo_resized)
        cur_x += lw2 + gap

    if has_text and font:
        ty = ay + (total_h - text_h) // 2
        draw.text((cur_x + 2, ty + 2), name, fill=(0, 0, 0, 160), font=font)
        draw.text((cur_x, ty), name, fill=(255, 255, 255, opacity), font=font)

    sheet = Image.alpha_composite(sheet, overlay)
    return sheet.convert("RGB")


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
  max-height:52vh; object-fit:cover;
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
  display:flex; gap:8px; margin-top:6px;
  justify-content:center; align-items:center;
}
#captureBtn {
  background:#f5c518; color:#000; border:none; border-radius:50%;
  width:64px; height:64px; font-size:15px; cursor:pointer; font-weight:bold;
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
  margin-top:3px; min-height:16px; letter-spacing:0.4px;
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
<div id="motionLabel" style="text-align:center;font-size:10px;color:#555;margin:1px 0 4px;">
  gerak = auto snap
</div>

<div id="controls">
  <button class="tbtn on" id="autoBtn" onclick="toggleAuto()">🤏 Auto Snap</button>
  <div style="display:flex;flex-direction:column;align-items:center;gap:3px;">
    <button id="captureBtn" onclick="startCapture()">📸</button>
    <span style="font-size:10px;color:#f5c518;font-weight:bold;letter-spacing:1px;">AMBIL FOTO</span>
  </div>
  <button class="tbtn" id="timerBtn" onclick="toggleTimer()">⏱️ Timer 3s</button>
</div>
<div id="status">Memulai kamera...</div>

<div id="previewBox">
  <p id="savedMsg">✅ Foto tersimpan otomatis!</p>
  <img id="previewImg" src="" alt="preview">
  <button id="retakeBtn" onclick="retake()">🔄 Ambil Ulang Foto</button>
  <p style="font-size:11px;color:#666;margin-top:4px;">Foto kurang pas? Tap ambil ulang</p>
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
let motionHoldFrames = 0;
let snapCooldown = 0;          // prevent double-snap
const MOTION_THRESHOLD = 10;  // lebih sensitif
const MOTION_TRIGGER   = 0.04; // 4% pixels bergerak = cukup
const HOLD_FRAMES      = 5;   // lebih cepat trigger

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

  // Cooldown countdown
  if (snapCooldown > 0) snapCooldown--;

  // Trigger auto snap
  if (autoSnap && motionHoldFrames >= HOLD_FRAMES && !capturing && snapCooldown === 0) {
    motionHoldFrames = 0;
    snapCooldown = 60; // ~2 detik cooldown biar ga dobel snap
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
  snapCooldown = 30; // sedikit delay setelah retake
  motionHoldFrames = 0;
  motionScore = 0;
  statusEl.textContent = autoSnap
    ? '🤏 Gerakkan tangan untuk snap otomatis'
    : '📸 Tap tombol untuk foto';
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
if "watermark_name" not in st.session_state:
    st.session_state.watermark_name = ""
if "watermark_logo" not in st.session_state:
    st.session_state.watermark_logo = None
if "watermark_position" not in st.session_state:
    st.session_state.watermark_position = "Kanan Bawah"
if "watermark_logo_size" not in st.session_state:
    st.session_state.watermark_logo_size = 12
if "watermark_opacity" not in st.session_state:
    st.session_state.watermark_opacity = 200
if "logo_font" not in st.session_state:
    st.session_state.logo_font = "Bold (Default)"
if "logo_shape" not in st.session_state:
    st.session_state.logo_shape = "none"
if "logo_text_color_hex" not in st.session_state:
    st.session_state.logo_text_color_hex = "#b42828"
if "logo_badge_color_hex" not in st.session_state:
    st.session_state.logo_badge_color_hex = "#ffffff"
if "logo_border_color_hex" not in st.session_state:
    st.session_state.logo_border_color_hex = "#cccccc"

# ── UI ─────────────────────────────────────────────────────────────────────────
st.markdown("# 📸 Photo Booth Cetak")
st.divider()

tab_photobooth, tab_collage, tab_support = st.tabs(["📸 Photo Booth", "🖼️ Collage", "💌 Dukung Developer"])

with tab_photobooth:
 st.markdown("*Ambil foto → Pilih tema → Pilih template → Download PDF / JPG*")

 col_left, col_right = st.columns([1, 1.4], gap="large")

# ── LEFT: Foto input + Filter + Template picker ───────────────────────────────
with col_left:
    st.markdown("### 1. Ambil / Upload Foto")

    input_mode = st.radio("Sumber foto", ["📷 Webcam", "📁 Upload File"], horizontal=True, label_visibility="collapsed")

    if input_mode == "📷 Webcam":
        # ── AR Camera preview ─────────────────────────────────────────────────
        components.html(get_ar_camera_html(), height=760, scrolling=False)

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
    st.markdown("### 🏷️ Watermark & Logo")

    wm_col1, wm_col2 = st.columns([1, 1])
    with wm_col1:
        wm = st.text_input(
            "Teks watermark (opsional)",
            value=st.session_state.watermark_name,
            key="wm_input", max_chars=30,
            placeholder="contoh: Zizah Studio",
        )
        st.session_state.watermark_name = wm
    with wm_col2:
        wm_pos = st.selectbox(
            "Posisi",
            list(WATERMARK_POSITIONS.keys()),
            index=list(WATERMARK_POSITIONS.keys()).index(st.session_state.watermark_position),
            key="wm_pos_sel",
        )
        st.session_state.watermark_position = wm_pos

    wm_logo_file = st.file_uploader(
        "Upload Logo (PNG transparan lebih bagus)",
        type=["png", "jpg", "jpeg", "webp"],
        key="wm_logo_upload",
    )
    if wm_logo_file:
        st.session_state.watermark_logo = Image.open(wm_logo_file).convert("RGBA")
        st.success("✅ Logo terupload!")

    if st.session_state.watermark_logo is not None:
        wm_preview_col, wm_ctrl_col = st.columns([1, 2])
        with wm_preview_col:
            st.image(st.session_state.watermark_logo, width=80, caption="Logo preview")
        with wm_ctrl_col:
            lsz = st.slider("Ukuran logo (%)", 5, 30,
                            st.session_state.watermark_logo_size, key="wm_logo_size")
            st.session_state.watermark_logo_size = lsz
            opac = st.slider("Opacity (0=transparan, 255=solid)",
                             50, 255, st.session_state.watermark_opacity, key="wm_opacity")
            st.session_state.watermark_opacity = opac
        if st.button("🗑️ Hapus Logo", key="wm_logo_del"):
            st.session_state.watermark_logo = None
            st.rerun()
    else:
        lsz = st.session_state.watermark_logo_size
        opac = st.session_state.watermark_opacity

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
        <div style="background:linear-gradient(135deg,#1a1a1a 0%,#222 100%);
                    border:2px dashed #444; border-radius:16px;
                    height:360px; display:flex; flex-direction:column;
                    align-items:center; justify-content:center;
                    color:#666; font-size:15px; text-align:center; padding:24px;
                    gap:12px;">
            <div style="font-size:52px; filter:grayscale(1) opacity(0.4);">📸</div>
            <div style="color:#f5c518; font-size:20px; font-weight:700;
                        font-family:'Courier New',monospace; letter-spacing:2px;">
                SIAP UNTUK FOTO?
            </div>
            <div style="color:#888; font-size:13px; line-height:1.7;">
                1. Pilih <b style="color:#aaa;">📷 Webcam</b> untuk ambil foto langsung<br>
                2. Atau <b style="color:#aaa;">📁 Upload File</b> dari galeri kamu<br>
                3. Foto langsung otomatis tersimpan & bisa diedit 🎨
            </div>
            <div style="margin-top:8px; background:#f5c518; color:#000;
                        padding:6px 18px; border-radius:20px; font-size:12px;
                        font-weight:700; letter-spacing:1px;">
                ← PANEL KIRI
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # ── Studio Print / Logo custom inputs ─────────────────────────────────
        if tpl_key == "studio_print":
            st.markdown("#### 🏷️ Kustomisasi Logo Studio")
            scol1, scol2 = st.columns(2)
            with scol1:
                sn = st.text_input("🏪 Nama Studio", value=st.session_state.studio_name,
                                   key="studio_name_input", max_chars=30)
                st.session_state.studio_name = sn
            with scol2:
                ss = st.text_input("📝 Tagline", value=st.session_state.studio_sub,
                                   key="studio_sub_input", max_chars=40)
                st.session_state.studio_sub = ss

            logo_col1, logo_col2, logo_col3 = st.columns(3)
            with logo_col1:
                lf = st.selectbox("🔤 Font Logo", list(LOGO_FONTS.keys()),
                                  index=list(LOGO_FONTS.keys()).index(st.session_state.logo_font),
                                  key="logo_font_sel")
                st.session_state.logo_font = lf
            with logo_col2:
                ls = st.selectbox("🔷 Bentuk Badge", list(LOGO_SHAPES.values()),
                                  key="logo_shape_sel")
                st.session_state.logo_shape = list(LOGO_SHAPES.keys())[list(LOGO_SHAPES.values()).index(ls)]
            with logo_col3:
                st.markdown("**Warna Teks**")
                ltc = st.color_picker("Warna Teks Logo", value=st.session_state.logo_text_color_hex,
                                      key="logo_text_color", label_visibility="collapsed")
                st.session_state.logo_text_color_hex = ltc

            bdc_col1, bdc_col2 = st.columns(2)
            with bdc_col1:
                st.markdown("**Warna Badge**")
                lbc = st.color_picker("Warna Badge", value=st.session_state.logo_badge_color_hex,
                                      key="logo_badge_color", label_visibility="collapsed")
                st.session_state.logo_badge_color_hex = lbc
            with bdc_col2:
                st.markdown("**Warna Border Badge**")
                lbrc = st.color_picker("Warna Border", value=st.session_state.logo_border_color_hex,
                                       key="logo_border_color", label_visibility="collapsed")
                st.session_state.logo_border_color_hex = lbrc

        def _hex_to_rgb(h):
            h = h.lstrip("#")
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

        with st.spinner("⚙️ Membuat layout..."):
            if tpl_key == "studio_print":
                sheet = build_studio_sheet(
                    st.session_state.photo, tpl, current_filter,
                    st.session_state.studio_name,
                    st.session_state.studio_sub,
                    logo_font=st.session_state.logo_font,
                    logo_shape=st.session_state.logo_shape,
                    logo_text_color=_hex_to_rgb(st.session_state.logo_text_color_hex),
                    logo_badge_color=_hex_to_rgb(st.session_state.logo_badge_color_hex),
                    logo_border_color=_hex_to_rgb(st.session_state.logo_border_color_hex),
                )
            elif tpl["style"].startswith("frame_") or tpl["style"].startswith("romance_"):
                sheet = build_frame_sheet(st.session_state.photo, tpl, current_filter)
            else:
                sheet = build_sheet(st.session_state.photo, tpl, current_filter)
            thumb = preview_thumbnail(sheet, max_px=700)

        # Before/After toggle
        show_before = st.toggle("👁️ Lihat tanpa filter (before/after)", value=False)

        if show_before:
            if tpl_key == "studio_print":
                sheet_before = build_studio_sheet(
                    st.session_state.photo, tpl, "normal",
                    st.session_state.studio_name, st.session_state.studio_sub,
                    logo_font=st.session_state.logo_font,
                    logo_shape=st.session_state.logo_shape,
                    logo_text_color=_hex_to_rgb(st.session_state.logo_text_color_hex),
                    logo_badge_color=_hex_to_rgb(st.session_state.logo_badge_color_hex),
                    logo_border_color=_hex_to_rgb(st.session_state.logo_border_color_hex),
                )
            elif tpl["style"].startswith("frame_") or tpl["style"].startswith("romance_"):
                sheet_before = build_frame_sheet(st.session_state.photo, tpl, "normal")
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

        sheet_wm = add_watermark(
            sheet,
            st.session_state.watermark_name,
            logo_img=st.session_state.watermark_logo,
            position=WATERMARK_POSITIONS.get(st.session_state.watermark_position, "bottom_right"),
            logo_size_pct=st.session_state.watermark_logo_size,
            opacity=st.session_state.watermark_opacity,
        )

        with d1:
            jpg_bytes = sheet_to_bytes(sheet_wm, "JPEG")
            st.download_button(
                label="⬇️ Download JPG",
                data=jpg_bytes,
                file_name=f"photobooth_{tpl_key}_{current_filter}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
                mime="image/jpeg",
                use_container_width=True,
            )

        with d2:
            pdf_bytes = sheet_to_pdf(sheet_wm, tpl)
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



with tab_support:
    API_URL = "https://photobooth-api.up.railway.app"  # ganti dengan URL Railway kamu

    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Spectral:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">
    <style>
    .support-wrap {
        max-width:620px; margin:0 auto; padding:8px 0;
    }
    .support-card {
        background:#1a0f0f;
        border:2px dashed #c8a040;
        border-radius:14px;
        padding:28px 24px 32px;
        box-shadow:0 0 24px rgba(200,160,64,0.18), inset 0 0 30px rgba(0,0,0,0.3);
        margin-bottom:20px;
    }
    .support-title {
        font-family:'Cinzel',serif;
        font-size:clamp(16px,4vw,22px);
        color:#c8a040;
        text-align:center;
        letter-spacing:2px;
        margin-bottom:6px;
        text-shadow:0 0 14px rgba(200,160,64,0.4);
    }
    .support-sub {
        font-family:'Spectral',Georgia,serif;
        font-size:14px;
        color:#c8b89a;
        text-align:center;
        margin-bottom:18px;
        line-height:1.6;
    }
    .doa-count {
        background:#2a1a0a;
        border:1px solid #c8a040;
        border-radius:8px;
        padding:10px 16px;
        text-align:center;
        font-family:'Cinzel',serif;
        color:#c8a040;
        font-size:13px;
        margin-bottom:18px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="support-wrap">', unsafe_allow_html=True)
    st.markdown("""
    <div class="support-card">
        <div class="support-title">💌 Pesan & Doa untuk Developer</div>
        <div class="support-sub">
            Aplikasi ini dibuat dengan sepenuh hati.<br>
            Tidak ada yang diminta selain doa & pesan baikmu. 🙏
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Hitung doa
    try:
        import requests as req_lib
        r = req_lib.get(f"{API_URL}/doa/count", timeout=3)
        total = r.json().get("total", 0)
        st.markdown(f'<div class="doa-count">🌟 {total} orang sudah mengirim doa & pesan</div>',
                    unsafe_allow_html=True)
    except Exception:
        st.markdown('<div class="doa-count">🌟 Jadilah yang pertama mengirim doa ✨</div>',
                    unsafe_allow_html=True)

    with st.form("form_doa", clear_on_submit=True):
        nama = st.text_input("Nama kamu (boleh anonim)", placeholder="contoh: Zizah 💕",
                             max_chars=40)
        pesan = st.text_area("Pesan & saran untuk developer 💬",
                             placeholder="Tulis pesanmu di sini...",
                             max_chars=500, height=120)
        doa = st.text_area("Doa untuk developer 🙏 (opsional)",
                           placeholder="contoh: Semoga rezekinya lancar, segera ke Jakarta...",
                           max_chars=300, height=80)

        # Detect device via JS
        components.html("""
        <script>
        const ua = navigator.userAgent;
        const el = window.parent.document.querySelector('input[aria-label="device_info_hidden"]');
        if (el) { el.value = ua; el.dispatchEvent(new Event('input',{bubbles:true})); }
        </script>
        """, height=0)
        device_info = st.text_input("device_info_hidden", key="device_info",
                                    label_visibility="collapsed")

        submitted = st.form_submit_button("💌 Kirim Pesan & Doa", use_container_width=True)

        if submitted:
            if not pesan.strip():
                st.warning("Tulis pesan dulu ya 😊")
            else:
                try:
                    import requests as req_lib
                    payload = {
                        "nama":   nama.strip() or "Anonim",
                        "pesan":  pesan.strip(),
                        "doa":    doa.strip(),
                        "device": device_info[:200] if device_info else "",
                    }
                    r = req_lib.post(f"{API_URL}/doa", json=payload, timeout=5)
                    data = r.json()
                    if data.get("status") == "ok":
                        st.success(f"✅ {data['pesan']}")
                        st.info(f"📍 Terdeteksi dari: **{data.get('lokasi','?')}**")
                        st.balloons()
                    else:
                        st.error("Gagal mengirim, coba lagi 😢")
                except Exception as ex:
                    st.error(f"Koneksi ke server gagal: {ex}")

    st.markdown('</div>', unsafe_allow_html=True)

    # Info developer
    st.divider()
    st.markdown("""
    <div style="text-align:center; padding:16px; background:#1a0f0f;
                border-radius:12px; border:1px solid #333; max-width:620px; margin:0 auto;">
        <div style="font-family:'Cinzel',serif; color:#c8a040; font-size:14px;
                    letter-spacing:1.5px; margin-bottom:8px;">TENTANG DEVELOPER</div>
        <div style="font-family:'Spectral',Georgia,serif; color:#c8b89a;
                    font-size:13px; line-height:1.8;">
            Dibuat oleh <b style="color:#c8a040;">Isfan Fajar Anugrah</b><br>
            IT Support · Python Developer · Serang, Banten<br>
            <span style="font-size:12px; color:#888;">
            Aplikasi ini dibuat dengan cinta dan kopi ☕<br>
            semoga bermanfaat untuk kamu 💛
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


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
    st.write("Zah, di atas itu bukti obrolan gua sama Pak Ageng (Recruiter HTC Global Services). Gua sengaja pajang di sini biar lu tahu semuanya.")
    
    st.write("Kemarin gua dapet panggilan interview di Jakarta. Udah gua siapin semuanya — termasuk script photo booth ini, buat ngerayain kalau goals.")
    
    st.write("Tapi situasi di rumah lagi nggak kondusif buat gua pergi. Jadi ya... gagal berangkat.")
    
    st.write("Nggak tau kenapa pengen cerita ke lu juga. Mungkin karena tanpa lu sadar, lu udah ngaruh ke hidup gua lebih dari yang lu kira.")
    
    st.write("Serius. Dari postingan lu di TikTok — yang bahkan bukan buat gua — gua bisa distract, baru kali ini gua ngerasa nggak terpaksa buat berubah. Gua putus sama kebiasaan lama, bukan karena disuruh, tapi karena lu tanpa sadar kasih alasan yang lebih kuat.")
    
    # Bagian cerita apes yang udah disinkronkan:
    st.write("Inget masalah kemarin? Apesnya lu gara-gara salah transfer, apesnya gua juga pas ngirim matcha malah nyangkut di security wkwk. Gara-gara drama sama-sama apes itu, gua mikir... emang kita kayaknya gabisa dipisah-pisahin, Zah. ❤️")
    
    st.write("Nomor gua masih sama, aktif terus 24 jam. Kalau lu mau ninggalin pesan di sini atau ngabarin langsung, pintu gua selalu kebuka. Urusan matcha yang gagal kemarin tetep bakal gua ganti — ntar gua DM lu lagi ya, wkwk.")
    
    st.write("Doain gua ya. Kalau masih ada kesempatan, gua bakal prioritasin lu jadi nomor satu — tapi kalau bukan lu, gua tetap berdoa semoga yang itu lu juga. wkwkw")
