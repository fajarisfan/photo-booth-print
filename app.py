import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance, ImageFilter
import io
import numpy as np
import math
import base64
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import datetime

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Photo Booth · Zizah",
    page_icon="📸",
    layout="centered",
)

# ── CSS — Flutter Mobile Design System ────────────────────────────────────────
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@700&display=swap" rel="stylesheet">
<style>
:root {
    --bg:        #0D0D0D;
    --surface:   #1A1A1A;
    --surface2:  #242424;
    --card:      #1E1E1E;
    --border:    #2E2E2E;
    --primary:   #F5C518;
    --primary-dk:#D4A800;
    --primary-bg:#2A2400;
    --success:   #00C853;
    --text:      #F0F0F0;
    --text2:     #AAAAAA;
    --text3:     #555555;
    --radius:    16px;
    --radius-sm: 12px;
    --font:      'Inter', system-ui, sans-serif;
    --mono:      'JetBrains Mono', monospace;
}
html, body, .stApp { background: var(--bg) !important; font-family: var(--font) !important; color: var(--text) !important; }
.main .block-container { padding: 0 12px 100px 12px !important; max-width: 460px !important; margin: 0 auto !important; }

/* AppBar */
.appbar {
    background: rgba(26,26,26,0.96);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    padding: 14px 16px 12px;
    margin: 0 -12px 16px -12px;
    display: flex; align-items: center; gap: 10px;
    position: sticky; top: 0; z-index: 100;
}
.appbar-icon { font-size: 22px; }
.appbar-title { font-family: var(--mono); font-size: 15px; font-weight: 700; color: var(--primary); letter-spacing: 1px; }
.appbar-sub { font-size: 10px; color: var(--text3); letter-spacing: 0.5px; }

/* Bottom Nav */
.bottom-nav {
    position: fixed; bottom: 0; left: 0; right: 0; z-index: 200;
    background: rgba(20,20,20,0.97);
    backdrop-filter: blur(16px);
    border-top: 1px solid var(--border);
    display: flex;
    max-width: 460px; margin: 0 auto;
}
.bnav-item {
    flex: 1; display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    padding: 10px 0 12px;
    cursor: pointer; gap: 3px;
    text-decoration: none;
    transition: all 0.15s;
}
.bnav-icon { font-size: 20px; line-height: 1; }
.bnav-label { font-size: 10px; font-weight: 600; letter-spacing: 0.3px; color: var(--text3); }
.bnav-item.active .bnav-label { color: var(--primary); }
.bnav-item.active .bnav-icon { filter: drop-shadow(0 0 6px rgba(245,197,24,0.5)); }

/* Cards */
.fl-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px; margin: 8px 0;
}

/* Section label */
.section-label {
    font-size: 10px; font-weight: 700; letter-spacing: 1.5px;
    color: var(--text3); text-transform: uppercase;
    margin: 20px 0 10px 0;
}

/* Horizontal scroll row */
.hscroll {
    display: flex; gap: 10px; overflow-x: auto;
    padding: 4px 0 10px; margin: 0 -12px; padding-left: 12px;
    scrollbar-width: none;
}
.hscroll::-webkit-scrollbar { display: none; }

/* Filter chip */
.fchip {
    flex-shrink: 0;
    display: flex; flex-direction: column; align-items: center; gap: 5px;
    cursor: pointer;
}
.fchip-img {
    width: 64px; height: 64px; border-radius: 12px;
    border: 2px solid var(--border);
    object-fit: cover; transition: border-color 0.15s;
}
.fchip.active .fchip-img { border-color: var(--primary); box-shadow: 0 0 0 1px var(--primary); }
.fchip-name { font-size: 9px; font-weight: 600; color: var(--text3); letter-spacing: 0.2px; }
.fchip.active .fchip-name { color: var(--primary); }

/* Template chip */
.tchip {
    flex-shrink: 0; width: 90px;
    display: flex; flex-direction: column; align-items: center; gap: 6px;
    cursor: pointer;
}
.tchip-preview {
    width: 90px; height: 110px; border-radius: 10px;
    border: 2px solid var(--border);
    background: var(--surface2);
    display: flex; align-items: center; justify-content: center;
    font-size: 28px;
    transition: border-color 0.15s;
    overflow: hidden;
}
.tchip.active .tchip-preview { border-color: var(--primary); box-shadow: 0 0 0 1px var(--primary); }
.tchip-name { font-size: 9px; font-weight: 600; color: var(--text3); text-align: center; line-height: 1.3; }
.tchip.active .tchip-name { color: var(--primary); }

/* Buttons */
div[data-testid="stButton"] > button {
    background: var(--primary) !important; color: #000 !important;
    font-family: var(--font) !important; font-weight: 600 !important;
    font-size: 13px !important; border: none !important;
    border-radius: var(--radius-sm) !important;
    padding: 12px 16px !important; min-height: 44px !important;
    width: 100% !important;
    box-shadow: 0 2px 8px rgba(245,197,24,0.2) !important;
    transition: all 0.15s !important;
}
div[data-testid="stButton"] > button:hover { background: var(--primary-dk) !important; transform: translateY(-1px) !important; }
div[data-testid="stButton"] > button[kind="secondary"] {
    background: var(--surface2) !important; color: var(--text) !important;
    border: 1.5px solid var(--border) !important; box-shadow: none !important;
}
div[data-testid="stButton"] > button[kind="secondary"]:hover {
    border-color: var(--primary) !important; color: var(--primary) !important;
}
div[data-testid="stDownloadButton"] > button {
    background: var(--surface2) !important; color: var(--primary) !important;
    border: 1.5px solid var(--primary) !important;
    border-radius: var(--radius-sm) !important; min-height: 48px !important;
    font-weight: 600 !important; font-size: 13px !important;
}

/* Inputs */
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
    background: var(--surface) !important; border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-sm) !important; color: var(--text) !important;
    font-family: var(--font) !important; font-size: 13px !important;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 2px rgba(245,197,24,0.12) !important;
}
div[data-testid="stTextInput"] label,
div[data-testid="stTextArea"] label,
div[data-testid="stSelectbox"] label { color: var(--text2) !important; font-size: 12px !important; font-weight: 600 !important; }

/* Radio → segmented */
div[data-testid="stRadio"] > div {
    display: flex; gap: 6px; background: var(--surface);
    padding: 4px; border-radius: var(--radius-sm); border: 1px solid var(--border);
}
div[data-testid="stRadio"] label {
    flex: 1; text-align: center; padding: 8px 4px !important;
    border-radius: 10px !important; cursor: pointer;
    font-size: 12px !important; font-weight: 600 !important;
    color: var(--text2) !important; transition: all 0.15s;
}
div[data-testid="stRadio"] label:has(input:checked) { background: var(--primary) !important; color: #000 !important; }

/* Expander */
div[data-testid="stExpander"] {
    background: var(--surface) !important; border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important; margin: 6px 0 !important;
}
div[data-testid="stExpander"] summary { color: var(--text) !important; font-weight: 600 !important; font-size: 13px !important; }

/* Image */
div[data-testid="stImage"] img { border-radius: var(--radius-sm) !important; }

/* File uploader */
div[data-testid="stFileUploader"] {
    background: var(--surface) !important; border: 2px dashed var(--border) !important;
    border-radius: var(--radius) !important;
}

/* Caption */
div[data-testid="stCaptionContainer"] p { color: var(--text3) !important; font-size: 11px !important; }

/* Divider */
hr { border: none !important; border-top: 1px solid var(--border) !important; margin: 16px 0 !important; }

/* Preview label pill */
.preview-pill {
    display: inline-flex; align-items: center; gap: 5px;
    background: var(--primary); color: #000;
    padding: 3px 12px; border-radius: 100px;
    font-size: 10px; font-weight: 700; letter-spacing: 0.8px;
    text-transform: uppercase; margin-bottom: 10px;
}

/* Info box */
.info-box {
    background: var(--surface); border: 1px solid var(--border);
    border-left: 3px solid var(--success);
    border-radius: var(--radius-sm); padding: 10px 14px;
    color: var(--text2); font-size: 12px; line-height: 1.6; margin: 8px 0;
}

/* Empty state */
.empty-state {
    background: var(--card); border: 2px dashed var(--border);
    border-radius: var(--radius); padding: 40px 24px;
    display: flex; flex-direction: column; align-items: center;
    gap: 12px; text-align: center;
}

/* Selectbox */
div[data-testid="stSelectbox"] > div {
    background: var(--surface) !important; border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-sm) !important; color: var(--text) !important;
}

/* Slider */
div[data-testid="stSlider"] label { color: var(--text2) !important; font-size: 12px !important; }

/* Toggle */
div[data-testid="stToggle"] label { color: var(--text2) !important; font-size: 13px !important; }
</style>
""", unsafe_allow_html=True)

# ── Navigation State ───────────────────────────────────────────────────────────
if "nav" not in st.session_state:
    st.session_state.nav = "booth"

# Bottom nav via query params / buttons
q = st.query_params.get("tab", "booth")
if q != st.session_state.nav:
    st.session_state.nav = q

# ── Bottom Navigation HTML ─────────────────────────────────────────────────────
booth_active = "active" if st.session_state.nav == "booth" else ""
diary_active = "active" if st.session_state.nav == "diary" else ""

st.markdown(f"""
<div class="bottom-nav">
    <a class="bnav-item {booth_active}" href="?tab=booth">
        <span class="bnav-icon">📸</span>
        <span class="bnav-label">Photo Booth</span>
    </a>
    <a class="bnav-item {diary_active}" href="?tab=diary">
        <span class="bnav-icon">📔</span>
        <span class="bnav-label">Diary</span>
    </a>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ── TEMPLATE DEFINITIONS ──────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
