import streamlit as st
from datetime import date, datetime

from main import analizar_partido, obtener_estadisticas


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Estadísticas de Fútbol",
    page_icon="⚽",
    layout="centered"
)


# ============================================================
# TÍTULO
# ============================================================

st.title("⚽ Estadísticas de Fútbol")

st.write(
    "Consulta estadísticas de los últimos partidos "
    "relevantes de dos equipos."
)


# ============================================================
# DATOS DEL PARTIDO
# ============================================================

equipo_a = st.text_input(
    "Equipo A",
    placeholder="Ejemplo: Universitario de Deportes"
)

equipo_b = st.text_input(
    "Equipo B",
    placeholder="Ejemplo: Alianza Lima"
)


# ============================================================
# LIGA
# ============================================================

liga = st.text_input(
    "Liga",
    placeholder="Ejemplo: Liga 1"
)


# ============================================================
# FECHA
# ============================================================

fecha_partido = st.date_input(
    "Fecha del partido",
    value=date.today()
)


# ============================================================
# FUNCIÓN PARA FORMATEAR FECHA
# ============================================================

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


# ============================================================
# FUNCIÓN PARA MOSTRAR PARTIDO
# ============================================================

def mostrar_partido(evento):

    if not evento:

        st.info(
            "No se encontró un partido válido."
        )

        return


    # ========================================================
    # EQUIPOS
    # ========================================================

    local = (
        evento
        .get("homeTeam", {})
        .get("name", "Desconocido")
    )

    visitante = (
        evento
        .get("awayTeam", {})
        .get("name", "Desconocido")
    )


    # ========================================================
    # FECHA
    # ========================================================

    fecha_formateada = formatear_fecha(
        evento
    )


    # ========================================================
    # TORNEO / LIGA
    # ========================================================

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

    if torneo:

        st.write(
            f"**Liga:** {torneo}"
        )


    # ========================================================
    # FECHA
    # ========================================================

    st.write(
        f"**Fecha:** {fecha_formateada}"
    )


    # ========================================================
    # PARTIDO
    # ========================================================

    st.write(
        f"**Partido:** "
        f"{local} vs {visitante}"
    )


    # ========================================================
    # RESULTADO
    # ========================================================

    home_score = (
        evento
        .get("homeScore", {})
        .get("current")
    )

    away_score = (
        evento
        .get("awayScore", {})
        .get("current")
    )

    if (
        home_score is not None
        and
        away_score is not None
    ):

        st.write(
            f"**Resultado:** "
            f"{home_score} - {away_score}"
        )


    # ========================================================
    # ESTADÍSTICAS
    # ========================================================

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


    # ========================================================
    # POSESIÓN
    # ========================================================

    if posesion:

        st.write(
            f"**Posesión:** "
            f"{local} {posesion[0]} - "
            f"{posesion[1]} {visitante}"
        )

    else:

        st.write(
            "**Posesión:** "
            "Datos no disponibles"
        )


    # ========================================================
    # CÓRNERS
    # ========================================================

    if corners:

        st.write(
            f"**Saques de esquina:** "
            f"{local} {corners[0]} - "
            f"{corners[1]} {visitante}"
        )

    else:

        st.write(
            "**Saques de esquina:** "
            "Datos no disponibles"
        )


    # ========================================================
    # FALTAS
    # ========================================================

    if faltas:

        st.write(
            f"**Faltas:** "
            f"{local} {faltas[0]} - "
            f"{faltas[1]} {visitante}"
        )

    else:

        st.write(
            "**Faltas:** "
            "Datos no disponibles"
        )


    # ========================================================
    # TARJETAS
    # ========================================================

    if tarjetas:

        st.write(
            f"**Tarjetas amarillas:** "
            f"{local} {tarjetas[0]} - "
            f"{tarjetas[1]} {visitante}"
        )

    else:

        st.write(
            "**Tarjetas amarillas:** "
            "Datos no disponibles"
        )


    # ========================================================
    # TIROS A PUERTA
    # ========================================================

    if tiros:

        st.write(
            f"**Tiros a puerta:** "
            f"{local} {tiros[0]} - "
            f"{tiros[1]} {visitante}"
        )

    else:

        st.write(
            "**Tiros a puerta:** "
            "Datos no disponibles"
        )


    # ========================================================
    # FUERAS DE JUEGO
    # ========================================================

    if fueras:

        st.write(
            f"**Fueras de juego:** "
            f"{local} {fueras[0]} - "
            f"{fueras[1]} {visitante}"
        )

    else:

        st.write(
            "**Fueras de juego:** "
            "Datos no disponibles"
        )


