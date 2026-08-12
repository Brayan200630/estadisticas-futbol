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
    # FECHA COMO STRING
    # ========================================================

    fecha_limite = fecha_partido.strftime(
        "%Y-%m-%d"
    )


    # ========================================================
    # BÚSQUEDA
    # ========================================================

    with st.spinner(
        "Buscando información en Sofascore..."
    ):

        print(
            "========================================"
        )

        print(
            "INICIO DE BÚSQUEDA"
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
            "Fecha límite:",
            fecha_limite
        )

        print(
            "========================================"
        )


        datos = analizar_partido(
            equipo_a.strip(),
            equipo_b.strip(),
            fecha_limite,
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


    st.info(
        f"Solo se mostrarán partidos anteriores al "
        f"{fecha_partido.strftime('%d/%m/%Y')}."
    )


    # ========================================================
    # FUNCIÓN PARA MOSTRAR PARTIDO
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

                fecha_evento = datetime.fromtimestamp(
                    timestamp
                )

                fecha_formateada = (
                    fecha_evento.strftime(
                        "%d/%m/%Y"
                    )
                )

            except Exception:

                fecha_evento = None

                fecha_formateada = (
                    "Fecha no disponible"
                )

        else:

            fecha_evento = None

            fecha_formateada = (
                "Fecha no disponible"
            )


        # ====================================================
        # LOCAL
        # ====================================================

        local = (
            evento
            .get("homeTeam", {})
            .get("name", "")
        )


        # ====================================================
        # VISITANTE
        # ====================================================

        visitante = (
            evento
            .get("awayTeam", {})
            .get("name", "")
        )


        # ====================================================
        # LIGA
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


        if torneo:

            st.write(
                f"**Liga:** {torneo}"
            )


        # ====================================================
        # FECHA
        # ====================================================

        st.write(
            f"**Fecha:** {fecha_formateada}"
        )


        # ====================================================
        # PARTIDO
        # ====================================================

        st.write(
            f"**Partido:** "
            f"{local} vs {visitante}"
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
        # POSESIÓN
        # ====================================================

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


        # ====================================================
        # CÓRNERS
        # ====================================================

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


        # ====================================================
        # TARJETAS
        # ====================================================

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


    h2h_original = datos.get(
        "h2h",
        []
    )


    # ========================================================
    # FILTRAR H2H POR FECHA
    # ========================================================

    h2h = []


    for evento in h2h_original:

        if not evento:
            continue


        timestamp = evento.get(
            "startTimestamp"
        )


        if not timestamp:
            continue


        try:

            fecha_evento = datetime.fromtimestamp(
                timestamp
            ).date()

        except Exception:

            continue


        # ====================================================
        # SOLO PARTIDOS ANTERIORES A LA FECHA DEL PARTIDO
        # ====================================================

        if fecha_evento >= fecha_partido:

            print(
                "H2H DESCARTADO POR FECHA:",
                fecha_evento,
                ">=",
                fecha_partido
            )

            continue


        # ====================================================
        # COMPROBAR QUE REALMENTE SEAN LOS DOS EQUIPOS
        # ====================================================

        home_id = (
            evento
            .get("homeTeam", {})
            .get("id")
        )


        away_id = (
            evento
            .get("awayTeam", {})
            .get("id")
        )


        id_a = datos.get(
            "equipo_a_id"
        )


        id_b = datos.get(
            "equipo_b_id"
        )


        # Si main.py entrega IDs, comprobarlos.
        if id_a and id_b:

            if {home_id, away_id} != {
                id_a,
                id_b
            }:

                continue


        h2h.append(
            evento
        )


    # ========================================================
    # ELIMINAR DUPLICADOS
    # ========================================================

    h2h_unicos = {}


    for evento in h2h:

        event_id = evento.get(
            "id"
        )

        if event_id:

            h2h_unicos[event_id] = evento


    h2h = list(
        h2h_unicos.values()
    )


    # ========================================================
    # ORDENAR DEL MÁS RECIENTE AL MÁS ANTIGUO
    # ========================================================

    h2h.sort(
        key=lambda evento:
        evento.get(
            "startTimestamp",
            0
        ),
        reverse=True
    )


    # ========================================================
    # SOLO LOS 2 MÁS RECIENTES
    # ========================================================

    h2h = h2h[:2]


    # ========================================================
    # MOSTRAR H2H
    # ========================================================

    if len(h2h) >= 1:

        st.subheader(
            "Último enfrentamiento"
        )

        mostrar_partido(
            h2h[0]
        )


    if len(h2h) >= 2:

        st.divider()

        st.subheader(
            "Enfrentamiento anterior"
        )

        mostrar_partido(
            h2h[1]
        )


    if len(h2h) == 0:

        st.warning(
            "No se encontró ningún enfrentamiento "
            "directo anterior a la fecha seleccionada."
        )


    # ========================================================
    # EQUIPO A
    # ========================================================

    st.divider()

    st.header(
        f"🏠 {nombre_a}"
    )


    # ========================================================
    # ÚLTIMO COMO LOCAL
    # ========================================================

    st.subheader(
        "Último partido como LOCAL"
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
    # ÚLTIMO COMO VISITANTE
    # ========================================================

    st.subheader(
        "Último partido como VISITANTE"
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
        f"✈️ {nombre_b}"
    )


    # ========================================================
    # ÚLTIMO COMO LOCAL
    # ========================================================

    st.subheader(
        "Último partido como LOCAL"
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
    # ÚLTIMO COMO VISITANTE
    # ========================================================

    st.subheader(
        "Último partido como VISITANTE"
    )


    st.write(
        "Las estadísticas fueron las siguientes:"
    )


    mostrar_partido(
        datos.get(
            "visitante_b"
        )
    )