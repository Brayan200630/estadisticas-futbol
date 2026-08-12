import streamlit as st
from datetime import date, datetime
from curl_cffi import requests
from urllib.parse import quote
import streamlit.components.v1 as components

from main import analizar_partido, obtener_estadisticas


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Estadísticas de Fútbol",
    page_icon="⚽",
    layout="centered"
)

BASE_URL = "https://www.sofascore.com/api/v1"


# ============================================================
# SESIÓN SOFASCORE
# ============================================================

session = requests.Session()


# ============================================================
# PETICIÓN A SOFASCORE
# ============================================================

@st.cache_data(ttl=3600)
def obtener_json_app(url):

    try:

        respuesta = session.get(
            url,
            impersonate="chrome",
            timeout=20
        )

        if respuesta.status_code != 200:
            return None

        return respuesta.json()

    except Exception:

        return None


# ============================================================
# BUSCAR EQUIPOS
# ============================================================

@st.cache_data(ttl=3600)
def buscar_equipos_app(nombre):

    if not nombre:
        return []

    url = (
        f"{BASE_URL}/search/all"
        f"?q={quote(nombre)}"
    )

    datos = obtener_json_app(url)

    if not datos:
        return []

    resultados = datos.get(
        "results",
        []
    )

    equipos = []

    for resultado in resultados:

        if resultado.get("type") != "team":
            continue

        entidad = resultado.get(
            "entity",
            {}
        )

        if not entidad:
            continue

        equipo_id = entidad.get("id")
        nombre_equipo = entidad.get("name")

        if not equipo_id or not nombre_equipo:
            continue

        pais = ""

        country = entidad.get(
            "country",
            {}
        )

        if isinstance(country, dict):

            pais = country.get(
                "name",
                ""
            )

        equipos.append(
            {
                "id": equipo_id,
                "name": nombre_equipo,
                "country": pais
            }
        )

    # ========================================================
    # ELIMINAR DUPLICADOS
    # ========================================================

    unicos = {}

    for equipo in equipos:

        if equipo["id"]:

            unicos[
                equipo["id"]
            ] = equipo

    return list(
        unicos.values()
    )


# ============================================================
# BUSCAR TORNEOS / LIGAS
# ============================================================

@st.cache_data(ttl=3600)
def buscar_ligas_app(nombre):

    if not nombre:
        return []

    url = (
        f"{BASE_URL}/search/all"
        f"?q={quote(nombre)}"
    )

    datos = obtener_json_app(url)

    if not datos:
        return []

    resultados = datos.get(
        "results",
        []
    )

    ligas = []

    for resultado in resultados:

        tipo = resultado.get(
            "type"
        )

        if tipo not in {
            "uniqueTournament",
            "tournament"
        }:
            continue

        entidad = resultado.get(
            "entity",
            {}
        )

        if not entidad:
            continue

        tournament_id = entidad.get(
            "id"
        )

        nombre_liga = entidad.get(
            "name"
        )

        # ----------------------------------------------------
        # Algunos resultados pueden tener uniqueTournament
        # dentro de entity.
        # ----------------------------------------------------

        if not tournament_id:

            unique = entidad.get(
                "uniqueTournament",
                {}
            )

            if isinstance(
                unique,
                dict
            ):

                tournament_id = unique.get(
                    "id"
                )

                if not nombre_liga:

                    nombre_liga = unique.get(
                        "name"
                    )

        if not tournament_id or not nombre_liga:
            continue

        pais = ""

        category = entidad.get(
            "category",
            {}
        )

        if isinstance(category, dict):

            pais = category.get(
                "name",
                ""
            )

        item = {
            "id": tournament_id,
            "name": nombre_liga,
            "country": pais
        }

        existe = False

        for liga in ligas:

            if liga["id"] == tournament_id:

                existe = True
                break

        if not existe:

            ligas.append(
                item
            )

    return ligas


# ============================================================
# TÍTULO
# ============================================================

st.title("⚽ Estadísticas de Fútbol")

st.write(
    "Consulta estadísticas de los últimos partidos "
    "relevantes de dos equipos."
)


# ============================================================
# EQUIPO A
# ============================================================

st.subheader("Equipo A")

busqueda_a = st.text_input(
    "Buscar Equipo A",
    placeholder="Escribe el nombre del equipo...",
    key="busqueda_equipo_a"
)

equipos_a = buscar_equipos_app(
    busqueda_a.strip()
)

opciones_a = [
    f'{equipo["name"]}'
    + (
        f' ({equipo["country"]})'
        if equipo["country"]
        else ""
    )
    for equipo in equipos_a
]

