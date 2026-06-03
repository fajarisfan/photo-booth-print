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
    page_title="Photo Booth Cetak",
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

def make_filter_thumb(photo: Image.Image, filter_key: str, size: int = 120) -> Image.Image:
    """Generate a small square thumbnail with the given filter applied."""
    w, h = photo.size
    # Center crop to square
    side = min(w, h)
    x = (w - side) // 2
    y = (h - side) // 2
    thumb = photo.crop((x, y, x + side, y + side))
    thumb = thumb.resize((size, size), Image.LANCZOS)
    filtered = apply_filter(thumb, filter_key)
    return filtered

# ── Session state ──────────────────────────────────────────────────────────────
if "photo" not in st.session_state:
    st.session_state.photo = None
if "selected_tpl" not in st.session_state:
    st.session_state.selected_tpl = "pas_foto_2x3"
if "selected_filter" not in st.session_state:
    st.session_state.selected_filter = "normal"

# ── UI ─────────────────────────────────────────────────────────────────────────
st.markdown("# 📸 Photo Booth Cetak")
st.markdown("*Ambil foto → Pilih tema → Pilih template → Download PDF / JPG*")
st.divider()

col_left, col_right = st.columns([1, 1.4], gap="large")

# ── LEFT: Foto input + Filter + Template picker ───────────────────────────────
with col_left:
    st.markdown("### 1. Ambil / Upload Foto")

    input_mode = st.radio("Sumber foto", ["📷 Webcam", "📁 Upload File"], horizontal=True, label_visibility="collapsed")

    if input_mode == "📷 Webcam":
        cam_img = st.camera_input("Klik tombol kamera untuk mengambil foto", label_visibility="visible")
        if cam_img:
            raw = Image.open(cam_img)
            # ✅ Fix mirror: flip horizontal untuk selfie kamera depan
            st.session_state.photo = ImageOps.mirror(raw)
            st.success("✅ Foto berhasil diambil!")
    else:
        uploaded = st.file_uploader(
            "Upload foto (JPG, PNG)",
            type=["jpg", "jpeg", "png", "webp"],
            label_visibility="visible",
        )
        if uploaded:
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

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style="text-align:center; color:#555; font-size:12px;">
Photo Booth Cetak — Output resolusi 300 DPI, siap cetak di kertas foto A4<br>
Template: Pas Foto 2×3 · 3×4 · 4×6 · Strip Polaroid · Photo Booth Grid · Film Strip · Wallet Print<br>
Filter: Normal · Hitam Putih · Vintage · Cool Blue · Golden Hour · Faded · Vivid · Sepia · Noir · Pastel · Neon · Film Grain
</div>
""", unsafe_allow_html=True)
