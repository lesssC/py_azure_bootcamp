import html

import streamlit as st

from ai_agent import (
    agente_match_habilidades,
    consultar_vacantes_bd,
    estado_catalogo,
    extraer_texto_anuncio,
    estructurar_anuncio,
    registrar_oferta_bd,
)

st.set_page_config(
    page_title="chambaYA | Kiosco comunitario",
    page_icon="assets/chambaya-logo.svg",
    layout="wide",
)

st.logo("assets/chambaya-logo.svg", size="large")
st.markdown(
    """
    <style>
    :root {
        --terra: #ED6A5A;
        --butter: #F4F1BB;
        --opal: #9BC1BC;
        --ivory: #E6EBE0;
        --aqua: #36C9C6;
    }
    .block-container { max-width: 1180px; padding-top: 2rem; }
    [data-testid="stSidebar"] [data-testid="stSidebarHeader"] { padding-top: 1rem; }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #f8faf5 0%, var(--ivory) 58%, #d9efec 100%);
    }
    [data-testid="stSidebar"] { background: var(--opal); }
    .brand-kicker {
        color: #315b59; font-size: 0.82rem; font-weight: 700;
        letter-spacing: .12em; text-transform: uppercase;
    }
    .brand-title {
        color: #173b3a; font-size: clamp(2.2rem, 5vw, 4.2rem);
        font-weight: 800; letter-spacing: -0.05em; line-height: 1;
        margin: 0.15rem 0 0.6rem;
    }
    .brand-title span { color: var(--terra); }
    .hero-copy { color: #315b59; font-size: 1.12rem; max-width: 680px; }
    div.stButton > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] button {
        background: var(--terra); border-color: var(--terra); color: white;
        font-weight: 700; border-radius: 0.75rem;
    }
    div.stButton > button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] button:hover {
        background: #d95749; border-color: #d95749;
    }
    div[data-testid="stAlert"] {
        border-radius: 0.85rem; border: 1px solid rgba(49, 91, 89, .16);
    }
    [data-testid="stDataFrame"] { overflow-x: auto; }
    @media (max-width: 760px) {
        .block-container { padding: 1rem 0.85rem 2rem; }
        [data-testid="stSidebar"] { display: none; }
        .brand-kicker { font-size: 0.7rem; }
        .brand-title { font-size: 2.65rem; }
        .hero-copy { font-size: 0.98rem; line-height: 1.4; }
        div[data-testid="stTabs"] button { font-size: 0.82rem; padding-left: 0.45rem; padding-right: 0.45rem; }
        div[data-testid="stHorizontalBlock"] { gap: 0.5rem; }
        div[data-testid="stButton"] button { min-height: 2.7rem; font-size: 0.82rem; }
        [data-testid="stDataFrame"] { display: none; }
        .mobile-catalog-card {
            display: block;
            background: rgba(255, 255, 255, 0.58);
            border: 1px solid rgba(49, 91, 89, .18);
            border-radius: 0.8rem;
            padding: 0.85rem;
            margin-bottom: 0.65rem;
        }
        .mobile-catalog-title { color: #173b3a; font-weight: 750; }
        .mobile-catalog-meta { color: #315b59; font-size: 0.86rem; line-height: 1.5; }
    }
    @media (min-width: 761px) {
        .mobile-catalog-card { display: none; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown('<div class="brand-kicker">Empleo local, claro y directo</div>', unsafe_allow_html=True)
st.markdown('<div class="brand-title">chamba<span>YA</span></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-copy">Encuentra oportunidades de oficio cerca de ti, '
    'sin currículum digital y con ayuda para entender cada anuncio.</div>',
    unsafe_allow_html=True,
)

tab_kiosco, tab_bodega = st.tabs(
    [":material/search: Buscar oportunidades", ":material/add_a_photo: Registrar anuncio"]
)

with tab_kiosco:
    st.subheader("¿Qué sabes hacer?")
    st.write("Elige un oficio o cuéntanos tu experiencia con tus propias palabras.")
    opciones = {
        ":material/construction: Pintura y construcción": "Pintura, preparación de paredes y drywall",
        ":material/restaurant: Cocina y ayudante": "Cocina, picado de alimentos y atención en puesto",
        ":material/bolt: Electricidad básica": "Instalaciones eléctricas sencillas y reparaciones",
        ":material/content_cut: Costura y textil": "Manejo de máquina remalladora y costura",
        ":material/plumbing: Plomería y gasfitería": "Arreglo de tuberías y caños",
        ":material/inventory_2: Limpieza y carga": "Orden de bodega y carga de mercadería",
    }
    columnas = st.columns(3)
    for indice, (etiqueta, habilidad) in enumerate(opciones.items()):
        if columnas[indice % 3].button(etiqueta, width="stretch"):
            st.session_state["habilidad"] = habilidad

    habilidad_personal = st.text_input(
        "O escribe tu habilidad", value=st.session_state.get("habilidad", "")
    )
    if st.button(
        ":material/confirmation_number: Generar mi ticket de oportunidades",
        type="primary",
        width="stretch",
    ):
        if not habilidad_personal.strip():
            st.warning(
                "Cuéntanos qué sabes hacer para buscar oportunidades para ti.",
                icon=":material/lightbulb:",
            )
        else:
            with st.spinner("Estamos buscando opciones cercanas..."):
                ticket = agente_match_habilidades(habilidad_personal.strip())
            st.success("Tu ticket de oportunidades está listo.", icon=":material/check_circle:")
            st.code(ticket, language=None)
            st.download_button(
                ":material/download: Descargar ticket",
                ticket,
                "ticket-chambaya.txt",
                "text/plain",
            )
            st.info(
                "Puedes imprimirlo o compartirlo por SMS desde el kiosco.",
                icon=":material/print:",
            )

    with st.expander(":material/list_alt: Ver catálogo disponible"):
        catalogo = consultar_vacantes_bd()
        if estado_catalogo().startswith("Azure SQL"):
            st.success(estado_catalogo(), icon=":material/cloud_done:")
        else:
            st.warning(
                "Estamos mostrando opciones de respaldo mientras se conecta el catálogo.",
                icon=":material/cloud_off:",
            )
        st.dataframe(
            catalogo,
            width="stretch",
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "titulo": st.column_config.TextColumn("Vacante", width="medium"),
                "fuente": st.column_config.TextColumn("Fuente", width="small"),
                "direccion": st.column_config.TextColumn("Dirección", width="medium"),
                "telefono": st.column_config.TextColumn("Contacto", width="small"),
                "req": st.column_config.TextColumn("Requisitos", width="medium"),
            },
        )
        st.markdown('<div class="mobile-catalog">', unsafe_allow_html=True)
        for oferta in catalogo:
            titulo_seguro = html.escape(str(oferta["titulo"]))
            fuente_segura = html.escape(str(oferta["fuente"]))
            direccion_segura = html.escape(str(oferta["direccion"]))
            telefono_seguro = html.escape(str(oferta["telefono"]))
            requisitos_seguro = html.escape(str(oferta["req"]))
            st.markdown(
                f"""
                <article class="mobile-catalog-card">
                    <div class="mobile-catalog-title">{titulo_seguro}</div>
                    <div class="mobile-catalog-meta">
                        <strong>Fuente:</strong> {fuente_segura}<br>
                        <strong>Dirección:</strong> {direccion_segura}<br>
                        <strong>Contacto:</strong> {telefono_seguro}<br>
                        <strong>Requisitos:</strong> {requisitos_seguro}
                    </div>
                </article>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

with tab_bodega:
    st.subheader("Digitalizar un anuncio")
    st.write("Sube una foto clara y revisa los datos antes de publicarlos.")
    foto = st.file_uploader(
        "Selecciona una foto del aviso",
        type=["jpg", "jpeg", "png"],
        key="foto_anuncio",
    )
    if foto:
        st.image(foto, caption="Vista previa del anuncio", width=350)
        if st.button(":material/document_scanner: Leer anuncio", width="stretch"):
            with st.spinner("Estamos leyendo el anuncio..."):
                texto_anuncio = extraer_texto_anuncio(foto.getvalue())
                st.session_state["texto_anuncio"] = texto_anuncio
                st.session_state["campos_anuncio"] = estructurar_anuncio(texto_anuncio)

    if st.session_state.get("texto_anuncio"):
        st.text_area(
            "Texto detectado (referencia para la validación)",
            st.session_state["texto_anuncio"],
            height=180,
            disabled=True,
        )
        st.info(
            "El sistema propone datos a partir de la imagen. Revísalos y corrígelos "
            "antes de publicar.",
            icon=":material/edit_note:",
        )
        campos = st.session_state.get("campos_anuncio", {})
        with st.form("formulario_nueva_oferta"):
            titulo = st.text_input("Título de la vacante", value=campos.get("titulo", ""))
            fuente = st.text_input(
                "Fuente del anuncio", value=campos.get("fuente", "Bodega / Mercado")
            )
            direccion = st.text_input("Dirección", value=campos.get("direccion", ""))
            telefono = st.text_input(
                "Teléfono de contacto", value=campos.get("telefono", "")
            )
            requisitos = st.text_area(
                "Requisitos mínimos", value=campos.get("requisitos", "")
            )
            guardar = st.form_submit_button(
                ":material/cloud_upload: Validar y guardar en el catálogo",
                width="stretch",
            )

        if guardar:
            try:
                oferta_id = registrar_oferta_bd(
                    titulo, fuente, direccion, telefono, requisitos
                )
            except (RuntimeError, ValueError) as error:
                st.error(str(error))
            else:
                st.success(
                    f"La oferta #{oferta_id} quedó publicada en el catálogo.",
                    icon=":material/check_circle:",
                )
                st.session_state.pop("texto_anuncio", None)
                st.session_state.pop("campos_anuncio", None)
                st.session_state.pop("foto_anuncio", None)
                st.rerun()
    else:
        st.info(
            "Primero lee la imagen. Luego podrás revisar los datos y publicar el "
            "anuncio en el catálogo.",
            icon=":material/info:",
        )
