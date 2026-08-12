import streamlit as st
from datetime import date, datetime

from main import (
    analizar_partido,
    obtener_estadisticas
)


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
    "Consulta los últimos partidos relevantes de dos equipos "
    "y sus enfrentamientos directos en la liga seleccionada."
)


# ============================================================
# DATOS DEL PARTIDO
# ============================================================

equipo_a = st.text_input(
    "Equipo A",
    placeholder="Ejemplo: Universitario"
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
# FECHA DEL PARTIDO
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

    if not timestamp:
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

def mostrar_partido(
    evento,
    mostrar_estadisticas=True
):

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

    fecha = formatear_fecha(
        evento
    )


    # ========================================================
    # LIGA
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


    # ========================================================
    # MOSTRAR INFORMACIÓN
    # ========================================================

    st.write(
        f"**Fecha:** {fecha}"
    )

    st.write(
        f"**Partido:** {local} vs {visitante}"
    )

    if torneo:

        st.write(
            f"**Liga:** {torneo}"
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

    if not mostrar_estadisticas:

        return


    with st.spinner(
        "Cargando estadísticas..."
    ):

        estadisticas = obtener_estadisticas(
            evento
        )


    if not estadisticas:

        st.warning(
            "No se pudieron obtener las estadísticas."
        )

        return


    # ========================================================
    # POSESIÓN
    # ========================================================

    posesion = estadisticas.get(
        "Posesión"
    )

    if posesion:

        st.write(
            f"**Posesión:** "
            f"{local} {posesion[0]} - "
            f"{posesion[1]} {visitante}"
        )

    else:

        st.write(
            "**Posesión:** Datos no disponibles"
        )


    # ========================================================
    # CÓRNERS
    # ========================================================

    corners = estadisticas.get(
        "Córners"
    )

    if corners:

        st.write(
            f"**Córners:** "
            f"{local} {corners[0]} - "
            f"{corners[1]} {visitante}"
        )

    else:

        st.write(
            "**Córners:** Datos no disponibles"
        )


    # ========================================================
    # FALTAS
    # ========================================================

    faltas = estadisticas.get(
        "Faltas"
    )

    if faltas:

        st.write(
            f"**Faltas:** "
            f"{local} {faltas[0]} - "
            f"{faltas[1]} {visitante}"
        )

    else:

        st.write(
            "**Faltas:** Datos no disponibles"
        )


    # ========================================================
    # TARJETAS
    # ========================================================

    tarjetas = estadisticas.get(
        "Tarjetas amarillas"
    )

    if tarjetas:

        st.write(
            f"**Tarjetas amarillas:** "
            f"{local} {tarjetas[0]} - "
            f"{tarjetas[1]} {visitante}"
        )

    else:

        st.write(
            "**Tarjetas amarillas:** Datos no disponibles"
        )


    # ========================================================
    # TIROS A PUERTA
    # ========================================================

    tiros = estadisticas.get(
        "Tiros a puerta"
    )

    if tiros:

        st.write(
            f"**Tiros a puerta:** "
            f"{local} {tiros[0]} - "
            f"{tiros[1]} {visitante}"
        )

    else:

        st.write(
            "**Tiros a puerta:** Datos no disponibles"
        )


    # ========================================================
    # FUERAS DE JUEGO
    # ========================================================

    fueras = estadisticas.get(
        "Fueras de juego"
    )

    if fueras:

        st.write(
            f"**Fueras de juego:** "
            f"{local} {fueras[0]} - "
            f"{fueras[1]} {visitante}"
        )

    else:

        st.write(
            "**Fueras de juego:** Datos no disponibles"
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
    # FECHA
    # ========================================================

    fecha_str = fecha_partido.strftime(
        "%Y-%m-%d"
    )


    # ========================================================
    # BÚSQUEDA
    # ========================================================

    with st.spinner(
        "Buscando información en Sofascore..."
    ):

        datos = analizar_partido(
            equipo_a.strip(),
            equipo_b.strip(),
            fecha_str,
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


    # ========================================================
    # NOMBRES
    # ========================================================

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
        f"Liga: {liga}"
    )

    st.info(
        f"Fecha de referencia: "
        f"{fecha_partido.strftime('%d/%m/%Y')}"
    )


    # ========================================================
    # H2H
    # ========================================================

    st.divider()

    st.header(
        "🤝 Enfrentamientos directos"
    )

    st.caption(
        "Se muestran los enfrentamientos más recientes "
        "entre ambos equipos, anteriores a la fecha indicada "
        "y pertenecientes a la liga seleccionada."
    )


    h2h = datos.get(
        "h2h",
        []
    )


    # --------------------------------------------------------
    # SI EXISTEN H2H
    # --------------------------------------------------------

    if h2h:

        for indice, evento in enumerate(
            h2h,
            start=1
        ):

            if indice == 1:

                st.subheader(
                    "Último enfrentamiento"
                )

            else:

                st.subheader(
                    f"Enfrentamiento anterior #{indice}"
                )


            mostrar_partido(
                evento,
                mostrar_estadisticas=True
            )


            if indice < len(h2h):

                st.divider()


    else:

        st.warning(
            "No se encontraron enfrentamientos directos "
            "válidos en la liga seleccionada antes de "
            "la fecha indicada."
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


    mostrar_partido(
        local_a,
        mostrar_estadisticas=True
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


    mostrar_partido(
        visitante_a,
        mostrar_estadisticas=True
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


    mostrar_partido(
        local_b,
        mostrar_estadisticas=True
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


    mostrar_partido(
        visitante_b,
        mostrar_estadisticas=True
    )