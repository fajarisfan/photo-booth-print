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
#wrap { position:relative; width:100%; max-width:480px; margin:0 auto; }
#video {
  width:100%; display:block; border-radius:10px;
  transform:scaleX(-1); /* mirror preview like a normal selfie camera */
}
#overlay {
  position:absolute; top:0; left:0; width:100%; height:100%;
  border-radius:10px; pointer-events:none;
}
#controls {
  display:flex; gap:6px; margin-top:8px; justify-content:center;
  flex-wrap:wrap; align-items:center;
}
#captureBtn {
  background:#f5c518; color:#000; border:none; border-radius:50%;
  width:58px; height:58px; font-size:22px; cursor:pointer; font-weight:bold;
  box-shadow:0 0 0 4px #333; transition:transform 0.1s, box-shadow 0.1s;
  flex-shrink:0;
}
#captureBtn:active { transform:scale(0.9); box-shadow:0 0 0 2px #333; }
.tbtn {
  background:#1e1e1e; color:#888; border:1.5px solid #444;
  border-radius:8px; padding:5px 9px; font-size:11px; cursor:pointer;
  transition:all 0.15s; white-space:nowrap;
}
.tbtn.on { background:#1e1e0a; color:#f5c518; border-color:#f5c518; }
#status {
  text-align:center; color:#888; font-size:11px; margin-top:6px;
  min-height:16px; letter-spacing:0.5px;
}
#flash {
  position:absolute; top:0; left:0; width:100%; height:100%;
  background:white; border-radius:10px; opacity:0; pointer-events:none;
  transition:opacity 0.05s;
}
</style>
</head>
<body>
<div id="wrap">
  <video id="video" autoplay playsinline muted></video>
  <canvas id="overlay"></canvas>
  <div id="flash"></div>
</div>
<div id="controls">
  <button class="tbtn" id="btnSkull"   onclick="tog('skull')">💀 Skull</button>
  <button class="tbtn on" id="btnSticker" onclick="tog('sticker')">🎩 Sticker</button>
  <button id="captureBtn" title="Ambil Foto">📸</button>
  <button class="tbtn on" id="btnQuote"   onclick="tog('quote')">💬 Quote</button>
  <button class="tbtn" id="btnHand"    onclick="tog('hand')">✋ Tangan</button>
</div>
<div id="status">Memuat model AI...</div>

<script src="https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh@0.4.1633559619/face_mesh.js" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1646424915/hands.js" crossorigin="anonymous"></script>

<script>
const video   = document.getElementById('video');
const canvas  = document.getElementById('overlay');
const ctx     = canvas.getContext('2d');
const status  = document.getElementById('status');
const flash   = document.getElementById('flash');
const captBtn = document.getElementById('captureBtn');

const feat = { skull:false, sticker:true, quote:true, hand:false };

function tog(f) {
  feat[f] = !feat[f];
  document.getElementById('btn' + f.charAt(0).toUpperCase() + f.slice(1))
    .classList.toggle('on', feat[f]);
}

// ── Quotes ───────────────────────────────────────────────────────────────────
const QUOTES = [
  "Senyum itu gratis ✨","You look amazing 🌟","Cheese! 🧀",
  "Strike a pose 💃","Camera loves you 📸","Living my best life 🔥",
  "Main character ⭐","Glow up era 🌸","Too glam 💅",
  "Unbothered 😌","Vibe check: ✔️","Built different 💪",
  "Soft life 🕊️","No bad days 🌈","Iconic 🏆",
];
let quote = QUOTES[0], qTimer = 0;

// ── Landmarks state ───────────────────────────────────────────────────────────
let faceLM = null, handLMs = [];

// Key indices
const NOSE=1, FORE=10, CHIN=152, LCHK=234, RCHK=454;
const LEYE_C=159, REYE_C=386, LEYE_L=33, REYE_R=263, LIP_T=13;
const LBROW=[70,63,105,66,107], RBROW=[336,296,334,293,300];

// ── MediaPipe init ────────────────────────────────────────────────────────────
let readyCount = 0;
function checkReady() {
  readyCount++;
  if (readyCount === 2) status.textContent = 'Siap! Hadapkan wajah ke kamera 😊';
}

const faceMesh = new FaceMesh({ locateFile: f =>
  `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh@0.4.1633559619/${f}` });
faceMesh.setOptions({ maxNumFaces:1, refineLandmarks:true,
  minDetectionConfidence:0.5, minTrackingConfidence:0.5 });
faceMesh.onResults(r => { faceLM = r.multiFaceLandmarks?.[0] || null; });