if opciones_a:

    seleccion_a = st.selectbox(
        "Selecciona Equipo A",
        opciones_a,
        key="seleccion_equipo_a"
    )

    indice_a = opciones_a.index(
        seleccion_a
    )

    equipo_a = equipos_a[
        indice_a
    ]["name"]

else:

    equipo_a = ""


# ============================================================
# EQUIPO B
# ============================================================

st.subheader("Equipo B")

busqueda_b = st.text_input(
    "Buscar Equipo B",
    placeholder="Escribe el nombre del equipo...",
    key="busqueda_equipo_b"
)

equipos_b = buscar_equipos_app(
    busqueda_b.strip()
)

opciones_b = [
    f'{equipo["name"]}'
    + (
        f' ({equipo["country"]})'
        if equipo["country"]
        else ""
    )
    for equipo in equipos_b
]

if opciones_b:

    seleccion_b = st.selectbox(
        "Selecciona Equipo B",
        opciones_b,
        key="seleccion_equipo_b"
    )

    indice_b = opciones_b.index(
        seleccion_b
    )

    equipo_b = equipos_b[
        indice_b
    ]["name"]

else:

    equipo_b = ""


# ============================================================
# COMPETICIÓN
# ============================================================

st.subheader("Competición")

modo_competicion = st.radio(
    "¿Cómo quieres buscar los partidos?",
    [
        "Competición específica",
        "Todas las competiciones"
    ],
    horizontal=True
)


# ============================================================
# LIGA / COPA ESPECÍFICA
# ============================================================

if modo_competicion == "Competición específica":

    busqueda_liga = st.text_input(
        "Buscar Liga / Copa",
        placeholder=(
            "Ejemplo: Liga 1, Libertadores, "
            "Champions League..."
        ),
        key="busqueda_liga"
    )

    ligas = buscar_ligas_app(
        busqueda_liga.strip()
    )

    opciones_ligas = [
        f'{liga_item["name"]}'
        + (
            f' ({liga_item["country"]})'
            if liga_item["country"]
            else ""
        )
        for liga_item in ligas
    ]

    if opciones_ligas:

        seleccion_liga = st.selectbox(
            "Selecciona Liga / Copa",
            opciones_ligas,
            key="seleccion_liga"
        )

        indice_liga = opciones_ligas.index(
            seleccion_liga
        )

        liga = ligas[
            indice_liga
        ]["name"]

    else:

        liga = ""

