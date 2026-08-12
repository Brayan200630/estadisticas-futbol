import streamlit as st
from datetime import date, datetime

from main import analizar_partido, obtener_estadisticas


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Estadísticas de Fútbol",
    page_icon="⚽",
    layout="wide"
)


# ============================================================
# DISEÑO VISUAL
# ============================================================

st.markdown("""
<style>

    /* --------------------------------------------------------
       FONDO GENERAL
    -------------------------------------------------------- */

    .stApp {
        background: #f5f7fa;
    }

    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }


    /* --------------------------------------------------------
       TÍTULO PRINCIPAL
    -------------------------------------------------------- */

    .titulo-principal {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        color: #111827;
        margin-bottom: 5px;
    }

    .subtitulo-principal {
        text-align: center;
        color: #6b7280;
        font-size: 17px;
        margin-bottom: 30px;
    }


    /* --------------------------------------------------------
       PANEL DE BÚSQUEDA
    -------------------------------------------------------- */

    .panel-busqueda {
        background: white;
        border-radius: 18px;
        padding: 28px;
        margin-bottom: 30px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.07);
        border: 1px solid #e5e7eb;
    }


    /* --------------------------------------------------------
       TÍTULOS DE SECCIÓN
    -------------------------------------------------------- */

    .titulo-seccion {
        font-size: 27px;
        font-weight: 800;
        color: #111827;
        margin-top: 20px;
        margin-bottom: 18px;
    }

    .subtitulo-seccion {
        font-size: 21px;
        font-weight: 700;
        color: #1f2937;
        margin-top: 20px;
        margin-bottom: 12px;
    }


    /* --------------------------------------------------------
       TARJETA DE PARTIDO
    -------------------------------------------------------- */

    .tarjeta-partido {
        background: white;
        border-radius: 16px;
        padding: 22px;
        margin-top: 10px;
        margin-bottom: 20px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 3px 12px rgba(0,0,0,0.06);
    }

    .liga-partido {
        text-align: center;
        color: #6b7280;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 4px;
    }

    .fecha-partido {
        text-align: center;
        color: #9ca3af;
        font-size: 13px;
        margin-bottom: 15px;
    }

    .equipos-partido {
        text-align: center;
        font-size: 20px;
        font-weight: 700;
        color: #111827;
        margin-bottom: 8px;
    }

    .resultado-partido {
        text-align: center;
        font-size: 34px;
        font-weight: 900;
        color: #111827;
        margin-bottom: 10px;
    }

    .penales-partido {
        text-align: center;
        color: #2563eb;
        font-size: 14px;
        font-weight: 700;
        margin-bottom: 15px;
    }


    /* --------------------------------------------------------
       TARJETAS DE ESTADÍSTICAS
    -------------------------------------------------------- */

    .estadistica {
        background: #f9fafb;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
        border: 1px solid #edf0f3;
        margin-top: 8px;
    }

    .estadistica-nombre {
        font-size: 12px;
        color: #6b7280;
        font-weight: 600;
        margin-bottom: 4px;
    }

    .estadistica-valor {
        font-size: 16px;
        color: #111827;
        font-weight: 800;
    }


    /* --------------------------------------------------------
       SEPARADORES
    -------------------------------------------------------- */

    .separador {
        height: 1px;
        background: #e5e7eb;
        margin: 35px 0;
    }


    /* --------------------------------------------------------
       BOTÓN
    -------------------------------------------------------- */

    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 48px;
        font-size: 17px;
        font-weight: 700;
    }


    /* --------------------------------------------------------
       MENSAJES
    -------------------------------------------------------- */

    .mensaje-vacio {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 15px;
        color: #6b7280;
        text-align: center;
        margin-bottom: 20px;
    }

</style>
""", unsafe_allow_html=True)


# ============================================================
# TÍTULO
# ============================================================