const handsMP = new Hands({ locateFile: f =>
  `https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1646424915/${f}` });
handsMP.setOptions({ maxNumHands:2, modelComplexity:1,
  minDetectionConfidence:0.5, minTrackingConfidence:0.5 });
handsMP.onResults(r => { handLMs = r.multiHandLandmarks || []; });

faceMesh.initialize().then(checkReady).catch(()=>{ readyCount++; });
handsMP.initialize().then(checkReady).catch(()=>{ readyCount++; });

// ── Camera ───────────────────────────────────────────────────────────────────
navigator.mediaDevices.getUserMedia({ video:{ facingMode:'user', width:640, height:480 }, audio:false })
  .then(s => {
    video.srcObject = s;
    video.onloadedmetadata = () => {
      canvas.width  = video.videoWidth;
      canvas.height = video.videoHeight;
      loop();
    };
  })
  .catch(() => status.textContent = '❌ Kamera tidak bisa diakses');

// ── Helpers ───────────────────────────────────────────────────────────────────
function P(i) {
  if (!faceLM) return null;
  return { x: faceLM[i].x * canvas.width, y: faceLM[i].y * canvas.height };
}

// ── Skull mesh ────────────────────────────────────────────────────────────────
function drawSkull() {
  if (!faceLM) return;
  ctx.save();
  const CONNS = [
    [10,338],[338,297],[297,332],[332,284],[284,251],[251,389],[389,356],[356,454],
    [454,323],[323,361],[361,288],[288,397],[397,365],[365,379],[379,378],[378,400],
    [400,377],[377,152],[152,148],[148,176],[176,149],[149,150],[150,136],[136,172],
    [172,58],[58,132],[132,93],[93,234],[234,127],[127,162],[162,21],[21,54],[54,103],
    [103,67],[67,109],[109,10],
    [168,6],[6,197],[197,195],[195,5],[5,4],[4,1],
    [33,246],[246,161],[161,160],[160,159],[159,158],[158,157],[157,173],
    [133,155],[155,154],[154,153],[153,145],[145,144],[144,163],[163,7],[7,33],
    [362,398],[398,384],[384,385],[385,386],[386,387],[387,388],[466,263],
    [263,249],[249,390],[390,373],[373,374],[374,380],[380,381],[381,382],[382,362],
  ];
  ctx.strokeStyle = 'rgba(0,255,100,0.6)';
  ctx.lineWidth = 0.9;
  for (const [a,b] of CONNS) {
    const pa = faceLM[a], pb = faceLM[b];
    ctx.beginPath();
    ctx.moveTo(pa.x*canvas.width, pa.y*canvas.height);
    ctx.lineTo(pb.x*canvas.width, pb.y*canvas.height);
    ctx.stroke();
  }
  ctx.fillStyle = 'rgba(0,255,100,0.7)';
  for (const p of faceLM) {
    ctx.beginPath();
    ctx.arc(p.x*canvas.width, p.y*canvas.height, 0.9, 0, Math.PI*2);
    ctx.fill();
  }
  ctx.restore();
}

