# ── UI ─────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:16px 0 8px;">
  <span style="font-size:24px;font-weight:700;letter-spacing:1px;color:#f5c518;">📸 Photo Booth</span>
  <div style="font-size:10px;color:#666;">by Fajar</div>
</div>
""", unsafe_allow_html=True)

# ── BUAT 3 TAB ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📸 Ambil", "🖼️ Frame", "💌 Surat"])

# ============================================================
# TAB 1 : AMBIL & CETAK
# ============================================================
with tab1:
    st.markdown('<div class="flutter-card">', unsafe_allow_html=True)
    st.markdown("#### 🖼️ Pilih Template")
    
    # ── Template Picker (Horizontal Chip) ──────────────────
    tpl_keys = list(TEMPLATES.keys())
    # Tambahkan opsi "Custom" jika frame custom terupload
    if "custom_frame_img" in st.session_state:
        tpl_keys = ["custom_frame"] + [k for k in tpl_keys if k != "custom_frame"]
    
    # Tampilkan dalam grid chip (3-4 per baris)
    cols_chip = st.columns(4)
    for i, key in enumerate(tpl_keys):
        with cols_chip[i % 4]:
            is_active = st.session_state.selected_tpl == key
            label = "✨" if key == "custom_frame" else TEMPLATES.get(key, {}).get("icon", "🖼️")
            if st.button(
                label,
                key=f"mob_tpl_{key}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
                help=TEMPLATES.get(key, {}).get("desc", "Custom Frame")
            ):
                st.session_state.selected_tpl = key
                st.rerun()
            # Nama pendek di bawah
            name = "Custom" if key == "custom_frame" else TEMPLATES.get(key, {}).get("name", key)[:10]
            st.caption(f"<small>{name}</small>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ── Kamera / Upload ──────────────────────────────────────
    st.markdown('<div class="flutter-card">', unsafe_allow_html=True)
    input_mode = st.radio("Sumber", ["📷 Kamera", "📁 Upload"], horizontal=True, label_visibility="collapsed")
    
    photo = None
    if input_mode == "📷 Kamera":
        # Fallback native (biar simpel di HP)
        cam = st.camera_input("Ambil foto", label_visibility="collapsed")
        if cam:
            photo = Image.open(cam).convert("RGB")
            st.session_state.photo = photo
    else:
        upload = st.file_uploader("Upload foto", type=["jpg","jpeg","png"], label_visibility="collapsed")
        if upload:
            photo = Image.open(upload).convert("RGB")
            st.session_state.photo = photo
    
    # ── Filter Cepat (Dropdown kecil) ───────────────────────
    if photo:
        fk = st.selectbox(
            "Tema",
            options=list(FILTERS.keys()),
            format_func=lambda k: f"{FILTERS[k]['icon']} {FILTERS[k]['name']}",
            index=list(FILTERS.keys()).index(st.session_state.selected_filter),
            key="mob_filter"
        )
        st.session_state.selected_filter = fk
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ── HASIL LANGSUNG CETAK ──────────────────────────────────
    if photo:
        st.markdown('<div class="flutter-card">', unsafe_allow_html=True)
        st.markdown("#### ✅ Hasil Jadi")
        
        tpl_key = st.session_state.selected_tpl
        current_filter = st.session_state.selected_filter
        
        with st.spinner("Memproses..."):
            # CEK CUSTOM FRAME
            if tpl_key == "custom_frame" and "custom_frame_img" in st.session_state and "custom_slots" in st.session_state:
                sheet = apply_custom_frame(
                    photo,
                    st.session_state.custom_frame_img,
                    st.session_state.custom_slots,
                    current_filter
                )
            else:
                tpl = TEMPLATES.get(tpl_key, TEMPLATES["pas_foto_2x3"])
                if tpl["style"].startswith("frame_") or tpl["style"].startswith("romance_"):
                    sheet = build_frame_sheet(photo, tpl, current_filter)
                elif tpl_key == "studio_print":
                    sheet = build_studio_sheet(photo, tpl, current_filter, st.session_state.studio_name, st.session_state.studio_sub)
                else:
                    sheet = build_sheet(photo, tpl, current_filter)
        
        # Preview
        st.image(sheet, use_container_width=True)
        
        # Tombol Download (JPG & PDF)
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button(
                "⬇️ JPG", data=sheet_to_bytes(sheet, "JPEG"),
                file_name=f"foto_{datetime.datetime.now().strftime('%H%M%S')}.jpg",
                mime="image/jpeg", use_container_width=True
            )
        with col_d2:
            st.download_button(
                "⬇️ PDF", data=sheet_to_pdf(sheet, {"name":"PhotoBooth"}),
                file_name=f"foto_{datetime.datetime.now().strftime('%H%M%S')}.pdf",
                mime="application/pdf", use_container_width=True
            )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ── OPSI TAMBAHAN (Watermark, Sticker) ──────────────
        with st.expander("🎨 Tambahkan Watermark / Sticker", expanded=False):
            wm = st.text_input("Teks watermark", placeholder="Nama kamu...")
            if st.button("➕ Tempel Watermark"):
                if wm:
                    sheet_wm = add_watermark(sheet, wm, logo_img=st.session_state.get("watermark_logo"))
                    st.image(sheet_wm, use_container_width=True)
                    st.download_button("⬇️ JPG + Watermark", data=sheet_to_bytes(sheet_wm, "JPEG"), ...)
                    
        # ── RESET ──────────────────────────────────────────────
        if st.button("🔄 Ambil Ulang", use_container_width=True):
            st.session_state.photo = None
            st.rerun()
    else:
        st.info("📸 Ambil atau upload foto dulu!")

# ============================================================
# TAB 2 : CUSTOM FRAME
# ============================================================
with tab2:
    st.markdown('<div class="flutter-card">', unsafe_allow_html=True)
    st.markdown("#### 🖌️ Upload Frame Sendiri")
    st.caption("Bikin frame di Canva/PS. Kasih kotak **hijau neon (#00FF00)** di tempat foto. Aplikasi bakal baca otomatis.")
    
    uploaded_frame = st.file_uploader("Upload Frame (PNG/JPG)", type=["png","jpg","jpeg"], key="custom_frame_upload")
    
    if uploaded_frame:
        frame_img = Image.open(uploaded_frame).convert("RGB")
        st.session_state["custom_frame_img"] = frame_img
        
        slots = detect_green_slots(frame_img)
        if not slots:
            st.warning("⚠️ Gak ketemu slot hijau! Pastikan pake #00FF00.")
        else:
            st.success(f"✅ Ditemukan {len(slots)} slot foto!")
            # Preview slot
            preview = frame_img.copy()
            draw = ImageDraw.Draw(preview)
            for (x,y,w,h) in slots:
                draw.rectangle([x,y,x+w,y+h], outline=(255,0,0), width=3)
            st.image(preview, caption="Slot terdeteksi (merah)", use_container_width=True)
            st.session_state["custom_slots"] = slots
            
            # Langsung pindah ke Tab 1
            st.info("🔄 Kembali ke Tab 📸 Ambil, pilih template 'Custom', lalu ambil foto!")
            if st.button("🚀 Buka Tab Ambil", use_container_width=True):
                st.session_state.selected_tpl = "custom_frame"
                st.rerun()
    
    if st.button("🗑️ Hapus Frame Custom", use_container_width=True):
        for k in ["custom_frame_img", "custom_slots"]:
            if k in st.session_state: del st.session_state[k]
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# TAB 3 : SURAT UNTUK KAMU 💌
# ============================================================
with tab3:
    st.markdown('<div class="flutter-card" style="background:linear-gradient(135deg,#1a1218,#1f1a1f);">', unsafe_allow_html=True)
    st.markdown("#### 💌 Ada Surat Untuk Kamu")
    
    # Panggil logic surat rahasia yang sudah kamu buat, tapi kita sederhanakan tampilannya
    if "surat_step" not in st.session_state:
        st.session_state.surat_step = 0
    
    step = st.session_state.surat_step
    STEPS = [
        {"type":"intro","content":"Ada sesuatu yang pengen gua ceritain...","btn":"Lanjut →"},
        {"type":"text","content":"Kemarin gua dapet panggilan interview di Jakarta. Tapi... gua tolak karena ortu. Anak tunggal, Zah.","btn":"Lanjut"},
        {"type":"text","content":"Gua buat aplikasi ini khusus buat lu. Bukan cuma photo booth—ini cara gua bilang: lu ngaruh banget buat gua.","btn":"Lanjut"},
        {"type":"final","content":"Nomor gua masih sama. Matcha yang gagal dulu bakal gua ganti. Doain gua ya, Zah. 🙏","btn":"💬 Hubungi", "wa_number":"6289XXXXXXXX"}
    ]
    
    if step == 0:
        if st.button("💌 Buka Surat", use_container_width=True):
            st.session_state.surat_step = 1
            st.rerun()
    else:
        current = STEPS[step - 1]
        st.markdown(f"<p style='color:#d4b8cc;font-size:15px;line-height:1.8;'>{current['content']}</p>", unsafe_allow_html=True)
        
        col_b, col_n = st.columns([1, 2])
        with col_b:
            if step > 1 and st.button("←", use_container_width=True):
                st.session_state.surat_step -= 1
                st.rerun()
        with col_n:
            if current.get("type") == "final":
                wa_num = current.get("wa_number", "62")
                st.markdown(f'<a href="https://wa.me/{wa_num}?text=Halo%20Jar%2C%20aku%20udah%20baca%20pesannya" target="_blank" style="display:block;background:#25D366;color:white;padding:10px;border-radius:10px;text-align:center;text-decoration:none;font-weight:700;">💬 {current["btn"]}</a>', unsafe_allow_html=True)
            else:
                if st.button(current["btn"], use_container_width=True, type="primary"):
                    st.session_state.surat_step += 1
                    st.rerun()
        
        # Progress dots
        dots = "".join([f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;margin:0 3px;background:{"#c084a0" if i < step else "#333"}"></span>' for i in range(len(STEPS))])
        st.markdown(f'<div style="text-align:center;margin-top:12px;">{dots}</div>', unsafe_allow_html=True)
    
    # ── PESAN & DOA (tetap dipertahankan) ──────────────────
    st.divider()
    with st.form("doa_mobile", clear_on_submit=True):
        nama = st.text_input("Nama (boleh anonim)", placeholder="Siapa nih?")
        pesan = st.text_area("Pesan buat developer 💬", placeholder="Tulis pesanmu...")
        if st.form_submit_button("💌 Kirim", use_container_width=True):
            st.success("Terima kasih! 🙏")
            # (Kode API request tetap sama seperti sebelumnya)
    st.markdown('</div>', unsafe_allow_html=True)