else:

    # IMPORTANTE:
    # Cadena vacía = todas las competiciones
    # según el main.py actual.

    liga = ""

    st.info(
        "🌎 Se buscarán los últimos partidos "
        "sin importar si fueron de liga, copa, "
        "competición internacional u otro torneo."
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
# FUNCIÓN PARA OBTENER RESULTADO
# ============================================================

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

    # ========================================================
    # RESULTADO ACTUAL
    # ========================================================

    home_current = home_score.get(
        "current"
    )

    away_current = away_score.get(
        "current"
    )

    # ========================================================
    # PENALES
    # ========================================================

    home_penalty = home_score.get(
        "penalties"
    )

    away_penalty = away_score.get(
        "penalties"
    )

    # ========================================================
    # PARTIDO DECIDIDO POR PENALES
    # ========================================================

    if (
        home_penalty is not None
        and
        away_penalty is not None
    ):

        home_regular = home_score.get(
            "normaltime"
        )

        away_regular = away_score.get(
            "normaltime"
        )

        if (
            home_regular is None
            or
            away_regular is None
        ):

            home_regular = home_score.get(
                "overtime"
            )

            away_regular = away_score.get(
                "overtime"
            )

        if (
            home_regular is None
            or
            away_regular is None
        ):

            home_regular = home_score.get(
                "period1"
            )

            away_regular = away_score.get(
                "period1"
            )

        if (
            home_regular is None
            or
            away_regular is None
        ):

            home_regular = home_current
            away_regular = away_current

        if (
            home_regular is not None
            and
            away_regular is not None
        ):

            return (
                f"{home_regular} "
                f"({home_penalty}) - "
                f"{away_regular} "
                f"({away_penalty})"
            )

    # ========================================================
    # RESULTADO NORMAL
    # ========================================================

    if (
        home_current is not None
        and
        away_current is not None
    ):

        return (
            f"{home_current} - "
            f"{away_current}"
        )

    return None


# ============================================================
# FUNCIÓN PARA GENERAR TEXTO DE UN PARTIDO
# ============================================================

def texto_partido(evento):

    if not evento:
        return "No se encontró un partido válido."

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

    fecha_formateada = formatear_fecha(
        evento
    )

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

    resultado = obtener_resultado(
        evento
    )

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

    texto = []

    if torneo:

        texto.append(
            f"Liga: {torneo}"
        )

    texto.append(
        f"Fecha: {fecha_formateada}"
    )

    texto.append(
        f"Partido: {local} vs {visitante}"
    )

    if resultado:

        texto.append(
            f"Resultado: {resultado}"
        )

    if posesion:

        texto.append(
            f"Posesión: "
            f"{local} {posesion[0]} - "
            f"{posesion[1]} {visitante}"
        )

    else:

        texto.append(
            "Posesión: Datos no disponibles"
        )

    if corners:

        texto.append(
            f"Saques de esquina: "
            f"{local} {corners[0]} - "
            f"{corners[1]} {visitante}"
        )

    else:

        texto.append(
            "Saques de esquina: Datos no disponibles"
        )

    if faltas:

        texto.append(
            f"Faltas: "
            f"{local} {faltas[0]} - "
            f"{faltas[1]} {visitante}"
        )

    else:

        texto.append(
            "Faltas: Datos no disponibles"
        )

    if tarjetas:

        texto.append(
            f"Tarjetas amarillas: "
            f"{local} {tarjetas[0]} - "
            f"{tarjetas[1]} {visitante}"
        )

    else:

        texto.append(
            "Tarjetas amarillas: Datos no disponibles"
        )

    if tiros:

        texto.append(
            f"Tiros a puerta: "
            f"{local} {tiros[0]} - "
            f"{tiros[1]} {visitante}"
        )

    else:

        texto.append(
            "Tiros a puerta: Datos no disponibles"
        )

    if fueras:

        texto.append(
            f"Fueras de juego: "
            f"{local} {fueras[0]} - "
            f"{fueras[1]} {visitante}"
        )

    else:

        texto.append(
            "Fueras de juego: Datos no disponibles"
        )

    return "\n".join(
        texto
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

    fecha_formateada = formatear_fecha(
        evento
    )

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

    st.write(
        f"**Fecha:** {fecha_formateada}"
    )

    st.write(
        f"**Partido:** "
        f"{local} vs {visitante}"
    )

    resultado = obtener_resultado(
        evento
    )

    if resultado:

        st.write(
            f"**Resultado:** {resultado}"
        )

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
            "Selecciona o escribe el Equipo A."
        )

        st.stop()

    if not equipo_b.strip():

        st.error(
            "Selecciona o escribe el Equipo B."
        )

        st.stop()

    if (
        modo_competicion
        ==
        "Competición específica"
        and
        not liga.strip()
    ):

        st.error(
            "Selecciona o escribe la liga/copa."
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
            "La fecha del partido debe ser "
            "posterior al 01/01/2020."
        )

        st.stop()

    st.info(
        f"📅 Buscando partidos desde "
        f"**{fecha_inicio.strftime('%d/%m/%Y')}** "
        f"hasta antes del "
        f"**{fecha_fin.strftime('%d/%m/%Y')}**."
    )

    # ========================================================
    # INFORMACIÓN DE COMPETICIÓN
    # ========================================================

    if modo_competicion == "Todas las competiciones":

        st.info(
            "🌎 Modo: **todas las competiciones**. "
            "No se filtrarán los partidos por liga o copa."
        )

    else:

        st.info(
            f"🏆 Competición seleccionada: "
            f"**{liga}**"
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
    # NOMBRES ENCONTRADOS
    # ========================================================

    nombre_a = datos.get(
        "equipo_a",
        equipo_a
    )

    nombre_b = datos.get(
        "equipo_b",
        equipo_b
    )

    st.success(
        f"Equipos encontrados: "
        f"{nombre_a} vs {nombre_b}"
    )

    if (
        modo_competicion
        ==
        "Todas las competiciones"
    ):

        st.info(
            "Liga: **Todas las competiciones**"
        )

    else:

        st.info(
            f"Liga seleccionada: **{liga}**"
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
            f"de {nombre_a} como local "
            "dentro del período seleccionado."
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
            f"de {nombre_a} como visitante "
            "dentro del período seleccionado."
        )

    # ========================================================
    # EQUIPO A
    # ========================================================

    st.divider()

    st.header(
        f"⚽ {nombre_a}"
    )

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

    # ========================================================
    # TEXTO COMPLETO PARA COPIAR
    # ========================================================

    texto_completo = []

    texto_completo.append(
        f"⚽ {nombre_a} vs {nombre_b}"
    )

    texto_completo.append("")

    if modo_competicion == "Todas las competiciones":

        texto_completo.append(
            "Competición: Todas las competiciones"
        )

    else:

        texto_completo.append(
            f"Competición: {liga}"
        )

    texto_completo.append(
        f"Fecha de referencia: "
        f"{fecha_partido.strftime('%d/%m/%Y')}"
    )

    texto_completo.append("")

    # ========================================================
    # H2H
    # ========================================================

    texto_completo.append(
        "🔁 ENFRENTAMIENTOS DIRECTOS"
    )

    texto_completo.append("")

    texto_completo.append(
        f"🏠 Último enfrentamiento con "
        f"{nombre_a} como LOCAL"
    )

    texto_completo.append("")

    if h2h_a_local:

        texto_completo.append(
            texto_partido(
                h2h_a_local
            )
        )

    else:

        texto_completo.append(
            "No se encontró un enfrentamiento."
        )

    texto_completo.append("")

    texto_completo.append(
        f"✈️ Último enfrentamiento con "
        f"{nombre_a} como VISITANTE"
    )

    texto_completo.append("")

    if h2h_a_visitante:

        texto_completo.append(
            texto_partido(
                h2h_a_visitante
            )
        )

    else:

        texto_completo.append(
            "No se encontró un enfrentamiento."
        )

    texto_completo.append("")

    # ========================================================
    # EQUIPO A
    # ========================================================

    texto_completo.append(
        f"⚽ {nombre_a}"
    )

    texto_completo.append("")

    texto_completo.append(
        "🏠 Último partido como LOCAL"
    )

    texto_completo.append("")

    if local_a:

        texto_completo.append(
            texto_partido(
                local_a
            )
        )

    else:

        texto_completo.append(
            "No se encontró un partido válido."
        )

    texto_completo.append("")

    texto_completo.append(
        "✈️ Último partido como VISITANTE"
    )

    texto_completo.append("")

    if visitante_a:

        texto_completo.append(
            texto_partido(
                visitante_a
            )
        )

    else:

        texto_completo.append(
            "No se encontró un partido válido."
        )

    texto_completo.append("")

    # ========================================================
    # EQUIPO B
    # ========================================================

    texto_completo.append(
        f"⚽ {nombre_b}"
    )

    texto_completo.append("")

    texto_completo.append(
        "🏠 Último partido como LOCAL"
    )

    texto_completo.append("")

    if local_b:

        texto_completo.append(
            texto_partido(
                local_b
            )
        )

    else:

        texto_completo.append(
            "No se encontró un partido válido."
        )

    texto_completo.append("")

    texto_completo.append(
        "✈️ Último partido como VISITANTE"
    )

    texto_completo.append("")

    if visitante_b:

        texto_completo.append(
            texto_partido(
                visitante_b
            )
        )

    else:

        texto_completo.append(
            "No se encontró un partido válido."
        )

    texto_final = "\n".join(
        texto_completo
    )

    # ========================================================
    # COPIAR RESULTADOS
    # ========================================================

    st.divider()

    st.header(
        "📋 Texto para copiar"
    )

    st.write(
        "Puedes copiar todo el análisis con el botón de abajo."
    )

    texto_html = (
        texto_final
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

    components.html(
        f"""
        <div style="
            width: 100%;
            font-family: Arial, sans-serif;
        ">

            <button
                onclick="copiarTexto()"
                style="
                    width: 100%;
                    padding: 12px;
                    background-color: #ff4b4b;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: bold;
                    cursor: pointer;
                "
            >
                📋 Copiar resultados
            </button>

            <div
                id="mensaje"
                style="
                    text-align: center;
                    margin-top: 8px;
                    font-size: 14px;
                    color: #16a34a;
                    font-weight: bold;
                "
            ></div>

        </div>

        <script>

        const texto = `{texto_html}`;

        function copiarTexto() {{

            navigator.clipboard.writeText(texto)
            .then(function() {{

                document.getElementById(
                    "mensaje"
                ).innerText =
                    "✅ Resultados copiados";

            }})
            .catch(function() {{

                const area =
                    document.createElement("textarea");

                area.value = texto;

                document.body.appendChild(area);

                area.select();

                document.execCommand(
                    "copy"
                );

                document.body.removeChild(area);

                document.getElementById(
                    "mensaje"
                ).innerText =
                    "✅ Resultados copiados";

            }});

        }}

        </script>
        """,
        height=75
    )

    # ========================================================
    # VISTA DEL TEXTO
    # ========================================================

    with st.expander(
        "👁️ Ver texto completo"
    ):

        st.code(
            texto_final,
            language=None
        )