// ── Stickers ──────────────────────────────────────────────────────────────────
function drawStickers() {
  if (!faceLM) return;
  const nose=P(NOSE), fore=P(FORE), chin=P(CHIN);
  const lc=P(LCHK), rc=P(RCHK);
  if (!nose||!fore||!chin||!lc||!rc) return;

  const fW = Math.abs(rc.x - lc.x);
  const fH = Math.abs(chin.y - fore.y);
  ctx.save();

  // 🎩 Top hat
  const hW = fW*1.15, hH = fH*0.55;
  const hX = fore.x - hW/2, hY = fore.y - hH*1.1;
  // brim
  ctx.fillStyle='#0d0600'; ctx.strokeStyle='#f5c518'; ctx.lineWidth=2;
  ctx.beginPath();
  ctx.ellipse(fore.x, hY+hH+3, hW*0.65, hH*0.13, 0, 0, Math.PI*2);
  ctx.fill(); ctx.stroke();
  // body
  ctx.fillStyle='#0d0600';
  ctx.beginPath();
  ctx.roundRect(hX+hW*0.08, hY, hW*0.84, hH, 5);
  ctx.fill(); ctx.stroke();
  // gold band
  ctx.fillStyle='#f5c518';
  ctx.fillRect(hX+hW*0.08, hY+hH*0.76, hW*0.84, hH*0.11);
  // buckle
  ctx.strokeStyle='#0d0600'; ctx.lineWidth=1;
  ctx.strokeRect(fore.x-7, hY+hH*0.76, 14, hH*0.11);

  // 👓 Glasses
  const eyeY = (P(LEYE_C).y + P(REYE_C).y)/2;
  const lCx=P(LEYE_C).x, rCx=P(REYE_C).x;
  const lR=fW*0.18;
  ctx.strokeStyle='#f5c518'; ctx.lineWidth=2.5;
  ctx.fillStyle='rgba(245,197,24,0.10)';
  ctx.beginPath(); ctx.arc(lCx,eyeY,lR,0,Math.PI*2); ctx.fill(); ctx.stroke();
  ctx.beginPath(); ctx.arc(rCx,eyeY,lR,0,Math.PI*2); ctx.fill(); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(lCx+lR,eyeY); ctx.lineTo(rCx-lR,eyeY); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(lCx-lR,eyeY); ctx.lineTo(P(LEYE_L).x-fW*0.08,eyeY-4); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(rCx+lR,eyeY); ctx.lineTo(P(REYE_R).x+fW*0.08,eyeY-4); ctx.stroke();

  // 👨 Moustache
  const lip=P(LIP_T);
  const mY=(nose.y+lip.y)/2, mW=fW*0.38;
  ctx.fillStyle='#2a0f00'; ctx.strokeStyle='#f5c518'; ctx.lineWidth=1.5;
  // left
  ctx.beginPath();
  ctx.moveTo(nose.x,mY);
  ctx.bezierCurveTo(nose.x-mW*0.25,mY-7, nose.x-mW,mY+5, nose.x-mW*0.88,mY+11);
  ctx.bezierCurveTo(nose.x-mW*0.55,mY+15, nose.x-mW*0.18,mY+9, nose.x,mY);
  ctx.fill(); ctx.stroke();
  // right
  ctx.beginPath();
  ctx.moveTo(nose.x,mY);
  ctx.bezierCurveTo(nose.x+mW*0.25,mY-7, nose.x+mW,mY+5, nose.x+mW*0.88,mY+11);
  ctx.bezierCurveTo(nose.x+mW*0.55,mY+15, nose.x+mW*0.18,mY+9, nose.x,mY);
  ctx.fill(); ctx.stroke();

  ctx.restore();
}

// ── Quote bubble ──────────────────────────────────────────────────────────────
function drawQuote() {
  if (!faceLM) return;
  const fore = P(FORE);
  if (!fore) return;
  qTimer++;
  if (qTimer > 150) { qTimer=0; quote=QUOTES[Math.floor(Math.random()*QUOTES.length)]; }

  ctx.save();
  const fs = Math.max(13, canvas.width*0.030);
  ctx.font = `bold ${fs}px 'Courier New',monospace`;
  const tw = ctx.measureText(quote).width;
  const pad=10, qx=fore.x, qy=Math.max(fore.y-36, fs+pad);
  ctx.fillStyle='rgba(0,0,0,0.70)';
  ctx.strokeStyle='#f5c518'; ctx.lineWidth=1.5;
  ctx.beginPath();
  ctx.roundRect(qx-tw/2-pad, qy-fs-4, tw+pad*2, fs+12, 8);
  ctx.fill(); ctx.stroke();
  ctx.fillStyle='#f5c518';
  ctx.textAlign='center'; ctx.textBaseline='bottom';
  ctx.fillText(quote, qx, qy+3);
  ctx.restore();
}

// ── Hand skeleton ─────────────────────────────────────────────────────────────
const HC=[[0,1],[1,2],[2,3],[3,4],[0,5],[5,6],[6,7],[7,8],
  [0,9],[9,10],[10,11],[11,12],[0,13],[13,14],[14,15],[15,16],
  [0,17],[17,18],[18,19],[19,20],[5,9],[9,13],[13,17]];

function drawHands() {
  const COLS=['#00e5ff','#ff6ec7'];
  for (let hi=0; hi<handLMs.length; hi++) {
    const hl=handLMs[hi], col=COLS[hi%2];
    ctx.save();
    ctx.strokeStyle=col; ctx.lineWidth=2.2;
    for (const [a,b] of HC) {
      ctx.beginPath();
      ctx.moveTo(hl[a].x*canvas.width, hl[a].y*canvas.height);
      ctx.lineTo(hl[b].x*canvas.width, hl[b].y*canvas.height);
      ctx.stroke();
    }
    ctx.fillStyle=col;
    for (const p of hl) {
      ctx.beginPath();
      ctx.arc(p.x*canvas.width, p.y*canvas.height, 2.5, 0, Math.PI*2);
      ctx.fill();
    }
    for (const t of [4,8,12,16,20]) {
      ctx.beginPath();
      ctx.arc(hl[t].x*canvas.width, hl[t].y*canvas.height, 5, 0, Math.PI*2);
      ctx.fill();
    }
    ctx.restore();
  }
}

