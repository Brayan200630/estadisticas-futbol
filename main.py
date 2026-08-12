from curl_cffi import requests
from datetime import datetime
from urllib.parse import quote


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_URL = "https://www.sofascore.com/api/v1"

session = requests.Session()


# ============================================================
# PETICIÓN A SOFASCORE
# ============================================================

def obtener_json(url):

    try:

        respuesta = session.get(
            url,
            impersonate="chrome",
            timeout=20
        )

        print("====================================")
        print("URL:", url)
        print("STATUS:", respuesta.status_code)
        print("====================================")

        if respuesta.status_code != 200:
            return None

        return respuesta.json()

    except Exception as error:

        print("ERROR:", error)

        return None


# ============================================================
# BUSCAR EQUIPO
# ============================================================

def buscar_equipo(nombre):

    url = (
        f"{BASE_URL}/search/all"
        f"?q={quote(nombre)}"
    )

    datos = obtener_json(url)

    if not datos:

        print("SOFASCORE NO DEVOLVIÓ DATOS")

        return None

    resultados = datos.get(
        "results",
        []
    )

    candidatos = []

    for resultado in resultados:

        entidad = resultado.get(
            "entity",
            {}
        )

        if not entidad:
            continue

        tipo = resultado.get(
            "type",
            ""
        )

        nombre_encontrado = entidad.get(
            "name",
            ""
        )

        print(
            "Resultado:",
            tipo,
            "|",
            nombre_encontrado
        )

        if tipo == "team":

            candidatos.append(
                entidad
            )

    # ========================================================
    # COINCIDENCIA EXACTA
    # ========================================================

    nombre_buscado = (
        nombre.strip().lower()
    )

    for equipo in candidatos:

        nombre_encontrado = (
            equipo
            .get("name", "")
            .strip()
            .lower()
        )

        if nombre_encontrado == nombre_buscado:

            print(
                "COINCIDENCIA EXACTA:",
                equipo.get("name"),
                "| ID:",
                equipo.get("id")
            )

            return equipo

    # ========================================================
    # COINCIDENCIA PARCIAL
    # ========================================================

    for equipo in candidatos:

        nombre_encontrado = (
            equipo
            .get("name", "")
            .strip()
            .lower()
        )

        if (
            nombre_buscado in nombre_encontrado
            or
            nombre_encontrado in nombre_buscado
        ):

            print(
                "COINCIDENCIA PARCIAL:",
                equipo.get("name"),
                "| ID:",
                equipo.get("id")
            )

            return equipo

    print(
        "NO SE ENCONTRÓ EL EQUIPO:",
        nombre
    )

    return None


# ============================================================
# OBTENER FECHA
# ============================================================

def obtener_fecha(evento):

    timestamp = evento.get(
        "startTimestamp"
    )

    if not timestamp:
        return None

    return datetime.fromtimestamp(
        timestamp
    )


# ============================================================
# ESTADO
# ============================================================

def obtener_estado(evento):

    status = evento.get(
        "status",
        {}
    )

    return str(
        status.get(
            "type",
            ""
        )
    ).lower()


def es_aplazado(evento):

    return obtener_estado(evento) in {
        "postponed",
        "delayed"
    }


def es_cancelado(evento):

    return obtener_estado(evento) in {
        "canceled",
        "cancelled"
    }


def es_no_iniciado(evento):

    return obtener_estado(evento) in {
        "scheduled",
        "notstarted",
        "not_started"
    }


def es_finalizado(evento):

    return obtener_estado(evento) in {
        "finished",
        "ended"
    }


# ============================================================
# PARTIDO VÁLIDO
# ============================================================

def partido_valido(evento):

    if not evento:
        return False

    if es_aplazado(evento):
        return False

    if es_cancelado(evento):
        return False

    if es_no_iniciado(evento):
        return False

    if not es_finalizado(evento):
        return False

    return True


# ============================================================
# FECHA ANTERIOR
# ============================================================