TEMPLATES = {
    "pas_foto_2x3":   {"name":"Pas Foto 2×3","w":2.0,"h":3.0,"cols":4,"rows":4,"desc":"4×4 = 16 foto","icon":"🪪","bg_color":(255,255,255),"border":0,"style":"pasfoto"},
    "pas_foto_3x4":   {"name":"Pas Foto 3×4","w":3.0,"h":4.0,"cols":3,"rows":3,"desc":"3×3 = 9 foto","icon":"🪪","bg_color":(255,255,255),"border":0,"style":"pasfoto"},
    "pas_foto_4x6":   {"name":"Pas Foto 4×6","w":4.0,"h":6.0,"cols":2,"rows":2,"desc":"2×2 = 4 foto","icon":"📷","bg_color":(255,255,255),"border":0,"style":"pasfoto"},
    "strip_polaroid": {"name":"Strip Polaroid","w":6.0,"h":4.5,"cols":1,"rows":4,"desc":"1×4 strip polaroid","icon":"🎞️","bg_color":(245,240,230),"border":15,"style":"polaroid"},
    "photobooth_grid":{"name":"Photo Booth Grid","w":5.0,"h":4.0,"cols":2,"rows":2,"desc":"2×2 grid booth","icon":"🎠","bg_color":(20,20,20),"border":8,"style":"booth"},
    "filmstrip":      {"name":"Film Strip","w":5.5,"h":4.0,"cols":1,"rows":5,"desc":"1×5 roll film","icon":"🎬","bg_color":(10,10,10),"border":10,"style":"film"},
    "wallet_print":   {"name":"Wallet Print","w":6.35,"h":8.89,"cols":2,"rows":3,"desc":"2×3 = 6 foto wallet","icon":"💳","bg_color":(255,255,255),"border":4,"style":"wallet"},
    "studio_print":   {"name":"Studio Print","w":7.0,"h":9.5,"cols":2,"rows":2,"desc":"2×2 gaya studio","icon":"🏪","bg_color":(255,255,255),"border":6,"style":"studio"},
    "frame_classic":  {"name":"Classic Polaroid","w":8.0,"h":9.5,"cols":1,"rows":1,"desc":"Polaroid putih klasik","icon":"🟦","bg_color":(255,255,255),"border":0,"style":"frame_classic"},
    "frame_strip3":   {"name":"Strip Frame 3","w":6.5,"h":5.0,"cols":1,"rows":3,"desc":"1×3 strip soft","icon":"🎞️","bg_color":(255,255,255),"border":0,"style":"frame_strip3"},
    "frame_grid4":    {"name":"Grid Frame 2×2","w":7.0,"h":7.0,"cols":2,"rows":2,"desc":"2×2 aesthetic","icon":"⊞","bg_color":(255,255,255),"border":0,"style":"frame_grid4"},
    "frame_pink":     {"name":"Pink Girly","w":8.0,"h":9.5,"cols":1,"rows":1,"desc":"Frame pink pastel cute","icon":"🌸","bg_color":(255,220,230),"border":0,"style":"frame_pink"},
    "frame_dark":     {"name":"Dark Aesthetic","w":8.0,"h":9.5,"cols":1,"rows":1,"desc":"Frame hitam moody","icon":"🖤","bg_color":(20,20,20),"border":0,"style":"frame_dark"},
    "romance_filmstrip":{"name":"💕 Filmstrip Memories","w":5.5,"h":4.0,"cols":3,"rows":1,"desc":"3 foto horizontal romantis","icon":"🎞️","bg_color":(255,245,240),"border":0,"style":"romance_filmstrip"},
    "romance_destined": {"name":"💗 Destined Together","w":7.0,"h":9.5,"cols":1,"rows":1,"desc":"Frame ornamen romantis","icon":"💗","bg_color":(255,248,245),"border":0,"style":"romance_destined"},
    "romance_keepsake": {"name":"💛 Keepsake","w":10.0,"h":6.0,"cols":3,"rows":1,"desc":"3 foto keepsake vintage","icon":"💛","bg_color":(255,250,235),"border":0,"style":"romance_keepsake"},
    "romance_lovenotes":{"name":"💌 Love Notes","w":7.5,"h":9.5,"cols":1,"rows":1,"desc":"Amplop surat cinta","icon":"💌","bg_color":(255,248,240),"border":0,"style":"romance_lovenotes"},
    "grunge_strip4":  {"name":"🎸 Grunge Strip","w":6.0,"h":18.0,"cols":1,"rows":4,"desc":"4 foto B&W grunge","icon":"🎸","bg_color":(20,18,16),"border":0,"style":"grunge_strip4","custom_label":True},
}

# ── FILTERS ───────────────────────────────────────────────────────────────────
FILTERS = {
    "normal":     {"name":"Normal",      "icon":"🌟","desc":"Foto asli tanpa filter"},
    "grayscale":  {"name":"Hitam Putih", "icon":"⬛","desc":"Classic B&W"},
    "vintage":    {"name":"Vintage",     "icon":"🟤","desc":"Hangat & klasik"},
    "cool":       {"name":"Cool Blue",   "icon":"🔵","desc":"Tone dingin kebiruan"},
    "warm":       {"name":"Golden Hour", "icon":"🟡","desc":"Warm sunset tone"},
    "faded":      {"name":"Faded",       "icon":"🌫️","desc":"Low contrast dreamy"},
    "vivid":      {"name":"Vivid",       "icon":"🌈","desc":"Saturasi tinggi, pop!"},
    "sepia":      {"name":"Sepia",       "icon":"☕","desc":"Coklat antik"},
    "noir":       {"name":"Noir",        "icon":"🎭","desc":"High-contrast B&W"},
    "pastel":     {"name":"Pastel",      "icon":"🌸","desc":"Soft & dreamy pastel"},
    "neon":       {"name":"Neon",        "icon":"💜","desc":"Cyberpunk neon vibe"},
    "film_grain": {"name":"Film Grain",  "icon":"📼","desc":"Analog film texture"},
}

WATERMARK_POSITIONS = {
    "Kanan Bawah": "bottom_right", "Kiri Bawah": "bottom_left",
    "Kanan Atas": "top_right",     "Kiri Atas": "top_left",
    "Tengah": "center",
}

LOGO_FONTS = {
    "Bold (Default)": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "Regular": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "Italic": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
    "Mono": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
}

LOGO_SHAPES = {
    "none": "Tanpa Badge", "rectangle": "Kotak",
    "rounded_rect": "Kotak Rounded", "ellipse": "Oval/Lingkaran",
}

# ══════════════════════════════════════════════════════════════════════════════
# ── IMAGE PROCESSING FUNCTIONS (dipertahanin semua) ──────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
DPI = 300
CM_TO_PX = DPI / 2.54

def cm_to_px(val): return int(val * CM_TO_PX)

def fit_crop(img, target_w, target_h):
    img = img.convert("RGB")
    iw, ih = img.size
    ratio = max(target_w / iw, target_h / ih)
    nw, nh = int(iw * ratio), int(ih * ratio)
    img = img.resize((nw, nh), Image.LANCZOS)
    x, y = (nw - target_w) // 2, (nh - target_h) // 2
    return img.crop((x, y, x + target_w, y + target_h))

def apply_filter(img, filter_key):
    img = img.convert("RGB")
    arr = np.array(img, dtype=np.float32)
    if filter_key == "normal": return img
    elif filter_key == "grayscale": return img.convert("L").convert("RGB")
    elif filter_key == "vintage":
        arr[:,:,0] = np.clip(arr[:,:,0]*1.1+15,0,255)
        arr[:,:,1] = np.clip(arr[:,:,1]*0.95+5,0,255)
        arr[:,:,2] = np.clip(arr[:,:,2]*0.75,0,255)
        r = Image.fromarray(arr.astype(np.uint8))
        r = ImageEnhance.Contrast(r).enhance(0.85)
        return ImageEnhance.Brightness(r).enhance(1.05)
    elif filter_key == "cool":
        arr[:,:,0] = np.clip(arr[:,:,0]*0.85,0,255)
        arr[:,:,2] = np.clip(arr[:,:,2]*1.15+10,0,255)
        return ImageEnhance.Color(Image.fromarray(arr.astype(np.uint8))).enhance(1.1)
    elif filter_key == "warm":
        arr[:,:,0] = np.clip(arr[:,:,0]*1.15+20,0,255)
        arr[:,:,1] = np.clip(arr[:,:,1]*1.05+10,0,255)
        arr[:,:,2] = np.clip(arr[:,:,2]*0.80,0,255)
        return ImageEnhance.Brightness(Image.fromarray(arr.astype(np.uint8))).enhance(1.08)
    elif filter_key == "faded":
        arr = np.clip(arr*0.75+40,0,255)
        return ImageEnhance.Color(Image.fromarray(arr.astype(np.uint8))).enhance(0.7)
    elif filter_key == "vivid":
        r = ImageEnhance.Color(img).enhance(1.8)
        r = ImageEnhance.Contrast(r).enhance(1.2)
        return ImageEnhance.Sharpness(r).enhance(1.3)
    elif filter_key == "sepia":
        gray = np.array(img.convert("L"), dtype=np.float32)
        sepia = np.stack([np.clip(gray*1.1+20,0,255), np.clip(gray*0.9+10,0,255), np.clip(gray*0.7,0,255)], axis=2)
        return Image.fromarray(sepia.astype(np.uint8))
    elif filter_key == "noir":
        r = ImageEnhance.Contrast(img.convert("L").convert("RGB")).enhance(1.8)
        return ImageEnhance.Brightness(r).enhance(0.9)
    elif filter_key == "pastel":
        r = ImageEnhance.Color(img).enhance(0.6)
        a = np.clip(np.array(r, dtype=np.float32)*0.85+50,0,255)
        a[:,:,0] = np.clip(a[:,:,0]+8,0,255); a[:,:,2] = np.clip(a[:,:,2]+5,0,255)
        return Image.fromarray(a.astype(np.uint8))
    elif filter_key == "neon":
        arr[:,:,0] = np.clip(arr[:,:,0]*0.7,0,255)
        arr[:,:,1] = np.clip(arr[:,:,1]*0.6,0,255)
        arr[:,:,2] = np.clip(arr[:,:,2]*1.4+30,0,255)
        r = ImageEnhance.Contrast(Image.fromarray(arr.astype(np.uint8))).enhance(1.5)
        a = np.array(r, dtype=np.float32)
        mask = (a.mean(axis=2) > 128).astype(np.float32)
        a[:,:,0] = np.clip(a[:,:,0]+mask*30,0,255)
        return Image.fromarray(a.astype(np.uint8))
    elif filter_key == "film_grain":
        arr[:,:,0] = np.clip(arr[:,:,0]*1.05+5,0,255)
        arr[:,:,2] = np.clip(arr[:,:,2]*0.92,0,255)
        grain = np.random.normal(0,12,arr.shape[:2]+(3,)).astype(np.float32)
        arr = np.clip(arr+grain,0,255)
        return ImageEnhance.Contrast(Image.fromarray(arr.astype(np.uint8))).enhance(0.95)
    return img

def make_filter_thumb(photo, filter_key, size=80):
    w, h = photo.size
    side = min(w, h)
    x, y = (w-side)//2, (h-side)//2
    cropped = photo.crop((x, y, x+side, y+side))
    filtered = apply_filter(cropped, filter_key)
    return filtered.resize((size, size), Image.LANCZOS)

def preview_thumbnail(sheet, max_px=700):
    w, h = sheet.size
    ratio = min(max_px/w, max_px/h)
    return sheet.resize((int(w*ratio), int(h*ratio)), Image.LANCZOS)

def sheet_to_bytes(sheet, fmt="JPEG"):
    buf = io.BytesIO()
    sheet.convert("RGB").save(buf, fmt, quality=95)
    return buf.getvalue()