// ── Main loop ─────────────────────────────────────────────────────────────────
let fc=0;
async function loop() {
  canvas.width  = video.videoWidth  || canvas.width;
  canvas.height = video.videoHeight || canvas.height;
  ctx.clearRect(0,0,canvas.width,canvas.height);

  // Send frames to mediapipe (staggered)
  fc++;
  if (video.readyState>=2) {
    if (fc%2===0) faceMesh.send({image:video}).catch(()=>{});
    if (fc%3===0) handsMP.send({image:video}).catch(()=>{});
  }

  if (feat.skull)   drawSkull();
  if (feat.sticker && faceLM) drawStickers();
  if (feat.quote  && faceLM) drawQuote();
  if (feat.hand   && handLMs.length) drawHands();

  // Face indicator dot
  ctx.fillStyle = faceLM ? '#00ff80' : '#ff4444';
  ctx.beginPath(); ctx.arc(12,12,6,0,Math.PI*2); ctx.fill();
  if (faceLM) {
    ctx.fillStyle='rgba(0,255,128,0.18)';
    ctx.beginPath(); ctx.arc(12,12,13,0,Math.PI*2); ctx.fill();
  }

  status.textContent = readyCount<2
    ? 'Memuat model AI...'
    : (faceLM ? '😊 Wajah terdeteksi — siap foto!' : '👀 Hadapkan wajah ke kamera...');

  requestAnimationFrame(loop);
}

// ── Capture photo ─────────────────────────────────────────────────────────────
captBtn.addEventListener('click', () => {
  // Flash effect
  flash.style.opacity='1';
  setTimeout(()=>{ flash.style.transition='opacity 0.3s'; flash.style.opacity='0';
    setTimeout(()=>{ flash.style.transition=''; },300); },50);

  const cap = document.createElement('canvas');
  cap.width=canvas.width; cap.height=canvas.height;
  const cc=cap.getContext('2d');

  // Draw video mirrored (natural selfie orientation)
  cc.save();
  cc.translate(cap.width,0); cc.scale(-1,1);
  cc.drawImage(video,0,0,cap.width,cap.height);
  cc.restore();

  // Draw overlays (landmarks were computed on mirrored preview coords, so also flip)
  cc.save();
  cc.translate(cap.width,0); cc.scale(-1,1);
  cc.drawImage(canvas,0,0);
  cc.restore();

  const dataUrl = cap.toDataURL('image/jpeg', 0.93);

  // Send to Streamlit via postMessage
  window.parent.postMessage({ type:'PHOTO_CAPTURED', dataUrl }, '*');

  // Also try direct input injection as fallback
  try {
    const allInputs = window.parent.document.querySelectorAll('input[aria-label="cam_bridge"]');
    if (allInputs.length) {
      allInputs[0].value = dataUrl;
      allInputs[0].dispatchEvent(new Event('input',{bubbles:true}));
    }
  } catch(e){}
});
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
        # ── AR Camera ────────────────────────────────────────────────────────
        components.html(get_ar_camera_html(), height=560, scrolling=False)

        # Bridge: JS postMessage → Streamlit text_input
        # The JS in the iframe sends postMessage to parent; this sibling iframe
        # listens and injects into the text_input below.
        components.html("""
        <script>
        window.addEventListener('message', function(e) {
          if (e.data && e.data.type === 'PHOTO_CAPTURED') {
            // Target our labelled input
            const inp = window.parent.document.querySelector('input[aria-label="cam_bridge"]');
            if (inp) {
              const nativeInput = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
              nativeInput.set.call(inp, e.data.dataUrl);
              inp.dispatchEvent(new Event('input', {bubbles:true}));
            }
          }
        });
        </script>
        """, height=0)

        # Hidden bridge input — receives base64 from JS above
        raw_b64 = st.text_input("cam_bridge", key="cam_bridge", label_visibility="collapsed")
        if raw_b64 and raw_b64.startswith("data:image"):
            header, b64data = raw_b64.split(",", 1)
            img_bytes = base64.b64decode(b64data)
            st.session_state.photo = Image.open(io.BytesIO(img_bytes))
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
        with st.spinner("⚙️ Membuat layout..."):
            sheet = build_sheet(st.session_state.photo, tpl, current_filter)
            thumb = preview_thumbnail(sheet, max_px=700)

        # Before/After toggle
        show_before = st.toggle("👁️ Lihat tanpa filter (before/after)", value=False)

        if show_before:
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
# ── Tampilkan screenshot chat HRD ─────────────────────────────────────────────
st.image("Screenshot_20260604-135129.jpg", caption="⚔️ Active Quest: Career Path Transition", use_container_width=True)

