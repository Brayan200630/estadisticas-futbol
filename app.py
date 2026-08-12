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
# FECHA
# ============================================================

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

        print(
            "===================================="
        )

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
            "===================================="
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
    # COMPROBAR ERROR
    # ========================================================

    if not datos:

        st.error(
            "Sofascore no devolvió información."
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


    liga_encontrada = datos.get(
        "liga",
        liga
    )


    # ========================================================
    # INFORMACIÓN ENCONTRADA
    # ========================================================

    st.success(
        f"Equipos encontrados: "
        f"{nombre_a} vs {nombre_b}"
    )


    st.info(
        f"Liga seleccionada: {liga_encontrada}"
    )


    # ========================================================
    # FUNCIÓN MOSTRAR PARTIDO
    # ========================================================

    def mostrar_partido(evento):

        if not evento:

            st.warning(
                "No se encontró un partido válido."
            )

            return


        # ====================================================
        # FECHA
        # ====================================================

        timestamp = evento.get(
            "startTimestamp"
        )


        if timestamp:

            try:

                fecha_formateada = (
                    datetime.fromtimestamp(
                        timestamp
                    ).strftime(
                        "%d/%m/%Y"
                    )
                )

            except Exception:

                fecha_formateada = (
                    "Fecha no disponible"
                )

        else:

            fecha_formateada = (
                "Fecha no disponible"
            )


        # ====================================================
        # EQUIPOS
        # ====================================================

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


        # ====================================================
        # LIGA
        # ====================================================

        torneo = ""

        unique_tournament = evento.get(
            "uniqueTournament",
            {}
        )


        if unique_tournament:

            torneo = unique_tournament.get(
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


        if torneo:

            st.write(
                f"**Liga:** {torneo}"
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
            and
            away_score is not None
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


        # ====================================================
        # POSESIÓN
        # ====================================================

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
                "**Posesión:** "
                "Datos no disponibles"
            )


        # ====================================================
        # CÓRNERS
        # ====================================================

        corners = estadisticas.get(
            "Córners"
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


        # ====================================================
        # FALTAS
        # ====================================================

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
                "**Faltas:** "
                "Datos no disponibles"
            )


        # ====================================================
        # TARJETAS
        # ====================================================

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
                "**Tarjetas amarillas:** "
                "Datos no disponibles"
            )


        # ====================================================
        # TIROS A PUERTA
        # ====================================================

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
                "**Tiros a puerta:** "
                "Datos no disponibles"
            )


        # ====================================================
        # FUERAS DE JUEGO
        # ====================================================

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
                "**Fueras de juego:** "
                "Datos no disponibles"
            )


    # ========================================================
    # ENFRENTAMIENTOS DIRECTOS
    # ========================================================

    st.divider()

    st.header(
        "🤝 Enfrentamientos directos"
    )


    h2h = datos.get(
        "h2h",
        []
    )


    print(
        "===================================="
    )

    print(
        "H2H RECIBIDOS POR APP:",
        len(h2h)
    )

    print(
        "===================================="
    )


    # ========================================================
    # H2H ENCONTRADOS
    # ========================================================

    if h2h:

        st.success(
            f"Se encontraron "
            f"{len(h2h)} enfrentamientos directos."
        )


        for i, partido in enumerate(
            h2h,
            start=1
        ):

            local_h2h = (
                partido
                .get("homeTeam", {})
                .get("name", "Desconocido")
            )


            visitante_h2h = (
                partido
                .get("awayTeam", {})
                .get("name", "Desconocido")
            )


            st.subheader(
                f"Enfrentamiento directo #{i}"
            )


            st.write(
                f"**{local_h2h} vs "
                f"{visitante_h2h}**"
            )


            mostrar_partido(
                partido
            )


            if i < len(h2h):

                st.divider()


    # ========================================================
    # SIN H2H
    # ========================================================

    else:

        st.warning(
            "No se encontraron enfrentamientos "
            "directos entre estos dos equipos "
            "en la liga seleccionada."
        )


    # ========================================================
    # EQUIPO A
    # ========================================================

    st.divider()

    st.header(
        f"⚽ {nombre_a}"
    )


    # ========================================================
    # LOCAL EQUIPO A
    # ========================================================

    st.subheader(
        "🏠 Último partido como LOCAL"
    )


    st.write(
        "Las estadísticas fueron las siguientes:"
    )


    mostrar_partido(
        datos.get(
            "local_a"
        )
    )


    # ========================================================
    # VISITANTE EQUIPO A
    # ========================================================

    st.subheader(
        "✈️ Último partido como VISITANTE"
    )


    st.write(
        "Las estadísticas fueron las siguientes:"
    )


    mostrar_partido(
        datos.get(
            "visitante_a"
        )
    )


    # ========================================================
    # EQUIPO B
    # ========================================================

    st.divider()

    st.header(
        f"⚽ {nombre_b}"
    )


    # ========================================================
    # LOCAL EQUIPO B
    # ========================================================

    st.subheader(
        "🏠 Último partido como LOCAL"
    )


    st.write(
        "Las estadísticas fueron las siguientes:"
    )


    mostrar_partido(
        datos.get(
            "local_b"
        )
    )


    # ========================================================
    # VISITANTE EQUIPO B
    # ========================================================

    st.subheader(
        "✈️ Último partido como VISITANTE"
    )


    st.write(
        "Las estadísticas fueron las siguientes:"
    )


    mostrar_partido(
        datos.get(
            "visitante_b"
        )
    )