def sheet_to_pdf(sheet, tpl):
    img_bytes = sheet_to_bytes(sheet, "JPEG")
    buf = io.BytesIO()
    ONE_CM = 28.35
    sw, sh = sheet.size
    pagesize = (A4[1], A4[0]) if sw > sh else A4
    c = rl_canvas.Canvas(buf, pagesize=pagesize)
    pw, ph = pagesize
    margin = 0.5 * ONE_CM
    scale = min((pw-2*margin)/sw, (ph-2*margin)/sh)
    dw, dh = sw*scale, sh*scale
    c.drawImage(ImageReader(io.BytesIO(img_bytes)), (pw-dw)/2, (ph-dh)/2, dw, dh)
    c.setFont("Helvetica", 7); c.setFillColorRGB(0.6,0.6,0.6)
    c.drawString(margin, margin*0.4, f"Photo Booth  •  {tpl['name']}  •  {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
    c.save()
    return buf.getvalue()

def add_watermark(sheet, name="", logo_img=None, position="bottom_right", logo_size_pct=12, opacity=200):
    if not name and logo_img is None: return sheet
    sheet = sheet.copy().convert("RGBA")
    w, h = sheet.size
    overlay = Image.new("RGBA", (w, h), (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    mg = int(w*0.018)
    logo_resized = None
    if logo_img:
        lw, lh = logo_img.size
        scale = (int(w*logo_size_pct/100)) / max(lw,lh)
        logo_resized = logo_img.resize((int(lw*scale), int(lh*scale)), Image.LANCZOS).convert("RGBA")
        r,g,b,a = logo_resized.split()
        a = a.point(lambda v: int(v*opacity/255))
        logo_resized = Image.merge("RGBA",(r,g,b,a))
    text_w, text_h, font = 0, 0, None
    if name:
        try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", max(18, int(w*0.026)))
        except: font = ImageFont.load_default()
        bbox = draw.textbbox((0,0), name, font=font)
        text_w, text_h = bbox[2]-bbox[0], bbox[3]-bbox[1]
    gap = int(w*0.008)
    tw = (logo_resized.size[0] if logo_resized else 0) + (gap if logo_resized and name else 0) + text_w
    th = max(logo_resized.size[1] if logo_resized else 0, text_h)
    pos_map = {"bottom_right":(w-tw-mg,h-th-mg),"bottom_left":(mg,h-th-mg),"top_right":(w-tw-mg,mg),"top_left":(mg,mg),"center":((w-tw)//2,(h-th)//2)}
    ax, ay = pos_map.get(position, (w-tw-mg,h-th-mg))
    cx = ax
    if logo_resized:
        lw2, lh2 = logo_resized.size
        overlay.paste(logo_resized, (cx, ay+(th-lh2)//2), logo_resized)
        cx += lw2 + gap
    if name and font:
        ty = ay + (th-text_h)//2
        draw.text((cx+2,ty+2), name, fill=(0,0,0,160), font=font)
        draw.text((cx,ty), name, fill=(255,255,255,opacity), font=font)
    return Image.alpha_composite(sheet, overlay).convert("RGB")

def build_sheet(photo, tpl, filter_key):
    filtered = apply_filter(photo, filter_key)
    cols, rows = tpl["cols"], tpl["rows"]
    border = tpl.get("border", 0)
    bg = tpl["bg_color"]
    style = tpl["style"]
    DPI_ = 300; CM_ = DPI_/2.54
    def cm(v): return int(v*CM_)
    cell_w = cm(tpl["w"]); cell_h = cm(tpl["h"])
    if border > 0:
        framed = add_polaroid_frame(fit_crop(filtered, cell_w, cell_h), border, tpl)
        fw, fh = framed.size
    else:
        fw, fh = cell_w, cell_h
    gap = 0
    sheet_w = fw*cols + gap*(cols-1)
    sheet_h = fh*rows + gap*(rows-1)
    sheet = Image.new("RGB", (sheet_w, sheet_h), bg)
    for r in range(rows):
        for c in range(cols):
            x, y = c*(fw+gap), r*(fh+gap)
            cell = fit_crop(filtered, cell_w, cell_h)
            if border > 0: cell = add_polaroid_frame(cell, border, tpl)
            sheet.paste(cell, (x, y))
    return sheet

def add_polaroid_frame(img, border_px, tpl):
    style = tpl["style"]; bg = tpl["bg_color"]; pw, ph = img.size
    if style == "polaroid":
        fw = pw+border_px*2; fh = ph+border_px*2+int(border_px*2.5)
        frame = Image.new("RGB",(fw,fh),bg); frame.paste(img,(border_px,border_px)); return frame
    elif style == "film":
        fw = pw+border_px*2; fh = ph+border_px*2
        frame = Image.new("RGB",(fw,fh),bg); draw = ImageDraw.Draw(frame)
        hole_w = max(4,border_px//2); hole_h = max(8,border_px)
        for yi in range(3):
            yp = border_px+(ph//3)*yi+ph//6-hole_h//2
            for hx in [border_px//4, fw-border_px//4-hole_w]:
                draw.rounded_rectangle([hx,yp,hx+hole_w,yp+hole_h],radius=2,fill=(40,40,40))
        frame.paste(img,(border_px,border_px)); return frame
    elif style in ("booth","wallet"):
        fw = pw+border_px*2; fh = ph+border_px*2
        frame = Image.new("RGB",(fw,fh),bg); frame.paste(img,(border_px,border_px)); return frame
    return img

def build_frame_sheet(photo, tpl, filter_key):
    style = tpl["style"]; bg = tpl["bg_color"]
    DPI_ = 300; CM_ = DPI_/2.54
    def cm(v): return int(v*CM_)
    filtered = apply_filter(photo, filter_key)

    if style == "frame_classic":
        pw, ph = cm(tpl["w"]), cm(tpl["h"])
        pad_s, pad_t, pad_b = cm(0.6), cm(0.6), cm(1.8)
        cell = fit_crop(filtered, pw-pad_s*2, ph-pad_t-pad_b)
        sheet = Image.new("RGB",(pw,ph),bg); sheet.paste(cell,(pad_s,pad_t)); return sheet
    elif style == "frame_strip3":
        pw = cm(tpl["w"]); pad_s, pad_t, pad_b, gap = cm(0.5), cm(0.4), cm(1.2), cm(0.35)
        total_h = cm(tpl["h"])*3; sheet_h = pad_t+3*(total_h//3)+gap*4+pad_b+cm(0.5)
        cell_h = (sheet_h-pad_t-pad_b-gap*2)//3
        sheet = Image.new("RGB",(pw,sheet_h),bg); draw = ImageDraw.Draw(sheet)
        for i in range(3):
            y = pad_t+i*(cell_h+gap); cell = fit_crop(filtered,pw-pad_s*2,cell_h)
            draw.rectangle([pad_s-2,y-2,pad_s+pw-pad_s*2+2,y+cell_h+2],outline=(200,200,200),width=1)
            sheet.paste(cell,(pad_s,y))
        return sheet
    elif style == "frame_grid4":
        pw, ph = cm(tpl["w"]*1.2), cm(tpl["h"]*1.2)
        pad, gap = cm(0.55), cm(0.3)
        cw, ch = (pw-pad*2-gap)//2, (ph-pad*2-gap)//2
        sheet = Image.new("RGB",(pw,ph),bg); draw = ImageDraw.Draw(sheet)
        for r in range(2):
            for c in range(2):
                x, y = pad+c*(cw+gap), pad+r*(ch+gap)
                cell = fit_crop(filtered,cw,ch)
                draw.rectangle([x-2,y-2,x+cw+2,y+ch+2],outline=(210,210,210),width=1)
                sheet.paste(cell,(x,y))
        return sheet
    elif style == "frame_pink":
        pw, ph = cm(tpl["w"]), cm(tpl["h"])
        pad_s, pad_t, pad_b = cm(0.7), cm(0.7), cm(2.2)
        cell = fit_crop(filtered, pw-pad_s*2, ph-pad_t-pad_b)
        sheet = Image.new("RGB",(pw,ph),bg); draw = ImageDraw.Draw(sheet)
        dot = (255,170,195)
        for i in range(0,pw,cm(0.6)):
            draw.ellipse([i-3,3,i+3,9],fill=dot); draw.ellipse([i-3,ph-9,i+3,ph-3],fill=dot)
        for i in range(0,ph,cm(0.6)):
            draw.ellipse([3,i-3,9,i+3],fill=dot); draw.ellipse([pw-9,i-3,pw-3,i+3],fill=dot)
        sheet.paste(cell,(pad_s,pad_t)); return sheet
    elif style == "frame_dark":
        pw, ph = cm(tpl["w"]), cm(tpl["h"])
        pad_s, pad_t, pad_b = cm(0.5), cm(0.5), cm(1.5)
        cell = fit_crop(filtered, pw-pad_s*2, ph-pad_t-pad_b)
        sheet = Image.new("RGB",(pw,ph),bg); draw = ImageDraw.Draw(sheet)
        draw.rectangle([cm(0.15),cm(0.15),pw-cm(0.15),ph-cm(0.15)],outline=(60,60,60),width=3)
        sheet.paste(cell,(pad_s,pad_t)); return sheet
    elif style == "romance_filmstrip":
        DPI_=300; CM_=DPI_/2.54
        def cm2(v): return int(v*CM_)
        pw=cm2(tpl["w"]); ph=cm2(tpl["h"]); bg_col=(255,245,240)
        sheet=Image.new("RGB",(pw,ph),bg_col); draw=ImageDraw.Draw(sheet)
        pad=cm2(0.4); gap=cm2(0.3)
        cell_w=(pw-pad*2-gap*2)//3; cell_h=ph-pad*2
        for i in range(3):
            x=pad+i*(cell_w+gap); cell=fit_crop(filtered,cell_w,cell_h)
            draw.rectangle([x-2,pad-2,x+cell_w+2,pad+cell_h+2],outline=(230,200,190),width=2)
            sheet.paste(cell,(x,pad))
        try:
            f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",cm2(0.25))
        except: f=ImageFont.load_default()
        txt="♥ FILMSTRIP MEMORIES ♥"
        bb=draw.textbbox((0,0),txt,font=f)
        draw.text(((pw-(bb[2]-bb[0]))//2,ph-cm2(0.35)),txt,fill=(200,140,130),font=f)
        return sheet
    elif style == "romance_destined":
        DPI_=300; CM_=DPI_/2.54
        def cm2(v): return int(v*CM_)
        pw=cm2(tpl["w"]); ph=cm2(tpl["h"]); bg_col=(255,248,245)
        sheet=Image.new("RGB",(pw,ph),bg_col); draw=ImageDraw.Draw(sheet)
        brd=cm2(0.4)
        draw.rectangle([brd,brd,pw-brd,ph-brd],outline=(200,160,100),width=3)
        draw.rectangle([brd+8,brd+8,pw-brd-8,ph-brd-8],outline=(230,180,150),width=1)
        try:
            ft=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",cm2(0.5))
            fs=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",cm2(0.28))
        except: ft=fs=ImageFont.load_default()
        title="Destined Together"
        bb=draw.textbbox((0,0),title,font=ft)
        draw.text(((pw-(bb[2]-bb[0]))//2,cm2(0.5)),title,fill=(170,80,100),font=ft)
        draw.text(((pw-cm2(0.5))//2,cm2(1.1)),"♥",fill=(200,100,120),font=ft)
        pad_s=cm2(1.2); cell_top=cm2(2.0); cell_bot=cm2(2.2)
        iw=pw-pad_s*2; ih=ph-cell_top-cell_bot
        cell=fit_crop(filtered,iw,ih)
        draw.rectangle([pad_s-3,cell_top-3,pad_s+iw+3,cell_top+ih+3],outline=(200,160,100),width=3)
        sheet.paste(cell,(pad_s,cell_top))
        by=cell_top+ih+cm2(0.2)
        for i,(txt,col) in enumerate([("US AGAINST THE WORLD",(130,70,80)),("♥",(200,100,120)),("FOR: [Crush Name]",(120,90,100))]):
            fnt=ft if i==1 else fs
            bb=draw.textbbox((0,0),txt,font=fnt)
            draw.text(((pw-(bb[2]-bb[0]))//2,by+i*cm2(0.4)),txt,fill=col,font=fnt)
        return sheet
    elif style == "romance_keepsake":
        DPI_=300; CM_=DPI_/2.54
        def cm2(v): return int(v*CM_)
        pw=cm2(tpl["w"]); ph=cm2(tpl["h"]); bg_col=(255,250,235)
        sheet=Image.new("RGB",(pw,ph),bg_col); draw=ImageDraw.Draw(sheet)
        draw.rectangle([cm2(0.2),cm2(0.2),pw-cm2(0.2),ph-cm2(0.2)],outline=(210,160,80),width=3)
        try:
            ft=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",cm2(0.55))
            fs=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",cm2(0.3))
        except: ft=fs=ImageFont.load_default()
        bb=draw.textbbox((0,0),"KEEPSAKE",font=ft)
        draw.text((pw-(bb[2]-bb[0])-cm2(0.5),cm2(0.35)),"KEEPSAKE",fill=(180,100,60),font=ft)
        gap=cm2(0.35); mx=cm2(0.5); my=cm2(1.0); mby=cm2(1.5)
        ch=ph-my-mby; tw=(pw-mx*2-gap*2)//3; labels=["YOU.","ME.","TOGETHER."]
        for i,lbl in enumerate(labels):
            x=mx+i*(tw+gap); cell=fit_crop(filtered,tw,ch)
            draw.rectangle([x-2,my-2,x+tw+2,my+ch+2],outline=(200,160,80),width=2)
            sheet.paste(cell,(x,my))
            bb=draw.textbbox((0,0),lbl,font=fs)
            draw.text((x+(tw-(bb[2]-bb[0]))//2,my+ch+cm2(0.1)),lbl,fill=(180,130,60),font=fs)
        return sheet
    elif style == "romance_lovenotes":
        DPI_=300; CM_=DPI_/2.54
        def cm2(v): return int(v*CM_)
        pw=cm2(tpl["w"]); ph=cm2(tpl["h"]); bg_col=(255,248,240)
        sheet=Image.new("RGB",(pw,ph),bg_col); draw=ImageDraw.Draw(sheet)
        draw.rectangle([cm2(0.3),cm2(0.3),pw-cm2(0.3),ph-cm2(0.3)],outline=(210,170,140),width=4)
        draw.rectangle([cm2(0.6),cm2(0.6),pw-cm2(0.6),ph-cm2(0.6)],outline=(230,200,170),width=1)
        try:
            ft=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",cm2(0.6))
            fs=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",cm2(0.3))
        except: ft=fs=ImageFont.load_default()
        title="Love Notes"
        bb=draw.textbbox((0,0),title,font=ft)
        draw.text(((pw-(bb[2]-bb[0]))//2,cm2(0.6)),title,fill=(180,100,80),font=ft)
        pad_s=cm2(0.8); cell_top=cm2(1.8); cell_bot=cm2(1.8)
        iw=pw-pad_s*2; ih=ph-cell_top-cell_bot
        cell=fit_crop(filtered,iw,ih)
        draw.rectangle([pad_s-3,cell_top-3,pad_s+iw+3,cell_top+ih+3],outline=(200,150,120),width=3)
        sheet.paste(cell,(pad_s,cell_top))
        by=cell_top+ih+cm2(0.3)
        for i,(txt,col) in enumerate([("💌 a letter for you","(160,100,80)"),("with love, always","(180,130,110)")]):
            bb=draw.textbbox((0,0),txt,font=fs)
            draw.text(((pw-(bb[2]-bb[0]))//2,by+i*cm2(0.45)),txt,fill=eval(col),font=fs)
        return sheet
    elif style == "grunge_strip4":
        DPI_=300; CM_=DPI_/2.54
        def cm2(v): return int(v*CM_)
        pw=cm2(tpl["w"]); ph=cm2(tpl["h"]); bg_col=(20,18,16)
        sheet=Image.new("RGB",(pw,ph),bg_col); draw=ImageDraw.Draw(sheet)
        header_h=cm2(3.0); footer_h=cm2(3.0)
        content_h=ph-header_h-footer_h
        pad_x=cm2(0.3); cell_h=content_h//4-cm2(0.15)
        bw=apply_filter(photo,"noir")
        for i in range(4):
            cy=header_h+i*(cell_h+cm2(0.15)); cell=fit_crop(bw,pw-pad_x*2,cell_h)
            draw.rectangle([pad_x-2,cy-2,pad_x+pw-pad_x*2+2,cy+cell_h+2],outline=(90,82,68),width=2)
            sheet.paste(cell,(pad_x,cy))
        try:
            f_title=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",cm2(0.62))
            f_sub=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",cm2(0.32))
        except: f_title=f_sub=ImageFont.load_default()
        def dtc(txt,font,y,fill=(238,228,195)):
            bb=draw.textbbox((0,0),txt,font=font); tx=(pw-(bb[2]-bb[0]))//2
            draw.text((tx+2,y+2),txt,fill=(0,0,0),font=font)
            draw.text((tx,y),txt,fill=fill,font=font)
        label_lines=st.session_state.get("grunge_label","PHOTO\nBOOTH").split("\n")
        for_name=st.session_state.get("grunge_for_name","")
        for li,ln in enumerate(label_lines): dtc(ln,f_title,cm2(0.18)+li*cm2(0.75))
        if for_name:
            bb=draw.textbbox((0,0),f"FOR: {for_name.upper()}",font=f_sub)
            draw.text((pw-(bb[2]-bb[0])-cm2(0.3),cm2(0.2)),f"FOR: {for_name.upper()}",fill=(200,190,160),font=f_sub)
        footer_y=ph-footer_h+cm2(0.18)
        for li,ln in enumerate(label_lines): dtc(ln,f_title,footer_y+li*cm2(0.75))
        return sheet
    return build_sheet(photo, tpl, filter_key)

def build_studio_sheet(photo, tpl, filter_key, studio_name="oh! shoot", studio_sub="PHOTO STUDIO",
                        logo_font="Bold (Default)", logo_shape="none",
                        logo_text_color=(180,40,40), logo_badge_color=(255,255,255), logo_border_color=(200,200,200)):
    DPI_=300; CM_=DPI_/2.54
    def cm(v): return int(v*CM_)
    filtered=apply_filter(photo,filter_key)
    pw=cm(tpl["w"]); ph=cm(tpl["h"]); bg=(255,255,255)
    sheet=Image.new("RGB",(pw,ph),bg)
    logo_h=cm(1.4); gap=cm(0.25); border=cm(0.3)
    cols,rows=tpl["cols"],tpl["rows"]
    content_h=ph-logo_h-gap-border*2
    cell_w=(pw-border*2-gap*(cols-1))//cols
    cell_h=(content_h-gap*(rows-1))//rows
    for r in range(rows):
        for c in range(cols):
            x=border+c*(cell_w+gap); y=border+r*(cell_h+gap)
            cell=fit_crop(filtered,cell_w,cell_h)
            sheet.paste(cell,(x,y))
    logo_y=ph-logo_h
    logo_bg=Image.new("RGB",(pw,logo_h),(245,245,245))
    draw=ImageDraw.Draw(logo_bg)
    try:
        fp=LOGO_FONTS.get(logo_font,LOGO_FONTS["Bold (Default)"])
        fn=ImageFont.truetype(fp,cm(0.55))
        fs=ImageFont.truetype(fp,cm(0.28))
    except: fn=fs=ImageFont.load_default()
    bb=draw.textbbox((0,0),studio_name,font=fn)
    draw.text(((pw-(bb[2]-bb[0]))//2,(logo_h-(bb[3]-bb[1]))//2-cm(0.15)),studio_name,fill=logo_text_color,font=fn)
    bb2=draw.textbbox((0,0),studio_sub,font=fs)
    draw.text(((pw-(bb2[2]-bb2[0]))//2,(logo_h+(bb[3]-bb[1]))//2-cm(0.05)),studio_sub,fill=(120,120,120),font=fs)
    sheet.paste(logo_bg,(0,logo_y))
    return sheet

# ── Camera HTML ────────────────────────────────────────────────────────────────
def get_camera_html():
    return """<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{background:#0D0D0D;font-family:'Inter',system-ui,sans-serif;color:#F0F0F0;}
#wrap{position:relative;width:100%;max-width:440px;margin:0 auto;}
#video{width:100%;display:block;border-radius:16px;transform:scaleX(-1);}
#countdownOverlay{
  position:absolute;top:0;left:0;width:100%;height:100%;
  display:flex;align-items:center;justify-content:center;
  pointer-events:none;opacity:0;border-radius:16px;background:rgba(0,0,0,0.3);
}
#countdownNum{
  font-size:clamp(72px,20vw,120px);font-weight:700;color:#F5C518;
  text-shadow:0 0 40px rgba(245,197,24,0.6),0 2px 12px rgba(0,0,0,0.9);
}
#flash{position:absolute;top:0;left:0;width:100%;height:100%;background:white;border-radius:16px;opacity:0;pointer-events:none;transition:opacity 0.25s;}
#motionBar{width:100%;height:3px;background:#1E1E1E;border-radius:2px;margin-top:6px;}
#motionFill{height:100%;width:0%;background:#F5C518;transition:width 0.1s;border-radius:2px;}
#controls{
  display:flex;gap:10px;margin-top:10px;justify-content:center;align-items:center;
  background:rgba(26,26,26,0.95);padding:10px 14px;border-radius:20px;
  border:1px solid #2E2E2E;backdrop-filter:blur(12px);
}
#captureBtn{
  background:#F5C518;color:#000;border:none;border-radius:50%;
  width:64px;height:64px;font-size:22px;cursor:pointer;font-weight:700;
  box-shadow:0 0 0 4px #2A2400,0 4px 16px rgba(245,197,24,0.4);
  transition:transform 0.1s;flex-shrink:0;
}
#captureBtn:active{transform:scale(0.88);}
.tbtn{
  background:#1E1E1E;color:#AAA;border:1.5px solid #2E2E2E;
  border-radius:12px;padding:8px 12px;font-size:11px;cursor:pointer;
  font-family:'Inter',sans-serif;font-weight:600;transition:all 0.15s;
}
.tbtn.on{background:#2A2400;color:#F5C518;border-color:#F5C518;}
#status{text-align:center;font-size:11px;color:#555;margin-top:6px;min-height:16px;}
#hint{
  background:#1A1A1A;border:1px solid #2E2E2E;border-radius:12px;
  padding:10px 12px;margin-top:8px;text-align:center;font-size:11px;color:#555;line-height:1.7;
}
#previewBox{margin-top:12px;text-align:center;display:none;}
#previewImg{max-width:100%;border-radius:12px;border:2px solid #F5C518;}
#savedMsg{font-size:13px;color:#00C853;margin:6px 0;font-weight:600;}
#retakeBtn{
  width:100%;background:#1E1E1E;color:#F5C518;border:1.5px solid #F5C518;
  border-radius:12px;padding:12px;font-size:13px;font-weight:600;
  cursor:pointer;margin-top:8px;font-family:'Inter',sans-serif;
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
  <button class="tbtn on" id="autoBtn" onclick="toggleAuto()">🤏 Auto</button>
  <div style="display:flex;flex-direction:column;align-items:center;gap:3px;">
    <button id="captureBtn" onclick="startCapture()">📸</button>
    <span style="font-size:9px;color:#F5C518;font-weight:700;letter-spacing:1px;">JEPRET</span>
  </div>
  <button class="tbtn" id="timerBtn" onclick="toggleTimer()">⏱️ 3s</button>
</div>
<div id="status">Memulai kamera...</div>
<div id="hint">
  🤏 <b style="color:#F5C518;">Auto snap</b> — gerakkan tangan<br>
  atau tap <b style="color:#F5C518;">📸 JEPRET</b> manual
</div>
<div id="previewBox">
  <p id="savedMsg">✅ Foto tersimpan!</p>
  <img id="previewImg" src="" alt="preview">
  <button id="retakeBtn" onclick="retake()">🔄 Ambil Ulang</button>
</div>
<script>
const video=document.getElementById('video'),flash=document.getElementById('flash'),
  motionFill=document.getElementById('motionFill'),cdOverlay=document.getElementById('countdownOverlay'),
  cdNum=document.getElementById('countdownNum'),statusEl=document.getElementById('status'),
  previewBox=document.getElementById('previewBox'),previewImg=document.getElementById('previewImg');
let autoSnap=true,timerMode=false,capturing=false,previewMode=false,capturedUrl=null;
function toggleAuto(){autoSnap=!autoSnap;document.getElementById('autoBtn').classList.toggle('on',autoSnap);if(!autoSnap)motionFill.style.width='0%';}
function toggleTimer(){timerMode=!timerMode;document.getElementById('timerBtn').classList.toggle('on',timerMode);}
navigator.mediaDevices.getUserMedia({video:{facingMode:'user',width:{ideal:1280},height:{ideal:720}},audio:false})
.then(s=>{video.srcObject=s;video.onloadedmetadata=()=>{initMotion();statusEl.textContent='🤏 Gerakkan tangan untuk auto snap';}})
.catch(()=>{statusEl.textContent='❌ Kamera tidak dapat diakses';});
let prevFrame=null,motionScore=0,motionHold=0,snapCooldown=0;
const SAMPLE_W=160,SAMPLE_H=90,mCanvas=document.createElement('canvas'),mCtx=mCanvas.getContext('2d',{willReadFrequently:true});
function initMotion(){mCanvas.width=SAMPLE_W;mCanvas.height=SAMPLE_H;requestAnimationFrame(motionLoop);}
function motionLoop(){
  requestAnimationFrame(motionLoop);
  if(previewMode||capturing||video.readyState<2)return;
  mCtx.drawImage(video,0,0,SAMPLE_W,SAMPLE_H);
  const curr=mCtx.getImageData(0,0,SAMPLE_W,SAMPLE_H).data;
  if(!prevFrame){prevFrame=new Uint8ClampedArray(curr);return;}
  let diff=0;
  for(let i=0;i<curr.length;i+=4){if((Math.abs(curr[i]-prevFrame[i])+Math.abs(curr[i+1]-prevFrame[i+1])+Math.abs(curr[i+2]-prevFrame[i+2]))/3>10)diff++;}
  prevFrame.set(curr);
  const ratio=diff/(SAMPLE_W*SAMPLE_H);
  motionScore=motionScore*0.7+ratio*0.3;
  motionFill.style.width=Math.min(100,motionScore*800)+'%';
  motionFill.style.background=motionScore>0.04?'#00C853':'#F5C518';
  if(motionScore>0.04){motionHold++;}else{motionHold=0;}
  if(snapCooldown>0)snapCooldown--;
  if(autoSnap&&motionHold>=5&&!capturing&&snapCooldown===0){motionHold=0;snapCooldown=60;startCapture();}
  if(!capturing)statusEl.textContent=motionScore>0.04?'✋ Gerakan terdeteksi...':(autoSnap?'🤏 Gerakkan tangan untuk auto snap':'📸 Tap jepret untuk foto');
}
function startCapture(){if(capturing||previewMode)return;timerMode?runCountdown(3):doSnap();}
function runCountdown(n){if(n<=0){doSnap();return;}capturing=true;cdNum.textContent=n;cdOverlay.style.opacity='1';cdNum.style.transform='scale(1.3)';cdNum.style.transition='transform 0.15s';setTimeout(()=>{cdNum.style.transform='scale(1)'},150);setTimeout(()=>runCountdown(n-1),1000);}
function doSnap(){
  cdOverlay.style.opacity='0';capturing=false;
  flash.style.transition='';flash.style.opacity='1';
  setTimeout(()=>{flash.style.transition='opacity 0.3s';flash.style.opacity='0';},60);
  const cap=document.createElement('canvas');cap.width=video.videoWidth||1280;cap.height=video.videoHeight||720;
  const cc=cap.getContext('2d');cc.translate(cap.width,0);cc.scale(-1,1);cc.drawImage(video,0,0,cap.width,cap.height);
  capturedUrl=cap.toDataURL('image/jpeg',0.93);
  function inject(url){
    try{
      const frames=[window,window.parent,window.top];
      for(const f of frames){try{const tas=f.document.querySelectorAll('textarea');for(const ta of tas){if((ta.getAttribute('aria-label')||'')==='cam_bridge_ta'){const s=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;s.call(ta,url);ta.dispatchEvent(new Event('input',{bubbles:true}));ta.dispatchEvent(new Event('change',{bubbles:true}));ta.focus();ta.blur();return true;}}}catch(e){}}
    }catch(e){}return false;
  }
  let tries=0;function tryInject(){if(inject(capturedUrl))return;tries++;if(tries<5)setTimeout(tryInject,400);}tryInject();
  previewImg.src=capturedUrl;previewBox.style.display='block';previewMode=true;statusEl.textContent='✅ Foto tersimpan!';
}
function retake(){capturedUrl=null;previewBox.style.display='none';previewMode=false;prevFrame=null;snapCooldown=30;motionHold=0;motionScore=0;}
</script>
</body>
</html>"""

# ══════════════════════════════════════════════════════════════════════════════
# ── SESSION STATE ─────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
defaults = {
    "photo": None, "selected_tpl": "frame_pink", "selected_filter": "normal",
    "grunge_label": "PHOTO\nBOOTH", "grunge_for_name": "",
    "studio_name": "oh! shoot", "studio_sub": "NEW WAVE PHOTO STUDIO",
    "watermark_name": "", "watermark_logo": None,
    "watermark_position": "Kanan Bawah", "watermark_logo_size": 12,
    "watermark_opacity": 200, "logo_font": "Bold (Default)",
    "logo_shape": "none", "logo_text_color_hex": "#b42828",
    "logo_badge_color_hex": "#ffffff", "logo_border_color_hex": "#cccccc",
    "surat_step": 0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# ── APPBAR ────────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
nav = st.session_state.nav

if nav == "booth":
    st.markdown("""
    <div class="appbar">
      <span class="appbar-icon">📸</span>
      <div>
        <div class="appbar-title">PHOTO BOOTH</div>
        <div class="appbar-sub">pilih frame · filter · download</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="appbar">
      <span class="appbar-icon">📔</span>
      <div>
        <div class="appbar-title">DIARY</div>
        <div class="appbar-sub">ruang kamu sendiri</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ── PHOTO BOOTH TAB ───────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
if nav == "booth":

    # ── 1. Ambil Foto ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">1 · Ambil Foto</div>', unsafe_allow_html=True)

    input_mode = st.radio("Sumber", ["📷 Kamera", "📁 Upload"], horizontal=True, label_visibility="collapsed")

    if input_mode == "📷 Kamera":
        components.html(get_camera_html(), height=780, scrolling=False)

        st.markdown("""<style>
        div[data-testid="stTextArea"]:has(textarea[aria-label="cam_bridge_ta"]){
            position:fixed!important;left:-9999px!important;top:-9999px!important;
            opacity:0!important;pointer-events:none!important;width:1px!important;height:1px!important;
        }
        </style>""", unsafe_allow_html=True)
        raw_b64 = st.text_area("cam_bridge_ta", key="cam_bridge_ta", label_visibility="collapsed", height=1)

        if (raw_b64 and isinstance(raw_b64, str) and raw_b64.strip().startswith("data:image")
                and not st.session_state.get("_photo_saved")):
            try:
                _, b64data = raw_b64.strip().split(",", 1)
                img = Image.open(io.BytesIO(base64.b64decode(b64data))).convert("RGB")
                st.session_state.photo = img
                st.session_state["_photo_saved"] = True
            except Exception as e:
                st.error(f"❌ Gagal proses foto: {e}")
            st.rerun()

        if not (raw_b64 and isinstance(raw_b64, str) and raw_b64.strip().startswith("data:image")):
            st.session_state["_photo_saved"] = False

        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        st.caption("Kamera di atas nggak jalan? Pakai tombol di bawah:")
        cam_fb = st.camera_input("", label_visibility="collapsed", key="cam_fallback")
        if cam_fb and st.session_state.get("_last_fb") != id(cam_fb):
            st.session_state.photo = Image.open(cam_fb).convert("RGB")
            st.session_state["_last_fb"] = id(cam_fb)
            st.rerun()

    else:
        uploaded = st.file_uploader("Upload foto (JPG, PNG)", type=["jpg","jpeg","png","webp"], label_visibility="visible")
        if uploaded:
            st.session_state.photo = Image.open(uploaded).convert("RGB")
            st.success("✅ Foto berhasil diupload!")

    if st.session_state.photo:
        st.success("✅ Foto siap — pilih frame & filter di bawah!")
        with st.expander("👁️ Lihat foto asli"):
            st.image(st.session_state.photo, use_container_width=True)

    st.divider()

    # ── 2. Pilih Template ─────────────────────────────────────────────────────
    st.markdown('<div class="section-label">2 · Pilih Frame / Template</div>', unsafe_allow_html=True)

    # Horizontal scroll template picker
    tpl_keys = list(TEMPLATES.keys())
    tpl_html = '<div class="hscroll">'
    for k in tpl_keys:
        t = TEMPLATES[k]
        active = "active" if st.session_state.selected_tpl == k else ""
        tpl_html += f"""
        <div class="tchip {active}" onclick="selectTpl('{k}')">
          <div class="tchip-preview">{t['icon']}</div>
          <div class="tchip-name">{t['name']}</div>
        </div>"""
    tpl_html += "</div>"

    st.markdown(tpl_html, unsafe_allow_html=True)

    # JS → Streamlit bridge untuk template selection
    st.markdown("""
    <script>
    function selectTpl(key) {
      const ta = window.parent.document.querySelector('textarea[aria-label="tpl_bridge"]');
      if(ta){
        const s=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;
        s.call(ta,key);ta.dispatchEvent(new Event('input',{bubbles:true}));ta.focus();ta.blur();
      }
    }
    </script>
    """, unsafe_allow_html=True)

    # Fallback: grid buttons untuk pilih template
    st.caption("Atau tap di bawah untuk pilih:")
    for i in range(0, len(tpl_keys), 3):
        cols_t = st.columns(3)
        for j, col in enumerate(cols_t):
            if i+j < len(tpl_keys):
                k = tpl_keys[i+j]; t = TEMPLATES[k]
                sel = st.session_state.selected_tpl == k
                with col:
                    if st.button(f"{'✅' if sel else t['icon']} {t['name']}", key=f"tpl_{k}",
                                 use_container_width=True, type="primary" if sel else "secondary"):
                        st.session_state.selected_tpl = k
                        st.rerun()
                    st.caption(t['desc'])

    tpl_key = st.session_state.selected_tpl
    if tpl_key not in TEMPLATES: tpl_key = list(TEMPLATES.keys())[0]; st.session_state.selected_tpl = tpl_key
    tpl = TEMPLATES[tpl_key]

    st.markdown(f"""
    <div class="info-box">
      <b>{tpl['icon']} {tpl['name']}</b> &nbsp;·&nbsp; {tpl['w']}×{tpl['h']} cm &nbsp;·&nbsp; {tpl['cols']}×{tpl['rows']} foto
    </div>
    """, unsafe_allow_html=True)

    # Grunge custom
    if tpl_key == "grunge_strip4":
        gc1, gc2 = st.columns(2)
        with gc1:
            gl = st.text_input("Judul (pakai \\n untuk baris baru)", value=st.session_state.grunge_label, key="grunge_label_input", max_chars=40)
            st.session_state.grunge_label = gl
        with gc2:
            gf = st.text_input("FOR: [nama]", value=st.session_state.grunge_for_name, key="grunge_for_input", max_chars=20)
            st.session_state.grunge_for_name = gf

    # Studio custom
    if tpl_key == "studio_print":
        sc1, sc2 = st.columns(2)
        with sc1:
            sn = st.text_input("🏪 Nama Studio", value=st.session_state.studio_name, key="studio_name_input", max_chars=30)
            st.session_state.studio_name = sn
        with sc2:
            ss = st.text_input("📝 Tagline", value=st.session_state.studio_sub, key="studio_sub_input", max_chars=40)
            st.session_state.studio_sub = ss

    st.divider()

    # ── 3. Pilih Filter ───────────────────────────────────────────────────────
    st.markdown('<div class="section-label">3 · Pilih Filter</div>', unsafe_allow_html=True)

    if st.session_state.photo:
        photo = st.session_state.photo
        current_filter = st.session_state.selected_filter
        filter_keys = list(FILTERS.keys())

        # Thumbnail grid 4 kolom
        THUMB_COLS = 4
        for row_start in range(0, len(filter_keys), THUMB_COLS):
            row_keys = filter_keys[row_start:row_start+THUMB_COLS]
            cols_f = st.columns(THUMB_COLS)
            for i, fkey in enumerate(row_keys):
                fdata = FILTERS[fkey]
                is_active = current_filter == fkey
                thumb = make_filter_thumb(photo, fkey, size=80)
                with cols_f[i]:
                    st.image(thumb, use_container_width=True)
                    if st.button(fdata['icon'], key=f"filter_{fkey}", use_container_width=True,
                                 type="primary" if is_active else "secondary", help=fdata['name']):
                        st.session_state.selected_filter = fkey
                        st.rerun()
                    st.markdown(f'<div style="font-size:9px;text-align:center;color:{"#F5C518" if is_active else "#555"};font-weight:{"700" if is_active else "500"};margin-top:2px">{fdata["name"]}</div>', unsafe_allow_html=True)

        active_f = FILTERS[current_filter]
        st.markdown(f'<div class="info-box">Filter: <b>{active_f["icon"]} {active_f["name"]}</b> — {active_f["desc"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state"><div style="font-size:32px;opacity:0.3">🎨</div><div style="color:#555;font-size:12px">Ambil foto dulu untuk preview filter</div></div>', unsafe_allow_html=True)

    st.divider()

    # ── 4. Watermark ──────────────────────────────────────────────────────────
    with st.expander("🏷️ Watermark & Logo (opsional)"):
        wc1, wc2 = st.columns(2)
        with wc1:
            wm = st.text_input("Teks watermark", value=st.session_state.watermark_name, key="wm_input", max_chars=30, placeholder="contoh: Zizah Studio")
            st.session_state.watermark_name = wm
        with wc2:
            wm_pos = st.selectbox("Posisi", list(WATERMARK_POSITIONS.keys()),
                                   index=list(WATERMARK_POSITIONS.keys()).index(st.session_state.watermark_position), key="wm_pos_sel")
            st.session_state.watermark_position = wm_pos
        wm_logo_file = st.file_uploader("Upload Logo PNG", type=["png","jpg","jpeg","webp"], key="wm_logo_upload")
        if wm_logo_file:
            st.session_state.watermark_logo = Image.open(wm_logo_file).convert("RGBA")
            st.success("✅ Logo terupload!")
        if st.session_state.watermark_logo:
            wpc1, wpc2 = st.columns([1,2])
            with wpc1: st.image(st.session_state.watermark_logo, width=60)
            with wpc2:
                lsz = st.slider("Ukuran logo (%)", 5, 30, st.session_state.watermark_logo_size, key="wm_logo_size")
                st.session_state.watermark_logo_size = lsz
                opac = st.slider("Opacity", 50, 255, st.session_state.watermark_opacity, key="wm_opacity")
                st.session_state.watermark_opacity = opac
            if st.button("🗑️ Hapus Logo", key="wm_logo_del"):
                st.session_state.watermark_logo = None; st.rerun()
        else:
            lsz = st.session_state.watermark_logo_size
            opac = st.session_state.watermark_opacity

    st.divider()

    # ── 5. Preview & Download ─────────────────────────────────────────────────
    st.markdown('<div class="section-label">4 · Preview & Download</div>', unsafe_allow_html=True)

    if st.session_state.photo is None:
        st.markdown("""
        <div class="empty-state">
          <div style="font-size:48px;opacity:0.2">📸</div>
          <div style="font-family:var(--mono);font-size:15px;font-weight:700;color:var(--primary);letter-spacing:2px;">SIAP UNTUK FOTO?</div>
          <div style="color:var(--text3);font-size:12px;line-height:1.8;">Ambil foto dengan 📷 Kamera<br>atau 📁 Upload dari galeri</div>
          <div style="background:var(--primary);color:#000;padding:5px 18px;border-radius:100px;font-size:11px;font-weight:700;">↑ SCROLL KE ATAS</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        current_filter = st.session_state.selected_filter
        active_f = FILTERS[current_filter]

        def _hex_to_rgb(h):
            h = h.lstrip("#"); return tuple(int(h[i:i+2],16) for i in (0,2,4))

        with st.spinner("⚙️ Membuat preview..."):
            if tpl_key == "studio_print":
                sheet = build_studio_sheet(st.session_state.photo, tpl, current_filter,
                    st.session_state.studio_name, st.session_state.studio_sub,
                    logo_font=st.session_state.logo_font, logo_shape=st.session_state.logo_shape,
                    logo_text_color=_hex_to_rgb(st.session_state.logo_text_color_hex),
                    logo_badge_color=_hex_to_rgb(st.session_state.logo_badge_color_hex),
                    logo_border_color=_hex_to_rgb(st.session_state.logo_border_color_hex))
            elif tpl["style"].startswith("frame_") or tpl["style"].startswith("romance_"):
                sheet = build_frame_sheet(st.session_state.photo, tpl, current_filter)
            else:
                sheet = build_sheet(st.session_state.photo, tpl, current_filter)
            thumb = preview_thumbnail(sheet, max_px=700)

        show_before = st.toggle("👁️ Before / After", value=False)
        if show_before:
            if tpl_key == "studio_print":
                sb = build_studio_sheet(st.session_state.photo, tpl, "normal",
                    st.session_state.studio_name, st.session_state.studio_sub)
            elif tpl["style"].startswith("frame_") or tpl["style"].startswith("romance_"):
                sb = build_frame_sheet(st.session_state.photo, tpl, "normal")
            else:
                sb = build_sheet(st.session_state.photo, tpl, "normal")
            bc1, bc2 = st.columns(2)
            with bc1:
                st.markdown('<div class="preview-pill">BEFORE</div>', unsafe_allow_html=True)
                st.image(preview_thumbnail(sb, 400), use_container_width=True)
            with bc2:
                st.markdown(f'<div class="preview-pill">AFTER · {active_f["name"]}</div>', unsafe_allow_html=True)
                st.image(thumb, use_container_width=True)
        else:
            st.markdown(f'<div class="preview-pill">PREVIEW · {active_f["icon"]} {active_f["name"]}</div>', unsafe_allow_html=True)
            st.image(thumb, use_container_width=True, caption=f"{tpl['name']} — siap cetak")

        sheet_wm = add_watermark(sheet, st.session_state.watermark_name,
            logo_img=st.session_state.watermark_logo,
            position=WATERMARK_POSITIONS.get(st.session_state.watermark_position,"bottom_right"),
            logo_size_pct=st.session_state.watermark_logo_size,
            opacity=st.session_state.watermark_opacity)

        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        d1, d2 = st.columns(2)
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        with d1:
            st.download_button("⬇️ Download JPG", sheet_to_bytes(sheet_wm,"JPEG"),
                f"photobooth_{tpl_key}_{current_filter}_{ts}.jpg", "image/jpeg", use_container_width=True)
        with d2:
            st.download_button("⬇️ Download PDF", sheet_to_pdf(sheet_wm, tpl),
                f"photobooth_{tpl_key}_{current_filter}_{ts}.pdf", "application/pdf", use_container_width=True)

        # Wallpaper S24 FE
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        with st.expander("📱 Wallpaper Samsung S24 FE"):
            def make_wallpaper(img):
                img = img.convert("RGB"); sw, sh = img.size; tr = 1080/2340; sr = sw/sh
                if sr > tr: nw=int(sh*tr); img=img.crop(((sw-nw)//2,0,(sw-nw)//2+nw,sh))
                else: nh=int(sw/tr); img=img.crop((0,(sh-nh)//2,sw,(sh-nh)//2+nh))
                return img.resize((1080,2340), Image.LANCZOS)
            wp1, wp2 = st.columns(2)
            with wp1:
                wa = make_wallpaper(st.session_state.photo)
                buf1 = io.BytesIO(); wa.save(buf1,"JPEG",quality=95)
                st.download_button("📷 Asli", buf1.getvalue(), "wallpaper_asli.jpg", "image/jpeg", use_container_width=True)
            with wp2:
                wb = make_wallpaper(sheet_wm)
                buf2 = io.BytesIO(); wb.save(buf2,"JPEG",quality=95)
                st.download_button("🎨 + Filter", buf2.getvalue(), "wallpaper_edited.jpg", "image/jpeg", use_container_width=True)

    st.divider()

    # ── Pesan & Doa ───────────────────────────────────────────────────────────
    API_URL = "https://izfa-api.vercel.app"

    st.markdown("""
    <div style="background:linear-gradient(135deg,#1a1218,#1f1a1f);border:1px solid #3d2b3d;
                border-radius:16px;padding:20px;margin:8px 0;text-align:center;">
      <div style="font-size:13px;color:#c8a040;letter-spacing:1.5px;font-weight:700;margin-bottom:6px;">💌 PESAN UNTUK DEVELOPER</div>
      <div style="font-size:12px;color:#888;line-height:1.7;">Aplikasi ini dibuat dengan sepenuh hati.<br>Tidak ada yang diminta selain doa & pesan baikmu. 🙏</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        import requests as req_lib
        r = req_lib.get(f"{API_URL}/doa/count", timeout=3)
        total = r.json().get("total", 0)
        st.markdown(f'<div style="text-align:center;font-size:12px;color:#888;margin:8px 0;">🌟 {total} orang sudah mengirim doa & pesan</div>', unsafe_allow_html=True)
    except:
        st.markdown('<div style="text-align:center;font-size:12px;color:#888;margin:8px 0;">🌟 Jadilah yang pertama mengirim doa ✨</div>', unsafe_allow_html=True)

    with st.form("form_doa", clear_on_submit=True):
        nama = st.text_input("Nama kamu (boleh anonim)", placeholder="contoh: Zizah 💕", max_chars=40)
        pesan = st.text_area("Pesan & saran 💬", placeholder="Tulis pesanmu di sini...", max_chars=500, height=100)
        doa = st.text_area("Doa untuk developer 🙏 (opsional)", placeholder="contoh: Semoga rezekinya lancar...", max_chars=300, height=70)
        components.html("""<script>
        const ua=navigator.userAgent;
        const el=window.parent.document.querySelector('input[aria-label="device_info_hidden"]');
        if(el){el.value=ua;el.dispatchEvent(new Event('input',{bubbles:true}));}
        </script>""", height=0)
        device_info = st.text_input("device_info_hidden", key="device_info", label_visibility="collapsed")
        submitted = st.form_submit_button("💌 Kirim Pesan & Doa", use_container_width=True)
        if submitted:
            if not pesan.strip(): st.warning("Tulis pesan dulu ya 😊")
            else:
                try:
                    import requests as req_lib
                    payload = {"nama":nama.strip() or "Anonim","pesan":pesan.strip(),"doa":doa.strip(),"device":device_info[:200] if device_info else ""}
                    r = req_lib.post(f"{API_URL}/doa", json=payload, timeout=5)
                    data = r.json()
                    if data.get("status") == "ok":
                        st.success(f"✅ {data['pesan']}"); st.info(f"📍 Dari: **{data.get('lokasi','?')}**"); st.balloons()
                    else: st.error("Gagal mengirim 😢")
                except Exception as ex: st.error(f"Koneksi gagal: {ex}")

    st.divider()
    st.markdown("""
    <div style="text-align:center;padding:14px;background:#1a0f0f;border-radius:12px;border:1px solid #333;">
      <div style="color:#c8a040;font-size:13px;font-weight:700;letter-spacing:1px;margin-bottom:6px;">TENTANG DEVELOPER</div>
      <div style="color:#c8b89a;font-size:12px;line-height:1.8;">
        Dibuat oleh <b style="color:#c8a040;">Isfan Fajar Anugrah</b><br>
        IT Support · Python Developer · Serang, Banten<br>
        <span style="font-size:11px;color:#666;">Dibuat dengan cinta dan kopi ☕<br>semoga bermanfaat untuk kamu 💛</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Pesan Rahasia untuk Zizah ─────────────────────────────────────────────
    STEPS = [
        {"type":"intro","content":"Ada sesuatu yang pengen gua ceritain...","btn":"Lanjut →"},
        {"type":"image","content":"https://i.postimg.cc/2Sc9t3vH/Screenshot-20260604-150953.png","caption":"Ini bukan rekayasa, Zah.","btn":"Terus..."},
        {"type":"text","content":"Kemarin gua dapet panggilan interview di Jakarta. Udah gua siapin semuanya — termasuk app photo booth ini, buat ngerayain kalau goals.","btn":"Terus..."},
        {"type":"text","content":"Tapi situasi di rumah lagi nggak kondusif. Jadi ya... gagal berangkat.","btn":"Masih mau dengerin?"},
        {"type":"text","content":"Nggak tau kenapa pengen cerita ke lu juga. Mungkin karena tanpa lu sadar, lu udah ngaruh ke hidup gua lebih dari yang lu kira.","btn":"Serius?"},
        {"type":"text","content":"Serius. Dari postingan lu di TikTok — yang bahkan bukan buat gua — baru kali ini gua ngerasa nggak terpaksa buat berubah. Gua putus sama kebiasaan lama, bukan karena disuruh, tapi karena lu tanpa sadar kasih alasan yang lebih kuat.","btn":"..."},
        {"type":"text","content":"Inget drama kemarin? Apesnya lu salah transfer, apesnya gua matcha nyangkut di security wkwk. Gara-gara itu gua mikir... emang kita kayaknya gabisa dipisah-pisahin, Zah. 😅❤️","btn":"Terus gimana?"},
        {"type":"final","content":"Nomor gua masih sama, aktif 24 jam. Pintu gua selalu kebuka — kalau lu mau cerita, nanya, atau sekadar bilang halo. Matcha yang gagal kemarin tetep bakal gua ganti kok, ntar gua DM lagi. Doain gua ya, Zah 🙏","btn":"💬 Hubungi Fajar di WA","wa_number":"6289XXXXXXXX"},
    ]

    step = st.session_state.surat_step
    if step == 0:
        st.markdown('<div style="text-align:center;margin-top:24px;"><div style="font-size:12px;color:#444;margin-bottom:12px;font-style:italic;">scroll sampai bawah dulu ya...</div></div>', unsafe_allow_html=True)
        if st.button("💌  ada sesuatu buat kamu, Zah", use_container_width=True):
            st.session_state.surat_step = 1; st.rerun()
    else:
        current = STEPS[step-1]
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1a1218,#1f1a1f);border:1px solid #3d2b3d;
                    border-radius:16px;padding:24px 20px;margin:8px 0;">
          <div style="font-size:10px;color:#555;letter-spacing:2px;margin-bottom:12px;">{step} / {len(STEPS)}</div>
        """, unsafe_allow_html=True)
        if current["type"] == "image":
            st.image(current["content"], use_container_width=True, caption=current.get("caption",""))
        elif current["type"] == "intro":
            st.markdown(f'<p style="color:#e8c4d8;font-size:20px;font-weight:600;text-align:center;line-height:1.6;font-style:italic;">"{current["content"]}"</p>', unsafe_allow_html=True)
        elif current["type"] in ("text","final"):
            st.markdown(f'<p style="color:#d4b8cc;font-size:15px;line-height:1.85;">{current["content"]}</p>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        dots = "".join([f'<span style="width:7px;height:7px;border-radius:50%;display:inline-block;margin:0 3px;background:{"#c084a0" if i<step else "#2E2E2E"}"></span>' for i in range(len(STEPS))])
        st.markdown(f'<div style="text-align:center;margin:12px 0">{dots}</div>', unsafe_allow_html=True)

        cb, cn = st.columns([1,2])
        with cb:
            if step > 1:
                if st.button("← Balik", use_container_width=True, type="secondary"):
                    st.session_state.surat_step -= 1; st.rerun()
        with cn:
            if current["type"] == "final":
                wa_num = current.get("wa_number","62")
                wa_url = f"https://wa.me/{wa_num}?text=Halo%20Jar%2C%20gua%20udah%20baca%20pesannya%20%F0%9F%98%8A"
                st.markdown(f'<a href="{wa_url}" target="_blank" style="display:block;text-align:center;background:#25D366;color:white;padding:12px;border-radius:12px;text-decoration:none;font-weight:700;font-size:14px;">💬 Hubungi Fajar di WA</a>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔄 Baca dari awal", use_container_width=True, type="secondary"):
                    st.session_state.surat_step = 0; st.rerun()
            else:
                if st.button(current["btn"], use_container_width=True, type="primary"):
                    st.session_state.surat_step += 1; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# ── DIARY TAB ─────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
elif nav == "diary":
    components.html("""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{background:#0D0D0D;font-family:'Inter',system-ui,sans-serif;color:#F0F0F0;min-height:100vh;}

/* PIN Screen */
#pinScreen{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:90vh;gap:20px;padding:24px;}
.pin-icon{font-size:48px;}
.pin-title{font-size:18px;font-weight:700;color:#F0F0F0;text-align:center;}
.pin-sub{font-size:13px;color:#666;text-align:center;line-height:1.6;}
.pin-dots{display:flex;gap:12px;margin:8px 0;}
.pin-dot{width:14px;height:14px;border-radius:50%;border:2px solid #2E2E2E;background:transparent;transition:background 0.15s;}
.pin-dot.filled{background:#F5C518;border-color:#F5C518;}
.pin-pad{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;width:260px;}
.pin-btn{background:#1E1E1E;border:1px solid #2E2E2E;border-radius:16px;padding:18px;font-size:20px;font-weight:600;color:#F0F0F0;cursor:pointer;text-align:center;transition:all 0.1s;}
.pin-btn:active{background:#2A2400;border-color:#F5C518;color:#F5C518;transform:scale(0.94);}
.pin-btn.del{font-size:16px;color:#666;}
.pin-error{font-size:13px;color:#FF4444;text-align:center;min-height:20px;}
.pin-note{font-size:11px;color:#333;text-align:center;line-height:1.6;max-width:280px;}

/* Diary Screen */
#diaryScreen{display:none;padding:0 0 80px;}

/* Mood bar */
.mood-row{display:flex;gap:8px;padding:14px 0 4px;overflow-x:auto;scrollbar-width:none;}
.mood-row::-webkit-scrollbar{display:none;}
.mood-btn{flex-shrink:0;background:#1E1E1E;border:1.5px solid #2E2E2E;border-radius:100px;padding:6px 14px;font-size:13px;cursor:pointer;transition:all 0.15s;white-space:nowrap;}
.mood-btn.active{border-color:#F5C518;background:#2A2400;}

/* New entry form */
.entry-form{background:#1A1A1A;border:1px solid #2E2E2E;border-radius:16px;padding:16px;margin:12px 0;}
.entry-form textarea{width:100%;background:transparent;border:none;outline:none;color:#F0F0F0;font-family:'Inter',sans-serif;font-size:14px;line-height:1.8;resize:none;min-height:120px;}
.entry-form textarea::placeholder{color:#333;}
.form-footer{display:flex;justify-content:space-between;align-items:center;margin-top:12px;padding-top:12px;border-top:1px solid #2E2E2E;}
.char-count{font-size:11px;color:#333;}
.save-btn{background:#F5C518;color:#000;border:none;border-radius:10px;padding:8px 20px;font-size:13px;font-weight:600;cursor:pointer;transition:all 0.15s;}
.save-btn:active{background:#D4A800;transform:scale(0.96);}
.save-btn:disabled{background:#2E2E2E;color:#555;cursor:not-allowed;}

/* Entry list */
.entries-label{font-size:10px;font-weight:700;letter-spacing:1.5px;color:#333;text-transform:uppercase;margin:20px 0 10px;}
.entry-card{background:#1A1A1A;border:1px solid #2E2E2E;border-radius:14px;padding:14px;margin:8px 0;position:relative;}
.entry-date{font-size:10px;color:#444;margin-bottom:6px;display:flex;align-items:center;gap:6px;}
.entry-mood{font-size:14px;}
.entry-text{font-size:13px;color:#C0C0C0;line-height:1.75;white-space:pre-wrap;word-break:break-word;}
.entry-del{position:absolute;top:12px;right:12px;background:none;border:none;color:#333;font-size:16px;cursor:pointer;padding:4px;}
.entry-del:hover{color:#FF4444;}

/* Empty */
.diary-empty{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding:48px 24px;text-align:center;}
.diary-empty .e-icon{font-size:40px;opacity:0.2;}
.diary-empty .e-text{font-size:13px;color:#333;line-height:1.7;}

/* Lock btn */
.lock-row{display:flex;justify-content:flex-end;padding:12px 0 4px;}
.lock-btn{background:#1E1E1E;border:1px solid #2E2E2E;border-radius:10px;padding:6px 14px;font-size:12px;color:#555;cursor:pointer;}

/* Confirm reset */
#resetConfirm{display:none;background:#FF4444;color:#fff;border:none;border-radius:10px;padding:8px 16px;font-size:12px;font-weight:600;cursor:pointer;margin-top:8px;width:100%;}
</style>
</head>
<body>

<!-- PIN SCREEN -->
<div id="pinScreen">
  <div class="pin-icon">📔</div>
  <div id="pinTitle" class="pin-title">Diary kamu</div>
  <div id="pinSub" class="pin-sub">Ini ruang kamu sendiri.<br>Cuma kamu yang bisa buka.</div>
  <div class="pin-dots">
    <div class="pin-dot" id="d0"></div>
    <div class="pin-dot" id="d1"></div>
    <div class="pin-dot" id="d2"></div>
    <div class="pin-dot" id="d3"></div>
  </div>
  <div class="pin-error" id="pinError"></div>
  <div class="pin-pad">
    <button class="pin-btn" onclick="pinInput('1')">1</button>
    <button class="pin-btn" onclick="pinInput('2')">2</button>
    <button class="pin-btn" onclick="pinInput('3')">3</button>
    <button class="pin-btn" onclick="pinInput('4')">4</button>
    <button class="pin-btn" onclick="pinInput('5')">5</button>
    <button class="pin-btn" onclick="pinInput('6')">6</button>
    <button class="pin-btn" onclick="pinInput('7')">7</button>
    <button class="pin-btn" onclick="pinInput('8')">8</button>
    <button class="pin-btn" onclick="pinInput('9')">9</button>
    <button class="pin-btn" onclick="pinInput('0')" style="grid-column:2">0</button>
    <button class="pin-btn del" onclick="pinDel()">⌫</button>
  </div>
  <div class="pin-note" id="pinNote">
    Data diary tersimpan di perangkat ini saja.<br>
    Tidak ada yang bisa akses selain kamu. 🔒
  </div>
  <button id="resetConfirm" onclick="confirmReset()">⚠️ Ya, hapus semua & reset PIN</button>
</div>

<!-- DIARY SCREEN -->
<div id="diaryScreen">
  <div class="lock-row">
    <button class="lock-btn" onclick="lockDiary()">🔒 Kunci</button>
  </div>

  <!-- Mood -->
  <div style="font-size:10px;font-weight:700;letter-spacing:1.5px;color:#333;text-transform:uppercase;margin-top:4px;">Mood hari ini</div>
  <div class="mood-row" id="moodRow">
    <button class="mood-btn" data-mood="" onclick="setMood(this)">— semua</button>
    <button class="mood-btn" data-mood="😊" onclick="setMood(this)">😊 Senang</button>
    <button class="mood-btn" data-mood="😢" onclick="setMood(this)">😢 Sedih</button>
    <button class="mood-btn" data-mood="😤" onclick="setMood(this)">😤 Kesal</button>
    <button class="mood-btn" data-mood="🥰" onclick="setMood(this)">🥰 Sayang</button>
    <button class="mood-btn" data-mood="😰" onclick="setMood(this)">😰 Cemas</button>
    <button class="mood-btn" data-mood="😌" onclick="setMood(this)">😌 Tenang</button>
    <button class="mood-btn" data-mood="🤔" onclick="setMood(this)">🤔 Bingung</button>
    <button class="mood-btn" data-mood="😴" onclick="setMood(this)">😴 Capek</button>
  </div>

  <!-- New entry -->
  <div class="entry-form">
    <textarea id="entryText" placeholder="Tulis apa yang ada di pikiranmu hari ini..." maxlength="2000" oninput="updateCount()"></textarea>
    <div class="form-footer">
      <span class="char-count" id="charCount">0 / 2000</span>
      <button class="save-btn" id="saveBtn" onclick="saveEntry()" disabled>Simpan</button>
    </div>
  </div>

  <!-- Entries list -->
  <div class="entries-label" id="entriesLabel">Catatan tersimpan</div>
  <div id="entriesList"></div>
</div>

<script>
// ── State ──────────────────────────────────────────────────────────────────
const STORAGE_KEY = 'izfa_diary_v1';
const PIN_KEY = 'izfa_diary_pin';
let currentPin = '';
let isSetupMode = false;
let setupPin = '';
let selectedMood = '';
let entries = [];
let unlocked = false;
let resetMode = false;

// ── Init ───────────────────────────────────────────────────────────────────
function init() {
  const savedPin = localStorage.getItem(PIN_KEY);
  if (!savedPin) {
    isSetupMode = true;
    document.getElementById('pinTitle').textContent = 'Buat PIN diarymu';
    document.getElementById('pinSub').textContent = 'Pilih 4 angka yang mudah kamu ingat.\nHanya kamu yang tahu.';
    document.getElementById('pinNote').innerHTML = '🔒 PIN ini tidak bisa dipulihkan jika lupa.<br>Simpan baik-baik ya.';
  }
}

// ── PIN Logic ──────────────────────────────────────────────────────────────
function pinInput(n) {
  if (currentPin.length >= 4) return;
  currentPin += n;
  updateDots();
  document.getElementById('pinError').textContent = '';
  if (currentPin.length === 4) {
    setTimeout(() => handlePinComplete(), 200);
  }
}

function pinDel() {
  currentPin = currentPin.slice(0,-1);
  updateDots();
  document.getElementById('pinError').textContent = '';
}

function updateDots() {
  for(let i=0;i<4;i++) {
    document.getElementById('d'+i).classList.toggle('filled', i < currentPin.length);
  }
}

function handlePinComplete() {
  const savedPin = localStorage.getItem(PIN_KEY);

  if (resetMode) {
    // confirm reset dengan PIN lama
    if (currentPin === savedPin) {
      localStorage.removeItem(PIN_KEY);
      localStorage.removeItem(STORAGE_KEY);
      location.reload();
    } else {
      shakeError('PIN salah, reset dibatalkan');
      resetMode = false;
      document.getElementById('resetConfirm').style.display = 'none';
    }
    currentPin = ''; updateDots(); return;
  }

  if (isSetupMode) {
    if (!setupPin) {
      setupPin = currentPin;
      currentPin = '';
      updateDots();
      document.getElementById('pinTitle').textContent = 'Ulangi PIN kamu';
      document.getElementById('pinSub').textContent = 'Masukkan PIN yang sama sekali lagi untuk konfirmasi.';
    } else {
      if (currentPin === setupPin) {
        localStorage.setItem(PIN_KEY, currentPin);
        openDiary();
      } else {
        setupPin = '';
        shakeError('PIN tidak cocok, coba lagi dari awal');
      }
    }
  } else {
    if (currentPin === savedPin) {
      openDiary();
    } else {
      shakeError('PIN salah ❌');
    }
  }
  currentPin = ''; updateDots();
}

function shakeError(msg) {
  document.getElementById('pinError').textContent = msg;
  const dots = document.querySelectorAll('.pin-dot');
  dots.forEach(d => { d.style.borderColor='#FF4444'; d.style.background='#FF444422'; });
  setTimeout(() => { dots.forEach(d => { d.style.borderColor=''; d.style.background=''; }); }, 600);
}

// ── Reset PIN (tahan 3 detik tombol 0) ────────────────────────────────────
let holdTimer = null;
document.querySelectorAll('.pin-btn').forEach(btn => {
  if(btn.textContent.trim() === '0') {
    btn.addEventListener('pointerdown', () => {
      holdTimer = setTimeout(() => {
        if(!isSetupMode) {
          resetMode = true;
          document.getElementById('pinTitle').textContent = 'Reset PIN?';
          document.getElementById('pinSub').textContent = 'Masukkan PIN lama untuk konfirmasi.\nSemua catatan akan terhapus.';
          document.getElementById('resetConfirm').style.display = 'block';
        }
      }, 3000);
    });
    btn.addEventListener('pointerup', () => clearTimeout(holdTimer));
  }
});

function confirmReset() {
  document.getElementById('pinTitle').textContent = 'Masukkan PIN lama';
  document.getElementById('pinSub').textContent = 'Konfirmasi dengan PIN lama kamu.';
  currentPin = ''; updateDots();
}

// ── Open Diary ─────────────────────────────────────────────────────────────
function openDiary() {
  unlocked = true;
  document.getElementById('pinScreen').style.display = 'none';
  document.getElementById('diaryScreen').style.display = 'block';
  loadEntries();
  renderEntries();
}

function lockDiary() {
  unlocked = false;
  document.getElementById('pinScreen').style.display = 'flex';
  document.getElementById('diaryScreen').style.display = 'none';
  document.getElementById('entryText').value = '';
  document.getElementById('charCount').textContent = '0 / 2000';
  document.getElementById('saveBtn').disabled = true;
  currentPin = ''; updateDots();
  document.getElementById('pinTitle').textContent = 'Selamat datang kembali 🌙';
  document.getElementById('pinSub').textContent = 'Masukkan PIN untuk buka diary.';
}

// ── Entries Storage ────────────────────────────────────────────────────────
function loadEntries() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    entries = raw ? JSON.parse(raw) : [];
  } catch(e) { entries = []; }
}

function saveToStorage() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(entries)); } catch(e) {}
}

// ── Mood ──────────────────────────────────────────────────────────────────
function setMood(btn) {
  document.querySelectorAll('.mood-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  selectedMood = btn.dataset.mood;
  renderEntries();
}

// ── New Entry ──────────────────────────────────────────────────────────────
function updateCount() {
  const txt = document.getElementById('entryText').value;
  document.getElementById('charCount').textContent = txt.length + ' / 2000';
  document.getElementById('saveBtn').disabled = txt.trim().length === 0;
}

function saveEntry() {
  const txt = document.getElementById('entryText').value.trim();
  if (!txt) return;
  const mood = document.querySelector('.mood-btn.active')?.dataset.mood || '';
  const entry = {
    id: Date.now(),
    text: txt,
    mood: mood,
    date: new Date().toLocaleDateString('id-ID', {weekday:'long',day:'numeric',month:'long',year:'numeric'}),
    time: new Date().toLocaleTimeString('id-ID', {hour:'2-digit',minute:'2-digit'}),
    ts: Date.now(),
  };
  entries.unshift(entry);
  saveToStorage();
  document.getElementById('entryText').value = '';
  document.getElementById('charCount').textContent = '0 / 2000';
  document.getElementById('saveBtn').disabled = true;
  renderEntries();
}

// ── Delete Entry ──────────────────────────────────────────────────────────
function deleteEntry(id) {
  if(!confirm('Hapus catatan ini?')) return;
  entries = entries.filter(e => e.id !== id);
  saveToStorage();
  renderEntries();
}

// ── Render ─────────────────────────────────────────────────────────────────
function renderEntries() {
  const list = document.getElementById('entriesList');
  const label = document.getElementById('entriesLabel');
  const filterMood = selectedMood;
  const filtered = filterMood ? entries.filter(e => e.mood === filterMood) : entries;

  label.textContent = filtered.length > 0 ? `${filtered.length} catatan tersimpan` : 'Belum ada catatan';

  if (filtered.length === 0) {
    list.innerHTML = `<div class="diary-empty">
      <div class="e-icon">📝</div>
      <div class="e-text">${entries.length === 0 ? 'Mulai tulis sesuatu...<br>Tidak ada yang menghakimi di sini.' : 'Tidak ada catatan dengan mood ini.'}</div>
    </div>`;
    return;
  }

  list.innerHTML = filtered.map(e => `
    <div class="entry-card">
      <div class="entry-date">
        ${e.mood ? '<span class="entry-mood">'+e.mood+'</span>' : ''}
        <span>${e.date} · ${e.time}</span>
      </div>
      <div class="entry-text">${escHtml(e.text)}</div>
      <button class="entry-del" onclick="deleteEntry(${e.id})">✕</button>
    </div>
  `).join('');
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

init();
</script>
</body>
</html>
""", height=900, scrolling=True)
