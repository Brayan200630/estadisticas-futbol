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
    "Consulta los últimos partidos relevantes de dos equipos, "
    "incluyendo enfrentamientos directos."
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
            timestamp
        ).strftime("%d/%m/%Y")

    except Exception:

        return "Fecha no disponible"


# ============================================================
# FUNCIÓN PARA MOSTRAR ESTADÍSTICAS
# ============================================================

def mostrar_estadistica(
    nombre,
    valor,
    local,
    visitante
):

    if (
        isinstance(valor, (list, tuple))
        and len(valor) >= 2
    ):

        st.write(
            f"**{nombre}:** "
            f"{local} {valor[0]} - "
            f"{valor[1]} {visitante}"
        )

    else:

        st.write(
            f"**{nombre}:** "
            "Datos no disponibles"
        )


# ============================================================
# FUNCIÓN PRINCIPAL PARA MOSTRAR PARTIDO
# ============================================================

def mostrar_partido(
    evento,
    titulo=None
):

    if not evento:

        st.warning(
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
        "Equipo local"
    )

    visitante = away_team.get(
        "name",
        "Equipo visitante"
    )


    # ========================================================
    # FECHA
    # ========================================================

    fecha = formatear_fecha(
        evento
    )


    # ========================================================
    # TORNEO
    # ========================================================

    torneo = ""

    unique = evento.get(
        "uniqueTournament",
        {}
    )

    if unique:

        torneo = unique.get(
            "name",
            ""
        )


    if not torneo:

        tournament = evento.get(
            "tournament",
            {}
        )

        torneo = tournament.get(
            "name",
            ""
        )


    # ========================================================
    # TÍTULO
    # ========================================================

    if titulo:

        st.subheader(
            titulo
        )


    # ========================================================
    # INFORMACIÓN
    # ========================================================

    st.write(
        f"**Fecha:** {fecha}"
    )

    st.write(
        f"**Partido:** "
        f"{local} vs {visitante}"
    )


    if torneo:

        st.write(
            f"**Liga:** {torneo}"
        )


    # ========================================================
    # RESULTADO
    # ========================================================

    home_score = evento.get(
        "homeScore",
        {}
    ).get(
        "current"
    )

    away_score = evento.get(
        "awayScore",
        {}
    ).get(
        "current"
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

    with st.spinner(
        "Cargando estadísticas..."
    ):

        estadisticas = obtener_estadisticas(
            evento
        )


    # ========================================================
    # POSESIÓN
    # ========================================================

    mostrar_estadistica(
        "Posesión",
        estadisticas.get(
            "Posesión"
        ),
        local,
        visitante
    )


    # ========================================================
    # CÓRNERS
    # ========================================================

    mostrar_estadistica(
        "Saques de esquina",
        estadisticas.get(
            "Córners"
        ),
        local,
        visitante
    )


    # ========================================================
    # FALTAS
    # ========================================================

    mostrar_estadistica(
        "Faltas",
        estadisticas.get(
            "Faltas"
        ),
        local,
        visitante
    )


    # ========================================================
    # TARJETAS
    # ========================================================

    mostrar_estadistica(
        "Tarjetas amarillas",
        estadisticas.get(
            "Tarjetas amarillas"
        ),
        local,
        visitante
    )


    # ========================================================
    # TIROS A PUERTA
    # ========================================================

    mostrar_estadistica(
        "Tiros a puerta",
        estadisticas.get(
            "Tiros a puerta"
        ),
        local,
        visitante
    )


    # ========================================================
    # FUERAS DE JUEGO
    # ========================================================

    mostrar_estadistica(
        "Fueras de juego",
        estadisticas.get(
            "Fueras de juego"
        ),
        local,
        visitante
    )


# ============================================================
# BOTÓN DE BÚSQUEDA
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
        f"Liga seleccionada: {liga}"
    )


    # ========================================================
    # FECHA DE CORTE
    # ========================================================

    st.caption(
        "Todos los partidos mostrados deben ser "
        f"anteriores al {fecha_partido.strftime('%d/%m/%Y')}."
    )


    # ========================================================
    # H2H
    # ========================================================

    st.divider()

    st.header(
        "🤝 Enfrentamientos directos"
    )

    h2h = datos.get(
        "h2h",
        []
    )


    # ========================================================
    # COMPROBAR H2H
    # ========================================================

    if h2h:

        # ----------------------------------------------------
        # PRIMER H2H
        # ----------------------------------------------------

        if len(h2h) >= 1:

            mostrar_partido(
                h2h[0],
                "Último enfrentamiento directo"
            )


        # ----------------------------------------------------
        # SEGUNDO H2H
        # ----------------------------------------------------

        if len(h2h) >= 2:

            st.divider()

            mostrar_partido(
                h2h[1],
                "Último enfrentamiento anterior"
            )


    else:

        st.warning(
            f"No se encontró un enfrentamiento directo "
            f"válido entre {nombre_a} y {nombre_b} "
            f"en la liga '{liga}' antes del "
            f"{fecha_partido.strftime('%d/%m/%Y')}."
        )


    # ========================================================
    # EQUIPO A
    # ========================================================

    st.divider()

    st.header(
        f"🏠 {nombre_a}"
    )


    # ========================================================
    # LOCAL A
    # ========================================================

    mostrar_partido(
        datos.get(
            "local_a"
        ),
        "Último partido como LOCAL"
    )


    # ========================================================
    # VISITANTE A
    # ========================================================

    st.divider()

    mostrar_partido(
        datos.get(
            "visitante_a"
        ),
        "Último partido como VISITANTE"
    )


    # ========================================================
    # EQUIPO B
    # ========================================================

    st.divider()

    st.header(
        f"✈️ {nombre_b}"
    )


    # ========================================================
    # LOCAL B
    # ========================================================

    mostrar_partido(
        datos.get(
            "local_b"
        ),
        "Último partido como LOCAL"
    )


    # ========================================================
    # VISITANTE B
    # ========================================================

    st.divider()

    mostrar_partido(
        datos.get(
            "visitante_b"
        ),
        "Último partido como VISITANTE"
    )