def es_anterior_a_fecha(
    evento,
    fecha_limite
):

    fecha = obtener_fecha(evento)

    if not fecha:
        return False

    return fecha.strftime(
        "%Y-%m-%d"
    ) < fecha_limite


# ============================================================
# OBTENER NOMBRE REAL DE LA LIGA
# ============================================================

def obtener_nombre_liga(evento):

    if not evento:
        return ""

    # --------------------------------------------------------
    # OPCIÓN 1
    # --------------------------------------------------------

    unique_tournament = evento.get(
        "uniqueTournament",
        {}
    )

    nombre = unique_tournament.get(
        "name",
        ""
    )

    if nombre:
        return nombre.strip()

    # --------------------------------------------------------
    # OPCIÓN 2
    # --------------------------------------------------------

    tournament = evento.get(
        "tournament",
        {}
    )

    nombre = tournament.get(
        "name",
        ""
    )

    if nombre:
        return nombre.strip()

    # --------------------------------------------------------
    # OPCIÓN 3
    # --------------------------------------------------------

    unique = tournament.get(
        "uniqueTournament",
        {}
    )

    nombre = unique.get(
        "name",
        ""
    )

    if nombre:
        return nombre.strip()

    return ""


# ============================================================
# FILTRO DE LIGA
# ============================================================

def pertenece_a_liga(
    evento,
    liga
):

    if not evento:
        return False

    if not liga:
        return False

    nombre_liga = obtener_nombre_liga(
        evento
    )

    liga_buscada = (
        liga.strip().lower()
    )

    liga_encontrada = (
        nombre_liga.strip().lower()
    )

    print(
        "LIGA ENCONTRADA:",
        repr(nombre_liga),
        "| LIGA BUSCADA:",
        repr(liga)
    )

    if not liga_encontrada:
        return False

    # Coincidencia exacta
    if liga_encontrada == liga_buscada:
        return True

    # Coincidencia parcial
    if (
        liga_buscada in liga_encontrada
        or
        liga_encontrada in liga_buscada
    ):
        return True

    return False


# ============================================================
# HISTORIAL DEL EQUIPO
# ============================================================