# ── Surat untuk Zizah ─────────────────────────────────────────────────────────
pesan_zizah_html = """
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Spectral:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">

<style>
  .scroll-wrapper {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    width: 100%;
    padding: 8px 0 24px 0;
    box-sizing: border-box;
  }

  .scroll-card {
    background: #2C1A10;
    border: 2px dashed #CA8A04;
    border-radius: 12px;
    max-width: 680px;
    width: 100%;
    padding: 32px 28px 36px 28px;
    box-sizing: border-box;
    box-shadow:
      0 0 18px rgba(202, 138, 4, 0.25),
      0 0 40px rgba(202, 138, 4, 0.10),
      inset 0 0 30px rgba(0, 0, 0, 0.35);
    position: relative;
  }

  .scroll-card::before,
  .scroll-card::after {
    content: "✦";
    font-size: 18px;
    color: #CA8A04;
    position: absolute;
    opacity: 0.7;
  }
  .scroll-card::before { top: 12px; left: 16px; }
  .scroll-card::after  { bottom: 12px; right: 16px; }

  .scroll-title {
    font-family: 'Cinzel', 'Times New Roman', serif;
    font-size: clamp(15px, 4vw, 20px);
    font-weight: 700;
    color: #CA8A04;
    text-align: center;
    letter-spacing: 2.5px;
    margin: 0 0 20px 0;
    text-shadow: 0 0 12px rgba(202, 138, 4, 0.45);
  }

  .scroll-divider {
    border: none;
    border-top: 1px solid rgba(202, 138, 4, 0.4);
    margin: 0 0 22px 0;
  }

  .scroll-body {
    font-family: 'Spectral', Georgia, 'Times New Roman', serif;
    font-size: clamp(14px, 3.5vw, 16px);
    line-height: 1.85;
    color: #F5E6D3;
    text-align: justify;
    hyphens: auto;
  }

  .scroll-body p {
    margin: 0 0 16px 0;
  }

  .scroll-body p:last-child {
    margin-bottom: 0;
  }

  .heart-beat {
    display: inline-block;
    animation: heartbeat 1.4s ease-in-out infinite;
    transform-origin: center;
  }

  @keyframes heartbeat {
    0%   { transform: scale(1);    }
    14%  { transform: scale(1.25); }
    28%  { transform: scale(1);    }
    42%  { transform: scale(1.18); }
    56%  { transform: scale(1);    }
    100% { transform: scale(1);    }
  }

  .scroll-footer {
    margin-top: 24px;
    text-align: right;
    font-family: 'Cinzel', serif;
    font-size: 12px;
    color: rgba(202, 138, 4, 0.55);
    letter-spacing: 1.5px;
  }
</style>

<div class="scroll-wrapper">
  <div class="scroll-card">

    <div class="scroll-title">📜 THE TRUTH BEHIND THE QUEST</div>
    <hr class="scroll-divider">

    <div class="scroll-body">
      <p>Zah, di atas itu bukti obrolan gua sama Pak Ageng (Recruiter HTC Global Services). Gua sengaja pajang di sini biar lu tahu semuanya secara terbuka. Gua rela ngambil langkah sejauh ini, nembus tantangan baru ke Jakarta, karena gua pengen nyari finansial yang lebih baik. Gua pengen berjuang di tempat yang bener-bener ngehargai hasil kerja keras gua.</p>

      <p>Tapi dari skrip ini gua mau lu tahu, lu gak usah khawatir, gua gabakal lupain lu, Zah. Gua kagum banget sama lu. Lu itu wanita mandiri, tipe cewek yang susah buat dideketin, dan jujur... cewek kayak lu yang emang gua cari selama ini.</p>

      <p>Sekarang bukannya gua menghilang atau ngejauh. Tapi setiap kali lu bales DM gua, gua sengaja mikir berkali-kali dulu mau bales apa. Biar apa? Biar lu gak marah, dan biar obrolan kita tuh bisa nambah asik ke depannya.</p>

      <p>Inget masalah matcha kemarin? Apesnya lu, apesnya gua juga kan? Gara-gara salah transfer itu, gua mikir... emang kita kayaknya gabisa dipisah-pisahin, Zah. <span class="heart-beat">❤️</span></p>
    </div>

    <div class="scroll-footer">— sealed with gold & sincerity —</div>

  </div>
</div>
"""

# ── Render ke Streamlit ────────────────────────────────────────────────────────
st.markdown(pesan_zizah_html, unsafe_allow_html=True)
