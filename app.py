import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
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
</style>
""", unsafe_allow_html=True)

# ── Template definitions ───────────────────────────────────────────────────────
# Each template: name, photo_w_cm, photo_h_cm, cols, rows, desc, style
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

# ── Helpers ────────────────────────────────────────────────────────────────────
DPI = 300
CM_TO_PX = DPI / 2.54

def cm_to_px(val):
    return int(val * CM_TO_PX)

def fit_crop(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Crop-center an image to fill target dimensions."""
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
        # sprocket holes
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

def build_sheet(photo: Image.Image, tpl: dict) -> Image.Image:
    """Build the print sheet for a given template."""
    cols, rows = tpl["cols"], tpl["rows"]
    photo_w_px = cm_to_px(tpl["w"])
    photo_h_px = cm_to_px(tpl["h"])
    border_px  = tpl["border"]
    style      = tpl["style"]
    bg         = tpl["bg_color"]

    # Prepare framed cell
    cell_img = fit_crop(photo, photo_w_px, photo_h_px)
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
    ONE_CM = 28.35  # 1 cm in PDF points

    # A4 landscape or portrait depending on sheet ratio
    sw, sh = sheet.size
    if sw > sh:
        pagesize = (A4[1], A4[0])  # landscape
    else:
        pagesize = A4

    c = rl_canvas.Canvas(buf, pagesize=pagesize)
    pw, ph = pagesize

    # Scale sheet to fit page with margin
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

    # Info footer
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

# ── Session state ──────────────────────────────────────────────────────────────
if "photo" not in st.session_state:
    st.session_state.photo = None
if "selected_tpl" not in st.session_state:
    st.session_state.selected_tpl = "pas_foto_2x3"

# ── UI ─────────────────────────────────────────────────────────────────────────
st.markdown("# 📸 Photo Booth Cetak")
st.markdown("*Ambil foto → Pilih template → Download PDF / JPG*")
st.divider()

col_left, col_right = st.columns([1, 1.4], gap="large")

# ── LEFT: Foto input + Template picker ────────────────────────────────────────
with col_left:
    st.markdown("### 1. Ambil / Upload Foto")

    input_mode = st.radio("Sumber foto", ["📷 Webcam", "📁 Upload File"], horizontal=True, label_visibility="collapsed")

    if input_mode == "📷 Webcam":
        cam_img = st.camera_input("Klik tombol kamera untuk mengambil foto", label_visibility="visible")
        if cam_img:
            st.session_state.photo = Image.open(cam_img)
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

    st.divider()
    st.markdown("### 2. Pilih Template")

    tpl_keys = list(TEMPLATES.keys())
    # 2 columns for template radio
    for i in range(0, len(tpl_keys), 2):
        c1, c2 = st.columns(2)
        for j, col in enumerate([c1, c2]):
            if i + j < len(tpl_keys):
                key = tpl_keys[i + j]
                tpl = TEMPLATES[key]
                selected = st.session_state.selected_tpl == key
                label = f"{'✅ ' if selected else ''}{tpl['icon']} **{tpl['name']}**\n\n{tpl['desc']}"
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
    st.markdown("### 3. Preview & Download")

    tpl_key = st.session_state.selected_tpl
    tpl = TEMPLATES[tpl_key]

    # Show template info
    st.markdown(f"""
    <div class="info-box">
    <b>{tpl['icon']} {tpl['name']}</b> &nbsp;|&nbsp;
    Ukuran foto: <b>{tpl['w']}×{tpl['h']} cm</b> &nbsp;|&nbsp;
    Susunan: <b>{tpl['cols']}×{tpl['rows']}</b>
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
            sheet = build_sheet(st.session_state.photo, tpl)
            thumb = preview_thumbnail(sheet, max_px=700)

        st.markdown('<div class="preview-label">PREVIEW</div>', unsafe_allow_html=True)
        st.image(thumb, use_container_width=True, caption=f"{tpl['name']} — siap cetak di printer A4")

        st.divider()
        st.markdown("### 4. Download")

        d1, d2 = st.columns(2)

        with d1:
            jpg_bytes = sheet_to_bytes(sheet, "JPEG")
            st.download_button(
                label="⬇️ Download JPG",
                data=jpg_bytes,
                file_name=f"photobooth_{tpl_key}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
                mime="image/jpeg",
                use_container_width=True,
            )

        with d2:
            pdf_bytes = sheet_to_pdf(sheet, tpl)
            st.download_button(
                label="⬇️ Download PDF",
                data=pdf_bytes,
                file_name=f"photobooth_{tpl_key}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        # Download all templates at once
        st.divider()
        if st.button("📦 Download SEMUA Template (ZIP)", use_container_width=True):
            with st.spinner("Membuat semua template..."):
                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    for k, t in TEMPLATES.items():
                        s = build_sheet(st.session_state.photo, t)
                        jpg = sheet_to_bytes(s, "JPEG")
                        pdf = sheet_to_pdf(s, t)
                        zf.writestr(f"{k}.jpg", jpg)
                        zf.writestr(f"{k}.pdf", pdf)
                zip_buf.seek(0)
            st.download_button(
                label="⬇️ Download ZIP",
                data=zip_buf.getvalue(),
                file_name=f"photobooth_all_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",
                use_container_width=True,
            )

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style="text-align:center; color:#555; font-size:12px;">
Photo Booth Cetak — Output resolusi 300 DPI, siap cetak di kertas foto A4<br>
Template: Pas Foto 2×3 · 3×4 · 4×6 · Strip Polaroid · Photo Booth Grid · Film Strip · Wallet Print
</div>
""", unsafe_allow_html=True)
