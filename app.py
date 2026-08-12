import streamlit as st
from datetime import date

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
    placeholder="Ejemplo: Wuhan Three Towns"
)

equipo_b = st.text_input(
    "Equipo B",
    placeholder="Ejemplo: Zhejiang"
)

fecha_partido = st.date_input(
    "Fecha del partido",
    value=date.today()
)


# ============================================================
# BOTÓN
# ============================================================

if st.button(
    "🔎 Buscar partido",
    use_container_width=True
):

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

    with st.spinner(
        "Buscando información en Sofascore..."
    ):

        datos = analizar_partido(
            equipo_a.strip(),
            equipo_b.strip(),
            fecha_partido.strftime(
                "%Y-%m-%d"
            )
        )


    # ========================================================
    # ERROR
    # ========================================================

    if "error" in datos:

        st.error(
            datos["error"]
        )

        st.stop()


    nombre_a = datos["equipo_a"]
    nombre_b = datos["equipo_b"]


    # ========================================================
    # INFORMACIÓN ENCONTRADA
    # ========================================================

    st.success(
        f"Equipos encontrados: "
        f"{nombre_a} vs {nombre_b}"
    )


    # ========================================================
    # FUNCIÓN PARA MOSTRAR PARTIDO
    # ========================================================

    def mostrar_partido(evento):

        if not evento:

            st.info(
                "No se encontró un partido válido."
            )

            return


        fecha = evento.get(
            "startTimestamp"
        )

        if fecha:

            from datetime import datetime

            fecha_formateada = (
                datetime.fromtimestamp(
                    fecha
                ).strftime(
                    "%d/%m/%Y"
                )
            )

        else:

            fecha_formateada = (
                "Fecha no disponible"
            )


        local = (
            evento
            .get("homeTeam", {})
            .get("name", "")
        )

        visitante = (
            evento
            .get("awayTeam", {})
            .get("name", "")
        )


        # ====================================================
        # RESULTADO
        # ====================================================

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


        st.write(
            f"**Fecha:** {fecha_formateada}"
        )

        st.write(
            f"**Partido:** "
            f"{local} vs {visitante}"
        )


        if (
            home_score is not None
            and away_score is not None
        ):

            st.write(
                f"**Resultado:** "
                f"{home_score} - {away_score}"
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


    # ========================================================
    # ENFRENTAMIENTOS DIRECTOS
    # ========================================================

    st.divider()

    st.header(
        "Enfrentamientos directos"
    )


    h2h = datos.get(
        "h2h",
        []
    )


    if len(h2h) >= 1:

        st.subheader(
            "El último encuentro se disputó el:"
        )

        mostrar_partido(
            h2h[0]
        )


    else:

        st.info(
            "No se encontró un enfrentamiento directo."
        )


    if len(h2h) >= 2:

        st.subheader(
            "El último encuentro anterior "
            "entre ambos se disputó el:"
        )

        mostrar_partido(
            h2h[1]
        )


    # ========================================================
    # WUHAN / EQUIPO A
    # ========================================================

    st.divider()

    st.header(
        nombre_a
    )


    st.subheader(
        "El último partido que jugó como LOCAL"
    )

    st.write(
        "Las estadísticas fueron las siguientes:"
    )

    mostrar_partido(
        datos.get("local_a")
    )


    st.subheader(
        "El último partido que jugó como VISITANTE"
    )

    st.write(
        "Las estadísticas fueron las siguientes:"
    )

    mostrar_partido(
        datos.get("visitante_a")
    )


    # ========================================================
    # ZHEJIANG / EQUIPO B
    # ========================================================

    st.divider()

    st.header(
        nombre_b
    )


    st.subheader(
        "El último partido que jugó como LOCAL"
    )

    st.write(
        "Las estadísticas fueron las siguientes:"
    )

    mostrar_partido(
        datos.get("local_b")
    )


    st.subheader(
        "El último partido que jugó como VISITANTE"
    )

    st.write(
        "Las estadísticas fueron las siguientes:"
    )

    mostrar_partido(
        datos.get("visitante_b")
    )