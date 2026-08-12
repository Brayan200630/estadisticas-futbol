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
    "Consulta los últimos partidos relevantes de dos equipos "
    "y sus enfrentamientos directos dentro de la liga seleccionada."
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
    placeholder="Ejemplo: Sporting Cristal"
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

    timestamp = evento.get("startTimestamp")

    if not timestamp:
        return "Fecha no disponible"

    try:

        return datetime.fromtimestamp(
            timestamp
        ).strftime("%d/%m/%Y")

    except Exception:

        return "Fecha no disponible"


# ============================================================
# FUNCIÓN PARA MOSTRAR ESTADÍSTICA
# ============================================================

def mostrar_estadistica(
    etiqueta,
    datos,
    local,
    visitante
):

    if (
        datos is not None
        and isinstance(datos, (list, tuple))
        and len(datos) >= 2
        and datos[0] is not None
        and datos[1] is not None
    ):

        st.write(
            f"**{etiqueta}:** "
            f"{local} {datos[0]} - "
            f"{datos[1]} {visitante}"
        )

    else:

        st.write(
            f"**{etiqueta}:** Datos no disponibles"
        )


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

    home_team = evento.get(
        "homeTeam",
        {}
    )

    away_team = evento.get(
        "awayTeam",
        {}
    )

    local = home_team.get(
        "name",
        "Local"
    )

    visitante = away_team.get(
        "name",
        "Visitante"
    )


    # ========================================================
    # FECHA
    # ========================================================

    fecha_formateada = formatear_fecha(
        evento
    )


    # ========================================================
    # TORNEO
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
    # INFORMACIÓN PRINCIPAL
    # ========================================================

    st.write(
        f"**Fecha:** {fecha_formateada}"
    )

    st.write(
        f"**Partido:** {local} vs {visitante}"
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
        and away_score is not None
    ):

        st.write(
            f"**Resultado:** "
            f"{home_score} - {away_score}"
        )


    # ========================================================
    # ESTADÍSTICAS
    # ========================================================

    with st.spinner(
        "Cargando estadísticas..."
    ):

        estadisticas = obtener_estadisticas(
            evento
        )


    if not estadisticas:

        st.warning(
            "Sofascore no devolvió estadísticas para este partido."
        )

        return


    # ========================================================
    # POSESIÓN
    # ========================================================

    mostrar_estadistica(
        "Posesión",
        estadisticas.get("Posesión"),
        local,
        visitante
    )


    # ========================================================
    # CÓRNERS
    # ========================================================

    mostrar_estadistica(
        "Saques de esquina",
        estadisticas.get("Córners"),
        local,
        visitante
    )


    # ========================================================
    # FALTAS
    # ========================================================

    mostrar_estadistica(
        "Faltas",
        estadisticas.get("Faltas"),
        local,
        visitante
    )


    # ========================================================
    # TARJETAS
    # ========================================================

    mostrar_estadistica(
        "Tarjetas amarillas",
        estadisticas.get("Tarjetas amarillas"),
        local,
        visitante
    )


    # ========================================================
    # TIROS A PUERTA
    # ========================================================

    mostrar_estadistica(
        "Tiros a puerta",
        estadisticas.get("Tiros a puerta"),
        local,
        visitante
    )


    # ========================================================
    # FUERAS DE JUEGO
    # ========================================================

    mostrar_estadistica(
        "Fueras de juego",
        estadisticas.get("Fueras de juego"),
        local,
        visitante
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
    # BÚSQUEDA
    # ========================================================

    with st.spinner(
        "Buscando información en Sofascore..."
    ):

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
    # ENFRENTAMIENTOS DIRECTOS
    # ========================================================

    st.divider()

    st.header(
        "🤝 Enfrentamientos directos"
    )

    st.caption(
        f"Se muestran únicamente enfrentamientos entre "
        f"{nombre_a} y {nombre_b}, disputados en "
        f"{liga}, antes del {fecha_partido.strftime('%d/%m/%Y')}."
    )


    h2h = datos.get(
        "h2h",
        []
    )


    if h2h:

        # ----------------------------------------------------
        # ÚLTIMO H2H
        # ----------------------------------------------------

        st.subheader(
            "Último enfrentamiento en la liga"
        )

        mostrar_partido(
            h2h[0]
        )


        # ----------------------------------------------------
        # SEGUNDO H2H
        # ----------------------------------------------------

        if len(h2h) >= 2:

            st.subheader(
                "Enfrentamiento anterior"
            )

            mostrar_partido(
                h2h[1]
            )


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
    # LOCAL A
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
        local_a
    )


    # ========================================================
    # VISITANTE A
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
        visitante_a
    )


    # ========================================================
    # EQUIPO B
    # ========================================================

    st.divider()

    st.header(
        f"⚽ {nombre_b}"
    )


    # ========================================================
    # LOCAL B
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
        local_b
    )


    # ========================================================
    # VISITANTE B
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
        visitante_b
    )