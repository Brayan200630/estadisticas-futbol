import streamlit as st
from datetime import date, datetime
from curl_cffi import requests
from urllib.parse import quote
import streamlit.components.v1 as components

from main import (
    analizar_partido,
    obtener_estadisticas,
    buscar_equipo
)

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

        if isinstance(
            category,
            dict
        ):

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

st.title(
    "⚽ Estadísticas de Fútbol"
)

st.write(
    "Consulta estadísticas de los últimos partidos "
    "relevantes de dos equipos."
)


# ============================================================
# EQUIPO A
# ============================================================

st.subheader(
    "Equipo A"
)

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

st.subheader(
    "Equipo B"
)

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

st.subheader(
    "Competición"
)

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

    liga = "TODAS"

    st.info(
        "🌎 Se buscarán los últimos partidos "
        "sin importar si fueron de liga, copa, "
        "competición internacional u otro torneo."
    )


# ============================================================
# FECHA
# ============================================================

fecha_partido = st.date_input(
    "Fecha límite del partido",
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
# FUNCIÓN PARA FORMATEAR FECHA Y HORA
# ============================================================

def formatear_fecha_hora(evento):

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
            "%d/%m/%Y %H:%M"
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
# OBTENER NOMBRE DEL ENTRENADOR
# ============================================================

@st.cache_data(ttl=3600)
def obtener_entrenador_equipo(team_id):

    if not team_id:
        return None

    endpoints = [

        f"{BASE_URL}/team/{team_id}/manager",

        f"{BASE_URL}/team/{team_id}/managers"

    ]

    for url in endpoints:

        datos = obtener_json_app(
            url
        )

        if not datos:
            continue

        manager = datos.get(
            "manager"
        )

        if isinstance(
            manager,
            dict
        ):

            nombre = manager.get(
                "name"
            )

            if nombre:
                return nombre

        managers = datos.get(
            "managers"
        )

        if isinstance(
            managers,
            list
        ) and managers:

            ultimo = managers[-1]

            if isinstance(
                ultimo,
                dict
            ):

                nombre = ultimo.get(
                    "name"
                )

                if nombre:
                    return nombre

    return None


# ============================================================
# OBTENER PRÓXIMOS PARTIDOS DEL EQUIPO
# ============================================================

@st.cache_data(ttl=900)
def obtener_proximos_partidos(team_id):

    if not team_id:
        return []

    partidos = []

    for pagina in range(5):

        url = (
            f"{BASE_URL}/team/"
            f"{team_id}/events/next/"
            f"{pagina}"
        )

        datos = obtener_json_app(
            url
        )

        if not datos:
            break

        eventos = datos.get(
            "events",
            []
        )

        if not eventos:
            break

        partidos.extend(
            eventos
        )

        if not datos.get(
            "hasNextPage",
            False
        ):

            break

    # ========================================================
    # ELIMINAR DUPLICADOS
    # ========================================================

    unicos = {}

    for evento in partidos:

        event_id = evento.get(
            "id"
        )

        if event_id:

            unicos[
                event_id
            ] = evento

    partidos = list(
        unicos.values()
    )

    # ========================================================
    # ORDENAR
    # ========================================================

    partidos.sort(
        key=lambda evento:
        evento.get(
            "startTimestamp",
            0
        )
    )

    return partidos


# ============================================================
# OBTENER PRÓXIMO PARTIDO ENTRE DOS EQUIPOS
# ============================================================

def obtener_proximo_h2h(
    equipo_a_id,
    equipo_b_id
):

    proximos_a = obtener_proximos_partidos(
        equipo_a_id
    )

    proximos_b = obtener_proximos_partidos(
        equipo_b_id
    )

    todos = []

    todos.extend(
        proximos_a
    )

    todos.extend(
        proximos_b
    )

    unicos = {}

    for evento in todos:

        if not evento:
            continue

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

        if not home_id or not away_id:
            continue

        if {
            home_id,
            away_id
        } != {
            equipo_a_id,
            equipo_b_id
        }:

            continue

        event_id = evento.get(
            "id"
        )

        if event_id:

            unicos[
                event_id
            ] = evento

    partidos = list(
        unicos.values()
    )

    partidos.sort(
        key=lambda evento:
        evento.get(
            "startTimestamp",
            0
        )
    )

    if partidos:
        return partidos[0]

    return None


# ============================================================
# OBTENER ALINEACIONES
# ============================================================

@st.cache_data(ttl=900)
def obtener_alineaciones(evento):

    if not evento:
        return None

    event_id = evento.get(
        "id"
    )

    if not event_id:
        return None

    url = (
        f"{BASE_URL}/event/"
        f"{event_id}/lineups"
    )

    datos = obtener_json_app(
        url
    )

    if not datos:
        return None

    return datos


# ============================================================
# OBTENER INCIDENTES
# ============================================================

@st.cache_data(ttl=900)
def obtener_incidentes(evento):

    if not evento:
        return []

    event_id = evento.get(
        "id"
    )

    if not event_id:
        return []

    url = (
        f"{BASE_URL}/event/"
        f"{event_id}/incidents"
    )

    datos = obtener_json_app(
        url
    )

    if not datos:
        return []

    return datos.get(
        "incidents",
        []
    )


# ============================================================
# OBTENER NOMBRE DE JUGADOR
# ============================================================

def obtener_nombre_jugador(player):

    if not isinstance(
        player,
        dict
    ):

        return "Jugador desconocido"

    return (
        player.get("name")
        or
        player.get("shortName")
        or
        "Jugador desconocido"
    )


# ============================================================
# OBTENER ALINEACIÓN DE UN EQUIPO
# ============================================================

def extraer_alineacion_equipo(
    alineaciones,
    side
):

    if not alineaciones:
        return None

    bloque = alineaciones.get(
        side
    )

    if not isinstance(
        bloque,
        dict
    ):

        return None

    titulares = []
    suplentes = []

    jugadores = bloque.get(
        "players",
        []
    )

    if not isinstance(
        jugadores,
        list
    ):

        jugadores = []

    for item in jugadores:

        if not isinstance(
            item,
            dict
        ):

            continue

        player = item.get(
            "player",
            {}
        )

        if not isinstance(
            player,
            dict
        ):

            player = {}

        nombre = obtener_nombre_jugador(
            player
        )

        posicion = (
            item.get(
                "position"
            )
            or
            ""
        )

        titular = item.get(
            "substitute"
        )

        numero = (
            player.get(
                "jerseyNumber"
            )
            or
            item.get(
                "jerseyNumber"
            )
        )

        texto = nombre

        if numero is not None:

            texto = (
                f"#{numero} "
                f"{texto}"
            )

        if posicion:

            texto += (
                f" ({posicion})"
            )

        if titular is True:

            suplentes.append(
                texto
            )

        else:

            titulares.append(
                texto
            )

    formacion = (
        bloque.get(
            "formation"
        )
    )

    return {

        "titulares":
            titulares,

        "suplentes":
            suplentes,

        "formacion":
            formacion

    }


# ============================================================
# OBTENER CAMBIOS
# ============================================================

def obtener_cambios(
    evento,
    equipo_id
):

    incidentes = obtener_incidentes(
        evento
    )

    cambios = []

    for incidente in incidentes:

        if not isinstance(
            incidente,
            dict
        ):

            continue

        if incidente.get(
            "incidentType"
        ) != "substitution":

            continue

        if incidente.get(
            "isHome"
        ) is True:

            lado = "home"

        else:

            lado = "away"

        home_id = (
            evento
            .get("homeTeam", {})
            .get("id")
        )

        if (
            lado == "home"
            and
            home_id != equipo_id
        ):

            continue

        if (
            lado == "away"
            and
            home_id == equipo_id
        ):

            continue

        jugador_entro = (
            incidente
            .get("playerIn", {})
        )

        jugador_salio = (
            incidente
            .get("playerOut", {})
        )

        if not isinstance(
            jugador_entro,
            dict
        ):

            jugador_entro = {}

        if not isinstance(
            jugador_salio,
            dict
        ):

            jugador_salio = {}

        minuto = (
            incidente.get(
                "time"
            )
            or
            incidente.get(
                "incidentTime"
            )
            or
            "?"
        )

        cambios.append(
            {
                "minuto":
                    minuto,

                "entro":
                    obtener_nombre_jugador(
                        jugador_entro
                    ),

                "salio":
                    obtener_nombre_jugador(
                        jugador_salio
                    )
            }
        )

    return cambios


# ============================================================
# OBTENER GOLES
# ============================================================

def obtener_goles(evento):

    incidentes = obtener_incidentes(
        evento
    )

    goles = []

    for incidente in incidentes:

        if not isinstance(
            incidente,
            dict
        ):

            continue

        tipo = incidente.get(
            "incidentType"
        )

        if tipo != "goal":
            continue

        jugador = incidente.get(
            "player",
            {}
        )

        if not isinstance(
            jugador,
            dict
        ):

            jugador = {}

        nombre = obtener_nombre_jugador(
            jugador
        )

        minuto = (
            incidente.get(
                "time"
            )
            or
            incidente.get(
                "incidentTime"
            )
            or
            "?"
        )

        is_home = incidente.get(
            "isHome"
        )

        if is_home is True:

            equipo = (
                evento
                .get("homeTeam", {})
                .get("name", "")
            )

        else:

            equipo = (
                evento
                .get("awayTeam", {})
                .get("name", "")
            )

        tipo_gol = (
            incidente.get(
                "incidentClass"
            )
            or
            ""
        )

        goles.append(
            {
                "minuto":
                    minuto,

                "jugador":
                    nombre,

                "equipo":
                    equipo,

                "tipo":
                    tipo_gol
            }
        )

    goles.sort(
        key=lambda x:
        str(x["minuto"])
    )

    return goles


# ============================================================
# MOSTRAR ALINEACIÓN
# ============================================================

def mostrar_alineacion(
    evento
):

    alineaciones = obtener_alineaciones(
        evento
    )

    if not alineaciones:
        return

    home = (
        evento
        .get("homeTeam", {})
    )

    away = (
        evento
        .get("awayTeam", {})
    )

    nombre_home = home.get(
        "name",
        "Local"
    )

    nombre_away = away.get(
        "name",
        "Visitante"
    )

    alineacion_home = (
        extraer_alineacion_equipo(
            alineaciones,
            "home"
        )
    )

    alineacion_away = (
        extraer_alineacion_equipo(
            alineaciones,
            "away"
        )
    )

    if not alineacion_home and not alineacion_away:
        return

    st.write(
        "### 👥 Alineaciones"
    )

    if alineacion_home:

        st.write(
            f"**{nombre_home}**"
        )

        if alineacion_home.get(
            "formacion"
        ):

            st.write(
                f"Formación: "
                f"{alineacion_home['formacion']}"
            )

        if alineacion_home.get(
            "titulares"
        ):

            st.write(
                "**Titulares:** "
                +
                ", ".join(
                    alineacion_home[
                        "titulares"
                    ]
                )
            )

        if alineacion_home.get(
            "suplentes"
        ):

            st.write(
                "**Suplentes:** "
                +
                ", ".join(
                    alineacion_home[
                        "suplentes"
                    ]
                )
            )

    if alineacion_away:

        st.write(
            f"**{nombre_away}**"
        )

        if alineacion_away.get(
            "formacion"
        ):

            st.write(
                f"Formación: "
                f"{alineacion_away['formacion']}"
            )

        if alineacion_away.get(
            "titulares"
        ):

            st.write(
                "**Titulares:** "
                +
                ", ".join(
                    alineacion_away[
                        "titulares"
                    ]
                )
            )

        if alineacion_away.get(
            "suplentes"
        ):

            st.write(
                "**Suplentes:** "
                +
                ", ".join(
                    alineacion_away[
                        "suplentes"
                    ]
                )
            )


# ============================================================
# MOSTRAR GOLES
# ============================================================

def mostrar_goles(
    evento
):

    goles = obtener_goles(
        evento
    )

    if not goles:
        return

    st.write(
        "### ⚽ Goles"
    )

    for gol in goles:

        texto = (
            f"**{gol['minuto']}'** — "
            f"{gol['jugador']} "
            f"({gol['equipo']})"
        )

        if gol.get(
            "tipo"
        ):

            texto += (
                f" — {gol['tipo']}"
            )

        st.write(
            texto
        )


# ============================================================
# MOSTRAR CAMBIOS
# ============================================================

def mostrar_cambios(
    evento
):

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

    cambios_home = obtener_cambios(
        evento,
        home_id
    )

    cambios_away = obtener_cambios(
        evento,
        away_id
    )

    if not cambios_home and not cambios_away:
        return

    st.write(
        "### 🔄 Cambios"
    )

    nombre_home = (
        evento
        .get("homeTeam", {})
        .get("name")
    )

    nombre_away = (
        evento
        .get("awayTeam", {})
        .get("name")
    )

    for cambio in cambios_home:

        st.write(
            f"**{nombre_home}** — "
            f"{cambio['minuto']}' "
            f"entró {cambio['entro']} "
            f"por {cambio['salio']}"
        )

    for cambio in cambios_away:

        st.write(
            f"**{nombre_away}** — "
            f"{cambio['minuto']}' "
            f"entró {cambio['entro']} "
            f"por {cambio['salio']}"
        )


# ============================================================
# MOSTRAR PRÓXIMO PARTIDO
# ============================================================

def mostrar_proximo_partido(
    evento,
    titulo
):

    if not evento:
        return

    st.subheader(
        titulo
    )

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

    st.write(
        f"**📅 Fecha y hora:** "
        f"{formatear_fecha_hora(evento)}"
    )

    st.write(
        f"**⚽ Partido:** "
        f"{local} vs {visitante}"
    )

    if torneo:

        st.write(
            f"**🏆 Competición:** "
            f"{torneo}"
        )

    # ========================================================
    # ENTRENADORES
    # ========================================================

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

    entrenador_home = (
        obtener_entrenador_equipo(
            home_id
        )
    )

    entrenador_away = (
        obtener_entrenador_equipo(
            away_id
        )
    )

    if entrenador_home:

        st.write(
            f"**👔 Entrenador {local}:** "
            f"{entrenador_home}"
        )

    if entrenador_away:

        st.write(
            f"**👔 Entrenador {visitante}:** "
            f"{entrenador_away}"
        )

    # ========================================================
    # ALINEACIONES
    # ========================================================

    mostrar_alineacion(
        evento
    )


# ============================================================
# FUNCIÓN PARA MOSTRAR PARTIDO TERMINADO
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

    st.write(
        f"**Fecha:** {fecha_formateada}"
    )

    st.write(
        f"**Partido:** "
        f"{local} vs {visitante}"
    )

    # ========================================================
    # RESULTADO
    # ========================================================

    resultado = obtener_resultado(
        evento
    )

    if resultado:

        st.write(
            f"**Resultado:** {resultado}"
        )

    # ========================================================
    # GOLES
    # ========================================================

    mostrar_goles(
        evento
    )

    # ========================================================
    # ALINEACIONES
    # ========================================================

    mostrar_alineacion(
        evento
    )

    # ========================================================
    # CAMBIOS
    # ========================================================

    mostrar_cambios(
        evento
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
# TEXTO COPIABLE
# ============================================================

def generar_texto_copiable(
    datos,
    nombre_a,
    nombre_b,
    liga
):

    lineas = []

    lineas.append(
        f"Equipos: {nombre_a} vs {nombre_b}"
    )

    lineas.append(
        f"Liga: {liga}"
    )

    lineas.append("")

    # ========================================================
    # FUNCIÓN INTERNA PARTIDO
    # ========================================================

    def texto_partido(
        titulo,
        evento
    ):

        resultado = []

        resultado.append(
            titulo
        )

        if not evento:

            resultado.append(
                "No se encontró un partido válido."
            )

            resultado.append("")

            return resultado

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

        fecha = formatear_fecha(
            evento
        )

        marcador = obtener_resultado(
            evento
        )

        resultado.append(
            f"Fecha: {fecha}"
        )

        resultado.append(
            f"Partido: "
            f"{local} vs {visitante}"
        )

        if torneo:

            resultado.append(
                f"Liga: {torneo}"
            )

        if marcador:

            resultado.append(
                f"Resultado: {marcador}"
            )

        # ====================================================
        # GOLES
        # ====================================================

        goles = obtener_goles(
            evento
        )

        if goles:

            resultado.append(
                "Goles:"
            )

            for gol in goles:

                linea = (
                    f"- {gol['minuto']}' "
                    f"{gol['jugador']} "
                    f"({gol['equipo']})"
                )

                if gol.get(
                    "tipo"
                ):

                    linea += (
                        f" — {gol['tipo']}"
                    )

                resultado.append(
                    linea
                )

        # ====================================================
        # ALINEACIONES
        # ====================================================

        alineaciones = obtener_alineaciones(
            evento
        )

        if alineaciones:

            resultado.append(
                "Alineaciones:"
            )

            for side, nombre_equipo in [
                (
                    "home",
                    local
                ),
                (
                    "away",
                    visitante
                )
            ]:

                alineacion = (
                    extraer_alineacion_equipo(
                        alineaciones,
                        side
                    )
                )

                if not alineacion:
                    continue

                resultado.append(
                    f"{nombre_equipo}:"
                )

                formacion = alineacion.get(
                    "formacion"
                )

                if formacion:

                    resultado.append(
                        f"- Formación: "
                        f"{formacion}"
                    )

                titulares = alineacion.get(
                    "titulares",
                    []
                )

                suplentes = alineacion.get(
                    "suplentes",
                    []
                )

                if titulares:

                    resultado.append(
                        "- Titulares: "
                        +
                        ", ".join(
                            titulares
                        )
                    )

                if suplentes:

                    resultado.append(
                        "- Suplentes: "
                        +
                        ", ".join(
                            suplentes
                        )
                    )

        # ====================================================
        # CAMBIOS
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

        cambios_home = obtener_cambios(
            evento,
            home_id
        )

        cambios_away = obtener_cambios(
            evento,
            away_id
        )

        if cambios_home or cambios_away:

            resultado.append(
                "Cambios:"
            )

            for cambio in cambios_home:

                resultado.append(
                    f"- {local}: "
                    f"{cambio['minuto']}' "
                    f"entró {cambio['entro']} "
                    f"por {cambio['salio']}"
                )

            for cambio in cambios_away:

                resultado.append(
                    f"- {visitante}: "
                    f"{cambio['minuto']}' "
                    f"entró {cambio['entro']} "
                    f"por {cambio['salio']}"
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

            resultado.append(
                f"Posesión: "
                f"{local} {posesion[0]} - "
                f"{posesion[1]} {visitante}"
            )

        else:

            resultado.append(
                "Posesión: Datos no disponibles"
            )

        if corners:

            resultado.append(
                f"Saques de esquina: "
                f"{local} {corners[0]} - "
                f"{corners[1]} {visitante}"
            )

        else:

            resultado.append(
                "Saques de esquina: "
                "Datos no disponibles"
            )

        if faltas:

            resultado.append(
                f"Faltas: "
                f"{local} {faltas[0]} - "
                f"{faltas[1]} {visitante}"
            )

        else:

            resultado.append(
                "Faltas: Datos no disponibles"
            )

        if tarjetas:

            resultado.append(
                f"Tarjetas amarillas: "
                f"{local} {tarjetas[0]} - "
                f"{tarjetas[1]} {visitante}"
            )

        else:

            resultado.append(
                "Tarjetas amarillas: "
                "Datos no disponibles"
            )

        if tiros:

            resultado.append(
                f"Tiros a puerta: "
                f"{local} {tiros[0]} - "
                f"{tiros[1]} {visitante}"
            )

        else:

            resultado.append(
                "Tiros a puerta: Datos no disponibles"
            )

        if fueras:

            resultado.append(
                f"Fueras de juego: "
                f"{local} {fueras[0]} - "
                f"{fueras[1]} {visitante}"
            )

        else:

            resultado.append(
                "Fueras de juego: "
                "Datos no disponibles"
            )

        resultado.append("")

        return resultado

    # ========================================================
    # PRÓXIMO H2H
    # ========================================================

    proximo_h2h = datos.get(
        "proximo_h2h"
    )

    if proximo_h2h:

        lineas.append(
            "🔜 PRÓXIMO ENFRENTAMIENTO"
        )

        lineas.append("")

        local = (
            proximo_h2h
            .get("homeTeam", {})
            .get("name")
        )

        visitante = (
            proximo_h2h
            .get("awayTeam", {})
            .get("name")
        )

        torneo = (
            proximo_h2h
            .get("uniqueTournament", {})
            .get("name")
        )

        if not torneo:

            torneo = (
                proximo_h2h
                .get("tournament", {})
                .get("name")
            )

        lineas.append(
            f"Fecha y hora: "
            f"{formatear_fecha_hora(proximo_h2h)}"
        )

        lineas.append(
            f"Partido: "
            f"{local} vs {visitante}"
        )

        if torneo:

            lineas.append(
                f"Competición: {torneo}"
            )

        lineas.append("")

    # ========================================================
    # PRÓXIMO EQUIPO A
    # ========================================================

    proximo_a = datos.get(
        "proximo_a"
    )

    if proximo_a:

        lineas.append(
            f"🔜 PRÓXIMO PARTIDO DE {nombre_a}"
        )

        lineas.append("")

        local = (
            proximo_a
            .get("homeTeam", {})
            .get("name")
        )

        visitante = (
            proximo_a
            .get("awayTeam", {})
            .get("name")
        )

        lineas.append(
            f"Fecha y hora: "
            f"{formatear_fecha_hora(proximo_a)}"
        )

        lineas.append(
            f"Partido: "
            f"{local} vs {visitante}"
        )

        torneo = (
            proximo_a
            .get("uniqueTournament", {})
            .get("name")
        )

        if not torneo:

            torneo = (
                proximo_a
                .get("tournament", {})
                .get("name")
            )

        if torneo:

            lineas.append(
                f"Competición: {torneo}"
            )

        home_id = (
            proximo_a
            .get("homeTeam", {})
            .get("id")
        )

        away_id = (
            proximo_a
            .get("awayTeam", {})
            .get("id")
        )

        entrenador_home = (
            obtener_entrenador_equipo(
                home_id
            )
        )

        entrenador_away = (
            obtener_entrenador_equipo(
                away_id
            )
        )

        if entrenador_home:

            lineas.append(
                f"Entrenador {local}: "
                f"{entrenador_home}"
            )

        if entrenador_away:

            lineas.append(
                f"Entrenador {visitante}: "
                f"{entrenador_away}"
            )

        alineaciones = obtener_alineaciones(
            proximo_a
        )

        if alineaciones:

            lineas.append(
                "Alineaciones:"
            )

            for side, nombre_equipo in [
                ("home", local),
                ("away", visitante)
            ]:

                alineacion = (
                    extraer_alineacion_equipo(
                        alineaciones,
                        side
                    )
                )

                if not alineacion:
                    continue

                formacion = alineacion.get(
                    "formacion"
                )

                if formacion:

                    lineas.append(
                        f"- {nombre_equipo} "
                        f"({formacion})"
                    )

                titulares = alineacion.get(
                    "titulares",
                    []
                )

                if titulares:

                    lineas.append(
                        "- Titulares: "
                        +
                        ", ".join(
                            titulares
                        )
                    )

        lineas.append("")

    # ========================================================
    # PRÓXIMO EQUIPO B
    # ========================================================

    proximo_b = datos.get(
        "proximo_b"
    )

    if proximo_b:

        lineas.append(
            f"🔜 PRÓXIMO PARTIDO DE {nombre_b}"
        )

        lineas.append("")

        local = (
            proximo_b
            .get("homeTeam", {})
            .get("name")
        )

        visitante = (
            proximo_b
            .get("awayTeam", {})
            .get("name")
        )

        lineas.append(
            f"Fecha y hora: "
            f"{formatear_fecha_hora(proximo_b)}"
        )

        lineas.append(
            f"Partido: "
            f"{local} vs {visitante}"
        )

        torneo = (
            proximo_b
            .get("uniqueTournament", {})
            .get("name")
        )

        if not torneo:

            torneo = (
                proximo_b
                .get("tournament", {})
                .get("name")
            )

        if torneo:

            lineas.append(
                f"Competición: {torneo}"
            )

        home_id = (
            proximo_b
            .get("homeTeam", {})
            .get("id")
        )

        away_id = (
            proximo_b
            .get("awayTeam", {})
            .get("id")
        )

        entrenador_home = (
            obtener_entrenador_equipo(
                home_id
            )
        )

        entrenador_away = (
            obtener_entrenador_equipo(
                away_id
            )
        )

        if entrenador_home:

            lineas.append(
                f"Entrenador {local}: "
                f"{entrenador_home}"
            )

        if entrenador_away:

            lineas.append(
                f"Entrenador {visitante}: "
                f"{entrenador_away}"
            )

        alineaciones = obtener_alineaciones(
            proximo_b
        )

        if alineaciones:

            lineas.append(
                "Alineaciones:"
            )

            for side, nombre_equipo in [
                ("home", local),
                ("away", visitante)
            ]:

                alineacion = (
                    extraer_alineacion_equipo(
                        alineaciones,
                        side
                    )
                )

                if not alineacion:
                    continue

                formacion = alineacion.get(
                    "formacion"
                )

                if formacion:

                    lineas.append(
                        f"- {nombre_equipo} "
                        f"({formacion})"
                    )

                titulares = alineacion.get(
                    "titulares",
                    []
                )

                if titulares:

                    lineas.append(
                        "- Titulares: "
                        +
                        ", ".join(
                            titulares
                        )
                    )

        lineas.append("")

    # ========================================================
    # H2H
    # ========================================================

    lineas.append(
        "🔁 ENFRENTAMIENTOS DIRECTOS"
    )

    lineas.append("")

    lineas.extend(
        texto_partido(
            f"🏠 Último enfrentamiento "
            f"con {nombre_a} como LOCAL",
            datos.get(
                "h2h_a_local"
            )
        )
    )

    lineas.extend(
        texto_partido(
            f"✈️ Último enfrentamiento "
            f"con {nombre_a} como VISITANTE",
            datos.get(
                "h2h_a_visitante"
            )
        )
    )

    # ========================================================
    # EQUIPO A
    # ========================================================

    lineas.append(
        f"⚽ {nombre_a}"
    )

    lineas.append("")

    lineas.extend(
        texto_partido(
            "🏠 Último partido como LOCAL",
            datos.get(
                "local_a"
            )
        )
    )

    lineas.extend(
        texto_partido(
            "✈️ Último partido como VISITANTE",
            datos.get(
                "visitante_a"
            )
        )
    )

    # ========================================================
    # EQUIPO B
    # ========================================================

    lineas.append(
        f"⚽ {nombre_b}"
    )

    lineas.append("")

    lineas.extend(
        texto_partido(
            "🏠 Último partido como LOCAL",
            datos.get(
                "local_b"
            )
        )
    )

    lineas.extend(
        texto_partido(
            "✈️ Último partido como VISITANTE",
            datos.get(
                "visitante_b"
            )
        )
    )

    return "\n".join(
        lineas
    )


# ============================================================
# BOTÓN COPIAR TEXTO
# ============================================================

def mostrar_boton_copiar(texto):

    texto_js = (
        texto
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
    )

    html = f"""
    <button
        onclick="copiarTexto()"
        style="
            width: 100%;
            padding: 10px 16px;
            font-size: 16px;
            font-weight: 600;
            border-radius: 8px;
            border: 1px solid #ccc;
            background: white;
            color: black;
            cursor: pointer;
        "
    >
        📋 Copiar texto completo
    </button>

    <script>

    function copiarTexto() {{

        const texto = `{texto_js}`;

        navigator.clipboard.writeText(texto)
            .then(() => {{

                const boton =
                    document.querySelector("button");

                boton.innerText =
                    "✅ Texto copiado";

                setTimeout(() => {{

                    boton.innerText =
                        "📋 Copiar texto completo";

                }}, 2000);

            }})
            .catch(() => {{

                const area =
                    document.createElement("textarea");

                area.value = texto;

                document.body.appendChild(
                    area
                );

                area.select();

                document.execCommand(
                    "copy"
                );

                document.body.removeChild(
                    area
                );

                const boton =
                    document.querySelector("button");

                boton.innerText =
                    "✅ Texto copiado";

                setTimeout(() => {{

                    boton.innerText =
                        "📋 Copiar texto completo";

                }}, 2000);

            }});

    }}

    </script>
    """

    components.html(
        html,
        height=55
    )


# ============================================================
# BOTÓN BUSCAR
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
        == "Competición específica"
        and
        not liga.strip()
    ):

        st.error(
            "Selecciona o escribe la liga/copa."
        )

        st.stop()

    # ========================================================
    # RANGO
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

    if modo_competicion == "Todas las competiciones":

        st.info(
            "🌎 Modo: **todas las competiciones**."
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

    st.success(
        f"Equipos encontrados: "
        f"{nombre_a} vs {nombre_b}"
    )

    if (
        modo_competicion
        == "Todas las competiciones"
    ):

        st.info(
            "Liga: **Todas las competiciones**"
        )

    else:

        st.info(
            f"Liga seleccionada: **{liga}**"
        )

    # ========================================================
    # OBTENER IDS PARA PRÓXIMOS PARTIDOS
    # ========================================================

    equipo_a_api = buscar_equipo(
        nombre_a
    )

    equipo_b_api = buscar_equipo(
        nombre_b
    )

    id_a = (
        equipo_a_api.get("id")
        if equipo_a_api
        else None
    )

    id_b = (
        equipo_b_api.get("id")
        if equipo_b_api
        else None
    )

    # ========================================================
    # PRÓXIMOS PARTIDOS
    # ========================================================

    proximo_h2h = None
    proximo_a = None
    proximo_b = None

    if id_a and id_b:

        proximo_h2h = obtener_proximo_h2h(
            id_a,
            id_b
        )

        proximos_a = obtener_proximos_partidos(
            id_a
        )

        proximos_b = obtener_proximos_partidos(
            id_b
        )

        if proximos_a:

            proximo_a = proximos_a[0]

        if proximos_b:

            proximo_b = proximos_b[0]

    datos["proximo_h2h"] = proximo_h2h
    datos["proximo_a"] = proximo_a
    datos["proximo_b"] = proximo_b

    # ========================================================
    # TEXTO COPIABLE
    # ========================================================

    texto_completo = generar_texto_copiable(
        datos,
        nombre_a,
        nombre_b,
        liga
    )

    # ========================================================
    # BOTÓN COPIAR ARRIBA
    # ========================================================

    mostrar_boton_copiar(
        texto_completo
    )

    # ========================================================
    # PRÓXIMO ENFRENTAMIENTO
    # ========================================================

    if proximo_h2h:

        st.divider()

        st.header(
            "🔜 Próximo enfrentamiento"
        )

        mostrar_proximo_partido(
            proximo_h2h,
            f"{nombre_a} vs {nombre_b}"
        )

    # ========================================================
    # PRÓXIMO PARTIDO EQUIPO A
    # ========================================================

    if proximo_a:

        st.divider()

        st.header(
            f"🔜 Próximo partido de {nombre_a}"
        )

        mostrar_proximo_partido(
            proximo_a,
            f"Próximo partido de {nombre_a}"
        )

    # ========================================================
    # PRÓXIMO PARTIDO EQUIPO B
    # ========================================================

    if proximo_b:

        st.divider()

        st.header(
            f"🔜 Próximo partido de {nombre_b}"
        )

        mostrar_proximo_partido(
            proximo_b,
            f"Próximo partido de {nombre_b}"
        )

    # ========================================================
    # H2H
    # ========================================================

    st.divider()

    st.header(
        "🔁 Enfrentamientos directos"
    )

    # ========================================================
    # H2H LOCAL
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
    # H2H VISITANTE
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