st.markdown(
    '<div class="titulo-principal">⚽ Estadísticas de Fútbol</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitulo-principal">'
    'Consulta los últimos partidos relevantes de dos equipos'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# PANEL DE BÚSQUEDA
# ============================================================

st.markdown(
    '<div class="panel-busqueda">',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="titulo-seccion">🔎 Buscar partido</div>',
    unsafe_allow_html=True
)

equipo_a = st.text_input(
    "Equipo A",
    placeholder="Ejemplo: Universitario de Deportes"
)

equipo_b = st.text_input(
    "Equipo B",
    placeholder="Ejemplo: Alianza Lima"
)

liga = st.text_input(
    "Liga o competición",
    placeholder="Ejemplo: Liga 1 / Copa Libertadores"
)

fecha_partido = st.date_input(
    "Fecha del partido",
    value=date.today()
)

if st.button(
    "🔎 Buscar partido",
    use_container_width=True
):

    # ========================================================
    # VALIDACIONES
    # ========================================================

    if not equipo_a.strip():

        st.error(
            "Escribe el nombre del Equipo A."
        )

        st.stop()


    if not equipo_b.strip():

        st.error(
            "Escribe el nombre del Equipo B."
        )

        st.stop()


    if not liga.strip():

        st.error(
            "Escribe la liga."
        )

        st.stop()


    # ========================================================
    # RANGO DE BÚSQUEDA
    # ========================================================

    fecha_inicio = date(
        2020,
        1,
        1
    )

    fecha_fin = fecha_partido


    if fecha_fin <= fecha_inicio:

        st.error(
            "La fecha del partido debe ser posterior "
            "al 01/01/2020."
        )

        st.stop()


    # ========================================================
    # INFORMACIÓN DEL RANGO
    # ========================================================

    st.info(
        f"📅 Buscando partidos desde "
        f"**{fecha_inicio.strftime('%d/%m/%Y')}** "
        f"hasta antes del "
        f"**{fecha_fin.strftime('%d/%m/%Y')}**."
    )


    # ========================================================
    # BÚSQUEDA
    # ========================================================

    with st.spinner(
        "Buscando información en SofaScore..."
    ):

        print(
            "===== INICIO DE BUSQUEDA ====="
        )

        print(
            "Equipo A:",
            equipo_a.strip()
        )

        print(
            "Equipo B:",
            equipo_b.strip()
        )

        print(
            "Liga:",
            liga.strip()
        )

        print(
            "Fecha:",
            fecha_partido
        )

        print(
            "RANGO:",
            fecha_inicio,
            "->",
            fecha_fin
        )


        datos = analizar_partido(
            equipo_a.strip(),
            equipo_b.strip(),
            fecha_partido.strftime(
                "%Y-%m-%d"
            ),
            liga.strip()
        )


    # ========================================================
    # ERROR
    # ========================================================

    if not datos:

        st.error(
            "No se recibieron datos."
        )

        st.stop()


    if "error" in datos:

        st.error(
            datos["error"]
        )

        st.stop()


    nombre_a = datos.get(
        "equipo_a",
        equipo_a
    )

    nombre_b = datos.get(
        "equipo_b",
        equipo_b
    )


    # ========================================================
    # INFORMACIÓN ENCONTRADA
    # ========================================================

    st.success(
        f"Equipos encontrados: "
        f"{nombre_a} vs {nombre_b}"
    )

    st.info(
        f"🏆 Liga seleccionada: {liga}"
    )


    # ========================================================
    # FUNCIÓN PARA FORMATEAR FECHA
    # ========================================================

    def formatear_fecha(evento):

        if not evento:
            return "Fecha no disponible"

        timestamp = evento.get(
            "startTimestamp"
        )

        if timestamp is None:
            return "Fecha no disponible"

        try:

            return datetime.fromtimestamp(
                int(timestamp)
            ).strftime(
                "%d/%m/%Y"
            )

        except Exception:

            return "Fecha no disponible"


    # ========================================================
    # FUNCIÓN PARA MOSTRAR RESULTADO
    # ========================================================

    def obtener_resultado(evento):

        if not evento:
            return None

        home_score = evento.get(
            "homeScore",
            {}
        )

        away_score = evento.get(
            "awayScore",
            {}
        )

        if not isinstance(
            home_score,
            dict
        ):

            home_score = {}

        if not isinstance(
            away_score,
            dict
        ):

            away_score = {}


        # ----------------------------------------------------
        # RESULTADO NORMAL
        # ----------------------------------------------------

        home = home_score.get(
            "current"
        )

        away = away_score.get(
            "current"
        )


        if home is None or away is None:

            return None


        resultado = f"{home} - {away}"


        # ----------------------------------------------------
        # DETECTAR PENALES
        # ----------------------------------------------------

        home_penalty = (
            home_score.get(
                "penalties"
            )
        )

        away_penalty = (
            away_score.get(
                "penalties"
            )
        )


        if (
            home_penalty is not None
            and
            away_penalty is not None
        ):

            try:

                if (
                    int(home_penalty) >= 0
                    and
                    int(away_penalty) >= 0
                ):

                    return (
                        f"{home} ({home_penalty}) "
                        f"- "
                        f"{away} ({away_penalty})"
                    )

            except Exception:

                pass


        # ----------------------------------------------------
        # ALGUNAS RESPUESTAS PUEDEN USAR PENALTY
        # ----------------------------------------------------

        home_penalty = (
            home_score.get(
                "penalty"
            )
        )

        away_penalty = (
            away_score.get(
                "penalty"
            )
        )


        if (
            home_penalty is not None
            and
            away_penalty is not None
        ):

            try:

                return (
                    f"{home} ({home_penalty}) "
                    f"- "
                    f"{away} ({away_penalty})"
                )

            except Exception:

                pass


        return resultado


    # ========================================================
    # FUNCIÓN PARA MOSTRAR PARTIDO
    # ========================================================

    def mostrar_partido(evento):

        if not evento:

            st.markdown(
                '<div class="mensaje-vacio">'
                'No se encontró un partido válido.'
                '</div>',
                unsafe_allow_html=True
            )

            return


        # ====================================================
        # EQUIPOS
        # ====================================================

        local = (
            evento
            .get("homeTeam", {})
            .get(
                "name",
                "Desconocido"
            )
        )

        visitante = (
            evento
            .get("awayTeam", {})
            .get(
                "name",
                "Desconocido"
            )
        )


        # ====================================================
        # FECHA
        # ====================================================

        fecha_formateada = formatear_fecha(
            evento
        )


        # ====================================================
        # TORNEO
        # ====================================================

        torneo = (
            evento
            .get("uniqueTournament", {})
            .get("name")
        )


        if not torneo:

            torneo = (
                evento
                .get("tournament", {})
                .get("name")
            )


        # ====================================================
        # RESULTADO
        # ====================================================

        resultado = obtener_resultado(
            evento
        )


        # ====================================================
        # MOSTRAR TARJETA
        # ====================================================

        torneo_html = (
            torneo
            if torneo
            else "Competición no disponible"
        )


        resultado_html = (
            resultado
            if resultado
            else "Resultado no disponible"
        )


        st.markdown(
            f"""
            <div class="tarjeta-partido">

                <div class="liga-partido">
                    🏆 {torneo_html}
                </div>

                <div class="fecha-partido">
                    📅 {fecha_formateada}
                </div>

                <div class="equipos-partido">
                    {local} &nbsp; vs &nbsp; {visitante}
                </div>

                <div class="resultado-partido">
                    {resultado_html}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


        # ====================================================
        # ESTADÍSTICAS
        # ====================================================

        estadisticas = obtener_estadisticas(
            evento
        )


        posesion = estadisticas.get(
            "Posesión"
        )

        corners = estadisticas.get(
            "Córners"
        )

        faltas = estadisticas.get(
            "Faltas"
        )

        tarjetas = estadisticas.get(
            "Tarjetas amarillas"
        )

        tiros = estadisticas.get(
            "Tiros a puerta"
        )

        fueras = estadisticas.get(
            "Fueras de juego"
        )


        # ====================================================
        # FUNCIÓN ESTADÍSTICA
        # ====================================================

        def mostrar_estadistica(
            nombre,
            valor
        ):

            if valor:

                st.markdown(
                    f"""
                    <div class="estadistica">

                        <div class="estadistica-nombre">
                            {nombre}
                        </div>

                        <div class="estadistica-valor">
                            {valor[0]} — {valor[1]}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

            else:

                st.markdown(
                    f"""
                    <div class="estadistica">

                        <div class="estadistica-nombre">
                            {nombre}
                        </div>

                        <div class="estadistica-valor">
                            —
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )


        # ====================================================
        # MOSTRAR ESTADÍSTICAS EN COLUMNAS
        # ====================================================

        col1, col2, col3 = st.columns(3)

        with col1:

            mostrar_estadistica(
                "Posesión",
                posesion
            )

            mostrar_estadistica(
                "Córners",
                corners
            )


        with col2:

            mostrar_estadistica(
                "Faltas",
                faltas
            )

            mostrar_estadistica(
                "Tarjetas amarillas",
                tarjetas
            )


        with col3:

            mostrar_estadistica(
                "Tiros a puerta",
                tiros
            )

            mostrar_estadistica(
                "Fueras de juego",
                fueras
            )


    # ========================================================
    # H2H
    # ========================================================

    st.markdown(
        '<div class="separador"></div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="titulo-seccion">'
        '🔁 Enfrentamientos directos'
        '</div>',
        unsafe_allow_html=True
    )


    # ========================================================
    # H2H EQUIPO A LOCAL
    # ========================================================

    st.markdown(
        f'<div class="subtitulo-seccion">'
        f'🏠 {nombre_a} como LOCAL'
        f'</div>',
        unsafe_allow_html=True
    )


    h2h_a_local = datos.get(
        "h2h_a_local"
    )


    if h2h_a_local:

        mostrar_partido(
            h2h_a_local
        )

    else:

        st.markdown(
            f"""
            <div class="mensaje-vacio">
                No se encontró un enfrentamiento de
                <strong>{nombre_a}</strong> como local
                dentro del período seleccionado.
            </div>
            """,
            unsafe_allow_html=True
        )


    # ========================================================
    # H2H EQUIPO A VISITANTE
    # ========================================================

    st.markdown(
        f'<div class="subtitulo-seccion">'
        f'✈️ {nombre_a} como VISITANTE'
        f'</div>',
        unsafe_allow_html=True
    )


    h2h_a_visitante = datos.get(
        "h2h_a_visitante"
    )


    if h2h_a_visitante:

        mostrar_partido(
            h2h_a_visitante
        )

    else:

        st.markdown(
            f"""
            <div class="mensaje-vacio">
                No se encontró un enfrentamiento de
                <strong>{nombre_a}</strong> como visitante
                dentro del período seleccionado.
            </div>
            """,
            unsafe_allow_html=True
        )


    # ========================================================
    # EQUIPO A
    # ========================================================

    st.markdown(
        '<div class="separador"></div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="titulo-seccion">'
        f'⚽ {nombre_a}'
        f'</div>',
        unsafe_allow_html=True
    )


    # ========================================================
    # EQUIPO A LOCAL
    # ========================================================

    st.markdown(
        '<div class="subtitulo-seccion">'
        '🏠 Último partido como LOCAL'
        '</div>',
        unsafe_allow_html=True
    )


    local_a = datos.get(
        "local_a"
    )


    if local_a:

        mostrar_partido(
            local_a
        )

    else:

        st.markdown(
            '<div class="mensaje-vacio">'
            'No se encontró un partido válido '
            'dentro del período seleccionado.'
            '</div>',
            unsafe_allow_html=True
        )


    # ========================================================
    # EQUIPO A VISITANTE
    # ========================================================

    st.markdown(
        '<div class="subtitulo-seccion">'
        '✈️ Último partido como VISITANTE'
        '</div>',
        unsafe_allow_html=True
    )


    visitante_a = datos.get(
        "visitante_a"
    )


    if visitante_a:

        mostrar_partido(
            visitante_a
        )

    else:

        st.markdown(
            '<div class="mensaje-vacio">'
            'No se encontró un partido válido '
            'dentro del período seleccionado.'
            '</div>',
            unsafe_allow_html=True
        )


    # ========================================================
    # EQUIPO B
    # ========================================================

    st.markdown(
        '<div class="separador"></div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="titulo-seccion">'
        f'⚽ {nombre_b}'
        f'</div>',
        unsafe_allow_html=True
    )


    # ========================================================
    # EQUIPO B LOCAL
    # ========================================================

    st.markdown(
        '<div class="subtitulo-seccion">'
        '🏠 Último partido como LOCAL'
        '</div>',
        unsafe_allow_html=True
    )


    local_b = datos.get(
        "local_b"
    )


    if local_b:

        mostrar_partido(
            local_b
        )

    else:

        st.markdown(
            '<div class="mensaje-vacio">'
            'No se encontró un partido válido '
            'dentro del período seleccionado.'
            '</div>',
            unsafe_allow_html=True
        )


    # ========================================================
    # EQUIPO B VISITANTE
    # ========================================================

    st.markdown(
        '<div class="subtitulo-seccion">'
        '✈️ Último partido como VISITANTE'
        '</div>',
        unsafe_allow_html=True
    )


    visitante_b = datos.get(
        "visitante_b"
    )


    if visitante_b:

        mostrar_partido(
            visitante_b
        )

    else:

        st.markdown(
            '<div class="mensaje-vacio">'
            'No se encontró un partido válido '
            'dentro del período seleccionado.'
            '</div>',
            unsafe_allow_html=True
        )