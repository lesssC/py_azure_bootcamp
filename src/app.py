import html

import streamlit as st

from ai_agent import (
    agente_match_habilidades,
    actualizar_oferta_bd,
    consultar_ofertas_admin,
    consultar_vacantes_bd,
    desactivar_oferta_bd,
    estado_catalogo,
    extraer_texto_anuncio,
    estructurar_anuncio,
    iniciar_sesion,
    registrar_usuario,
    registrar_oferta_bd,
)

st.set_page_config(
    page_title="chambaYA | Kiosco comunitario",
    page_icon="assets/chambaya-logo.svg",
    layout="wide",
)

st.image("assets/chambaya-logo.svg", width=180)
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
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
        overflow-x: hidden;
    }
    .block-container { max-width: 1180px; padding-top: 1rem; }
    [data-testid="stImage"] {
        margin: 0 0 0.35rem;
    }
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
    [data-testid="stDataFrame"] {
        max-width: 100%;
        overflow: hidden;
    }
    .mobile-catalog { display: none; }
    @media (max-width: 900px) {
        .block-container { padding: 1rem 0.85rem 2rem; }
        [data-testid="stSidebar"] { display: none; }
        [data-testid="stImage"] { margin-bottom: 0.25rem; }
        .brand-kicker { font-size: 0.7rem; }
        .brand-title { font-size: 2.65rem; }
        .hero-copy { font-size: 0.98rem; line-height: 1.4; }
        div[data-testid="stTabs"] button { font-size: 0.82rem; padding-left: 0.45rem; padding-right: 0.45rem; }
        div[data-testid="stHorizontalBlock"] { gap: 0.5rem; }
        div[data-testid="stButton"] button { min-height: 2.7rem; font-size: 0.82rem; }
        [data-testid="stDataFrame"] { display: none; }
        .mobile-catalog { display: block; }
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
    @media (min-width: 901px) {
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

tab_kiosco, tab_catalogo, tab_bodega, tab_cuenta, tab_admin = st.tabs(
    [
        ":material/search: Buscar oportunidades",
        ":material/list_alt: Catálogo",
        ":material/add_a_photo: Registrar anuncio",
        ":material/account_circle: Mi cuenta",
        ":material/admin_panel_settings: Administración",
    ]
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

with tab_catalogo:
    st.subheader("Oportunidades disponibles")
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
            "titulo": st.column_config.TextColumn("Vacante", width="medium"),
            "fuente": st.column_config.TextColumn("Fuente", width="small"),
            "direccion": st.column_config.TextColumn("Dirección", width="medium"),
            "telefono": st.column_config.TextColumn("Contacto", width="small"),
            "req": st.column_config.TextColumn("Requisitos", width="medium"),
            "fecha": st.column_config.DatetimeColumn("Publicada", format="DD/MM/YYYY HH:mm"),
        },
    )
    st.markdown('<div class="mobile-catalog">', unsafe_allow_html=True)
    for oferta in catalogo:
        st.markdown(
            f"""
            <article class="mobile-catalog-card">
                <div class="mobile-catalog-title">{html.escape(str(oferta["titulo"]))}</div>
                <div class="mobile-catalog-meta">
                    <strong>Publicada:</strong> {html.escape(str(oferta.get("fecha", "")))}<br>
                    <strong>Fuente:</strong> {html.escape(str(oferta["fuente"]))}<br>
                    <strong>Dirección:</strong> {html.escape(str(oferta["direccion"]))}<br>
                    <strong>Contacto:</strong> {html.escape(str(oferta["telefono"]))}<br>
                    <strong>Requisitos:</strong> {html.escape(str(oferta["req"]))}
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
        key=f"foto_anuncio_{st.session_state.get('uploader_version', 0)}",
    )
    if foto:
        foto_bytes = foto.getvalue()
        if len(foto_bytes) > 10 * 1024 * 1024:
            st.error(
                "La imagen es demasiado grande. Selecciona una foto de máximo 10 MB.",
                icon=":material/image_not_supported:",
            )
            foto = None
        try:
            if foto:
                st.image(foto_bytes, caption="Vista previa del anuncio", width=350)
        except (OSError, ValueError):
            st.error(
                "No pudimos abrir esta imagen. Usa un archivo JPG o PNG válido.",
                icon=":material/broken_image:",
            )
            foto = None

        if foto and st.button(
            ":material/document_scanner: Leer anuncio", width="stretch"
        ):
            with st.spinner("Estamos leyendo el anuncio..."):
                texto_anuncio = extraer_texto_anuncio(foto_bytes)
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
                st.toast("Aviso publicado correctamente.")
                st.session_state.pop("texto_anuncio", None)
                st.session_state.pop("campos_anuncio", None)
                st.session_state["uploader_version"] = st.session_state.get(
                    "uploader_version", 0
                ) + 1
                st.session_state["abrir_catalogo"] = True
                st.rerun()
    else:
        st.info(
            "Primero lee la imagen. Luego podrás revisar los datos y publicar el "
            "anuncio en el catálogo.",
            icon=":material/info:",
        )

with tab_cuenta:
    st.subheader("Mi cuenta")
    if st.session_state.get("usuario"):
        usuario = st.session_state["usuario"]
        st.success(
            f"Sesión iniciada como {usuario['nombre']} ({usuario['rol']}).",
            icon=":material/account_circle:",
        )
        if st.button(":material/logout: Cerrar sesión"):
            st.session_state.pop("usuario")
            st.rerun()
    else:
        modo_cuenta = st.radio(
            "¿Qué deseas hacer?",
            ["Iniciar sesión", "Crear cuenta"],
            horizontal=True,
        )
        if modo_cuenta == "Iniciar sesión":
            correo = st.text_input("Correo electrónico", key="login_correo")
            password = st.text_input("Contraseña", type="password", key="login_password")
            if st.button(":material/login: Ingresar", type="primary"):
                try:
                    usuario = iniciar_sesion(correo, password)
                except RuntimeError as error:
                    st.error(str(error))
                else:
                    if usuario:
                        st.session_state["usuario"] = usuario
                        st.toast("Sesión iniciada correctamente.")
                        st.rerun()
                    else:
                        st.error("Correo o contraseña incorrectos.", icon=":material/lock:")
        else:
            nombre = st.text_input("Nombre completo", key="registro_nombre")
            correo = st.text_input("Correo electrónico", key="registro_correo")
            password = st.text_input(
                "Contraseña (mínimo 8 caracteres)",
                type="password",
                key="registro_password",
            )
            invite_code = st.text_input(
                "Código de invitación para administrador (opcional)",
                type="password",
                key="registro_invite",
                help="Déjalo vacío para crear una cuenta de usuario.",
            )
            if st.button(":material/person_add: Registrarme", type="primary"):
                try:
                    rol = registrar_usuario(nombre, correo, password, invite_code)
                except (RuntimeError, ValueError) as error:
                    st.error(str(error))
                else:
                    st.success(
                        "Cuenta de administrador creada."
                        if rol == "admin"
                        else "Cuenta creada. Ya puedes iniciar sesión.",
                        icon=":material/check_circle:",
                    )

with tab_admin:
    usuario = st.session_state.get("usuario")
    if not usuario or usuario.get("rol") != "admin":
        st.info(
            "Inicia sesión con una cuenta administradora para gestionar las ofertas.",
            icon=":material/lock:",
        )
    else:
        st.subheader("Administración de oportunidades")
        ofertas_admin = consultar_ofertas_admin()
        for oferta in ofertas_admin:
            with st.expander(
                f"{'Disponible' if oferta['activo'] else 'No disponible'} · "
                f"{oferta['titulo']} · {oferta['fecha']}"
            ):
                with st.form(f"editar_oferta_{oferta['id']}"):
                    nuevo_titulo = st.text_input("Título", oferta["titulo"])
                    nueva_fuente = st.text_input("Fuente", oferta["fuente"])
                    nueva_direccion = st.text_input("Dirección", oferta["direccion"])
                    nuevo_telefono = st.text_input("Teléfono", oferta["telefono"])
                    nuevos_requisitos = st.text_area("Requisitos", oferta["req"])
                    nueva_activa = st.checkbox("Disponible en el catálogo", oferta["activo"])
                    guardar_cambios = st.form_submit_button("Guardar cambios")
                if guardar_cambios:
                    actualizar_oferta_bd(
                        oferta["id"], nuevo_titulo, nueva_fuente, nueva_direccion,
                        nuevo_telefono, nuevos_requisitos, nueva_activa,
                    )
                    st.toast("Oferta actualizada.")
                    st.rerun()
                if st.button("Desactivar oferta", key=f"desactivar_{oferta['id']}"):
                    desactivar_oferta_bd(oferta["id"])
                    st.toast("Oferta marcada como no disponible.")
                    st.rerun()