def obtener_historial(team_id):

    partidos = []

    pagina = 0

    # Aumentamos a 20 páginas para tener más posibilidades
    # de encontrar H2H antiguos.

    while pagina < 20:

        url = (
            f"{BASE_URL}/team/"
            f"{team_id}/events/last/"
            f"{pagina}"
        )

        datos = obtener_json(
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

        print(
            "EQUIPO:",
            team_id,
            "| PÁGINA:",
            pagina,
            "| PARTIDOS:",
            len(eventos)
        )

        partidos.extend(
            eventos
        )

        if not datos.get(
            "hasNextPage",
            False
        ):
            break

        pagina += 1

    return partidos


# ============================================================
# OBTENER H2H
# ============================================================

def obtener_h2h(
    historial_a,
    historial_b,
    equipo_a_id,
    equipo_b_id,
    fecha_limite,
    liga
):

    encontrados = []

    # ========================================================
    # UNIR HISTORIALES
    # ========================================================

    todos = (
        historial_a
        +
        historial_b
    )

    # ========================================================
    # ELIMINAR DUPLICADOS
    # ========================================================

    unicos = {}

    for evento in todos:

        event_id = evento.get(
            "id"
        )

        if event_id:

            unicos[event_id] = evento

    todos = list(
        unicos.values()
    )

    # ========================================================
    # BUSCAR H2H
    # ========================================================

    for evento in todos:

        if not evento:
            continue

        # ----------------------------------------------------
        # FECHA
        # ----------------------------------------------------

        if not es_anterior_a_fecha(
            evento,
            fecha_limite
        ):
            continue

        # ----------------------------------------------------
        # FINALIZADO
        # ----------------------------------------------------

        if not partido_valido(evento):
            continue

        # ----------------------------------------------------
        # IDS
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # COMPROBAR QUE SEAN LOS DOS EQUIPOS
        # ----------------------------------------------------

        if {home_id, away_id} != {
            equipo_a_id,
            equipo_b_id
        }:

            continue

        # ----------------------------------------------------
        # LIGA
        # ----------------------------------------------------

        if not pertenece_a_liga(
            evento,
            liga
        ):

            continue

        print(
            "===================================="
        )

        print(
            "H2H ENCONTRADO"
        )

        print(
            evento
            .get("homeTeam", {})
            .get("name", ""),
            "vs",
            evento
            .get("awayTeam", {})
            .get("name", "")
        )

        print(
            "LIGA:",
            obtener_nombre_liga(evento)
        )

        print(
            "EVENT ID:",
            evento.get("id")
        )

        print(
            "===================================="
        )

        encontrados.append(
            evento
        )

    # ========================================================
    # ORDENAR
    # ========================================================

    encontrados.sort(
        key=lambda x:
        x.get(
            "startTimestamp",
            0
        ),
        reverse=True
    )

    # ========================================================
    # DOS H2H MÁS RECIENTES
    # ========================================================

    return encontrados[:2]


# ============================================================
# ÚLTIMO PARTIDO COMO LOCAL
# ============================================================

def ultimo_local(
    historial,
    equipo,
    fecha_limite,
    liga
):

    candidatos = []

    for evento in historial:

        if not es_anterior_a_fecha(
            evento,
            fecha_limite
        ):
            continue

        if not pertenece_a_liga(
            evento,
            liga
        ):
            continue

        local = (
            evento
            .get("homeTeam", {})
            .get("name", "")
        )

        if (
            local.lower()
            ==
            equipo.lower()
            and
            partido_valido(evento)
        ):

            candidatos.append(
                evento
            )

    candidatos.sort(
        key=lambda x:
        x.get(
            "startTimestamp",
            0
        ),
        reverse=True
    )

    if candidatos:

        return candidatos[0]

    return None


# ============================================================
# ÚLTIMO PARTIDO COMO VISITANTE
# ============================================================

def ultimo_visitante(
    historial,
    equipo,
    fecha_limite,
    liga
):

    candidatos = []

    for evento in historial:

        if not es_anterior_a_fecha(
            evento,
            fecha_limite
        ):
            continue

        if not pertenece_a_liga(
            evento,
            liga
        ):
            continue

        visitante = (
            evento
            .get("awayTeam", {})
            .get("name", "")
        )

        if (
            visitante.lower()
            ==
            equipo.lower()
            and
            partido_valido(evento)
        ):

            candidatos.append(
                evento
            )

    candidatos.sort(
        key=lambda x:
        x.get(
            "startTimestamp",
            0
        ),
        reverse=True
    )

    if candidatos:

        return candidatos[0]

    return None


# ============================================================
# ESTADÍSTICAS
# ============================================================

def obtener_estadisticas(evento):

    resultado = {

        "Posesión": None,

        "Córners": None,

        "Faltas": None,

        "Tarjetas amarillas": None,

        "Tiros a puerta": None,

        "Fueras de juego": None
    }

    if not evento:
        return resultado

    if not partido_valido(evento):
        return resultado

    event_id = evento.get(
        "id"
    )

    if not event_id:
        return resultado

    url = (
        f"{BASE_URL}/event/"
        f"{event_id}/statistics"
    )

    datos = obtener_json(
        url
    )

    if not datos:
        return resultado

    periodos = datos.get(
        "statistics",
        []
    )

    periodo = None

    for item in periodos:

        if item.get(
            "period"
        ) == "ALL":

            periodo = item

            break

    if periodo is None:

        if periodos:

            periodo = periodos[0]

        else:

            return resultado

    grupos = periodo.get(
        "groups",
        []
    )

    estadisticas = {}

    for grupo in grupos:

        for item in grupo.get(
            "statisticsItems",
            []
        ):

            nombre = item.get(
                "name",
                ""
            ).strip().lower()

            if nombre:

                estadisticas[
                    nombre
                ] = item

    nombres = {

        "ball possession":
            "Posesión",

        "corner kicks":
            "Córners",

        "fouls":
            "Faltas",

        "yellow cards":
            "Tarjetas amarillas",

        "shots on target":
            "Tiros a puerta",

        "offsides":
            "Fueras de juego"
    }

    for (
        nombre_api,
        nombre_salida
    ) in nombres.items():

        item = estadisticas.get(
            nombre_api
        )

        if not item:
            continue

        local = item.get(
            "home"
        )

        visitante = item.get(
            "away"
        )

        resultado[
            nombre_salida
        ] = (
            local,
            visitante
        )

    return resultado


# ============================================================
# ANALIZAR PARTIDO
# ============================================================

def analizar_partido(
    nombre_equipo_a,
    nombre_equipo_b,
    fecha_partido,
    liga
):

    # ========================================================
    # VALIDAR LIGA
    # ========================================================

    if not liga or not liga.strip():

        return {
            "error":
            "Debes indicar una liga."
        }

    liga = liga.strip()

    # ========================================================
    # BUSCAR EQUIPOS
    # ========================================================

    equipo_a = buscar_equipo(
        nombre_equipo_a
    )

    equipo_b = buscar_equipo(
        nombre_equipo_b
    )

    if not equipo_a:

        return {
            "error":
            f"No se encontró: {nombre_equipo_a}"
        }

    if not equipo_b:

        return {
            "error":
            f"No se encontró: {nombre_equipo_b}"
        }

    # ========================================================
    # IDS Y NOMBRES
    # ========================================================

    id_a = equipo_a["id"]

    id_b = equipo_b["id"]

    nombre_a = equipo_a["name"]

    nombre_b = equipo_b["name"]

    print(
        "===================================="
    )

    print(
        "EQUIPO A:",
        nombre_a,
        "| ID:",
        id_a
    )

    print(
        "EQUIPO B:",
        nombre_b,
        "| ID:",
        id_b
    )

    print(
        "LIGA:",
        liga
    )

    print(
        "FECHA:",
        fecha_partido
    )

    print(
        "===================================="
    )

    # ========================================================
    # HISTORIALES
    # ========================================================

    historial_a = obtener_historial(
        id_a
    )

    historial_b = obtener_historial(
        id_b
    )

    # ========================================================
    # H2H
    # ========================================================

    h2h = obtener_h2h(
        historial_a,
        historial_b,
        id_a,
        id_b,
        fecha_partido,
        liga
    )

    print(
        "TOTAL H2H ENCONTRADOS:",
        len(h2h)
    )

    # ========================================================
    # EQUIPO A - LOCAL
    # ========================================================

    local_a = ultimo_local(
        historial_a,
        nombre_a,
        fecha_partido,
        liga
    )

    # ========================================================
    # EQUIPO A - VISITANTE
    # ========================================================

    visitante_a = ultimo_visitante(
        historial_a,
        nombre_a,
        fecha_partido,
        liga
    )

    # ========================================================
    # EQUIPO B - LOCAL
    # ========================================================

    local_b = ultimo_local(
        historial_b,
        nombre_b,
        fecha_partido,
        liga
    )

    # ========================================================
    # EQUIPO B - VISITANTE
    # ========================================================

    visitante_b = ultimo_visitante(
        historial_b,
        nombre_b,
        fecha_partido,
        liga
    )

    # ========================================================
    # RESULTADO
    # ========================================================

    return {

        "equipo_a":
        nombre_a,

        "equipo_b":
        nombre_b,

        "liga":
        liga,

        "h2h":
        h2h,

        "local_a":
        local_a,

        "visitante_a":
        visitante_a,

        "local_b":
        local_b,

        "visitante_b":
        visitante_b
    }