# ============================================================
# BOTÓN
# ============================================================

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
        "Buscando información en Sofascore..."
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
        f"Liga seleccionada: {liga}"
    )


    # ========================================================
    # H2H
    # ========================================================

    st.divider()

    st.header(
        "🔁 Enfrentamientos directos"
    )


    # ========================================================
    # H2H EQUIPO A LOCAL
    # ========================================================

    st.subheader(
        f"🏠 Último enfrentamiento "
        f"con {nombre_a} como LOCAL"
    )

    h2h_a_local = datos.get(
        "h2h_a_local"
    )

    if h2h_a_local:

        mostrar_partido(
            h2h_a_local
        )

    else:

        st.info(
            "No se encontró un enfrentamiento "
            f"de {nombre_a} como local en la "
            "liga seleccionada dentro del período "
            "01/01/2020 → fecha del partido."
        )


    # ========================================================
    # H2H EQUIPO A VISITANTE
    # ========================================================

    st.subheader(
        f"✈️ Último enfrentamiento "
        f"con {nombre_a} como VISITANTE"
    )

    h2h_a_visitante = datos.get(
        "h2h_a_visitante"
    )

    if h2h_a_visitante:

        mostrar_partido(
            h2h_a_visitante
        )

    else:

        st.info(
            "No se encontró un enfrentamiento "
            f"de {nombre_a} como visitante en la "
            "liga seleccionada dentro del período "
            "01/01/2020 → fecha del partido."
        )


    # ========================================================
    # EQUIPO A
    # ========================================================

    st.divider()

    st.header(
        f"⚽ {nombre_a}"
    )


    # ========================================================
    # EQUIPO A LOCAL
    # ========================================================

    st.subheader(
        "🏠 Último partido como LOCAL"
    )

    st.write(
        "Las estadísticas fueron las siguientes:"
    )

    local_a = datos.get(
        "local_a"
    )

    if local_a:

        mostrar_partido(
            local_a
        )

    else:

        st.info(
            "No se encontró un partido válido "
            "desde el 01/01/2020 hasta la fecha "
            "seleccionada."
        )


    # ========================================================
    # EQUIPO A VISITANTE
    # ========================================================

    st.subheader(
        "✈️ Último partido como VISITANTE"
    )

    st.write(
        "Las estadísticas fueron las siguientes:"
    )

    visitante_a = datos.get(
        "visitante_a"
    )

    if visitante_a:

        mostrar_partido(
            visitante_a
        )

    else:

        st.info(
            "No se encontró un partido válido "
            "desde el 01/01/2020 hasta la fecha "
            "seleccionada."
        )


    # ========================================================
    # EQUIPO B
    # ========================================================

    st.divider()

    st.header(
        f"⚽ {nombre_b}"
    )


    # ========================================================
    # EQUIPO B LOCAL
    # ========================================================

    st.subheader(
        "🏠 Último partido como LOCAL"
    )

    st.write(
        "Las estadísticas fueron las siguientes:"
    )

    local_b = datos.get(
        "local_b"
    )

    if local_b:

        mostrar_partido(
            local_b
        )

    else:

        st.info(
            "No se encontró un partido válido "
            "desde el 01/01/2020 hasta la fecha "
            "seleccionada."
        )


    # ========================================================
    # EQUIPO B VISITANTE
    # ========================================================

    st.subheader(
        "✈️ Último partido como VISITANTE"
    )

    st.write(
        "Las estadísticas fueron las siguientes:"
    )

    visitante_b = datos.get(
        "visitante_b"
    )

    if visitante_b:

        mostrar_partido(
            visitante_b
        )

    else:

        st.info(
            "No se encontró un partido válido "
            "desde el 01/01/2020 hasta la fecha "
            "seleccionada."
        )