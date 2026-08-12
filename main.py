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

        if respuesta.status_code != 200:

            print(
                f"HTTP {respuesta.status_code}: {url}"
            )

            return None

        return respuesta.json()

    except Exception as error:

        print(
            f"Error consultando Sofascore: {error}"
        )

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
        return None

    resultados = datos.get(
        "results",
        []
    )

    # Coincidencia exacta
    for resultado in resultados:

        entidad = resultado.get(
            "entity",
            {}
        )

        nombre_encontrado = entidad.get(
            "name",
            ""
        )

        deporte = entidad.get(
            "sport",
            {}
        ).get(
            "slug"
        )

        if (
            nombre_encontrado.lower()
            == nombre.lower()
            and deporte == "football"
        ):

            return entidad

    # Coincidencia parcial
    for resultado in resultados:

        entidad = resultado.get(
            "entity",
            {}
        )

        nombre_encontrado = entidad.get(
            "name",
            ""
        )

        deporte = entidad.get(
            "sport",
            {}
        ).get(
            "slug"
        )

        if (
            nombre.lower()
            in nombre_encontrado.lower()
            and deporte == "football"
        ):

            return entidad

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
# ESTADO DEL PARTIDO
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


# ============================================================
# PARTIDO APLAZADO
# ============================================================

def es_aplazado(evento):

    estado = obtener_estado(
        evento
    )

    return estado in {
        "postponed",
        "delayed"
    }


# ============================================================
# PARTIDO CANCELADO
# ============================================================

def es_cancelado(evento):

    estado = obtener_estado(
        evento
    )

    return estado in {
        "canceled",
        "cancelled"
    }


# ============================================================
# PARTIDO NO INICIADO
# ============================================================

def es_no_iniciado(evento):

    estado = obtener_estado(
        evento
    )

    return estado in {
        "scheduled",
        "notstarted",
        "not_started"
    }


# ============================================================
# PARTIDO FINALIZADO
# ============================================================

def es_finalizado(evento):

    estado = obtener_estado(
        evento
    )

    return estado in {
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

    fecha = obtener_fecha(
        evento
    )

    if not fecha:
        return False

    return fecha.strftime(
        "%Y-%m-%d"
    ) < fecha_limite


# ============================================================
# HISTORIAL DEL EQUIPO
# ============================================================

def obtener_historial(team_id):

    partidos = []

    pagina = 0

    while True:

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

        partidos.extend(
            eventos
        )

        if not datos.get(
            "hasNextPage",
            False
        ):
            break

        pagina += 1

        if pagina >= 10:
            break

    return partidos


# ============================================================
# OBTENER H2H
# ============================================================

def obtener_h2h(
    historial,
    equipo_local,
    equipo_visitante,
    fecha_limite
):

    encontrados = []

    for evento in historial:

        if not es_anterior_a_fecha(
            evento,
            fecha_limite
        ):
            continue

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

        if (
            local.lower()
            == equipo_local.lower()
            and
            visitante.lower()
            == equipo_visitante.lower()
            and
            partido_valido(evento)
        ):

            encontrados.append(
                evento
            )

    encontrados.sort(
        key=lambda x:
        x.get(
            "startTimestamp",
            0
        ),
        reverse=True
    )

    return encontrados


# ============================================================
# DOS ÚLTIMOS H2H
# ============================================================

def obtener_dos_h2h(
    historial_a,
    historial_b,
    equipo_a,
    equipo_b,
    fecha_limite
):

    h2h_a = obtener_h2h(
        historial_a,
        equipo_a,
        equipo_b,
        fecha_limite
    )

    h2h_b = obtener_h2h(
        historial_b,
        equipo_b,
        equipo_a,
        fecha_limite
    )

    todos = h2h_a + h2h_b

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

    todos.sort(
        key=lambda x:
        x.get(
            "startTimestamp",
            0
        ),
        reverse=True
    )

    return todos[:2]


# ============================================================
# ÚLTIMO PARTIDO COMO LOCAL
# ============================================================

def ultimo_local(
    historial,
    equipo,
    fecha_limite
):

    candidatos = []

    for evento in historial:

        if not es_anterior_a_fecha(
            evento,
            fecha_limite
        ):
            continue

        local = (
            evento
            .get("homeTeam", {})
            .get("name", "")
        )

        if (
            local.lower()
            == equipo.lower()
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
    fecha_limite
):

    candidatos = []

    for evento in historial:

        if not es_anterior_a_fecha(
            evento,
            fecha_limite
        ):
            continue

        visitante = (
            evento
            .get("awayTeam", {})
            .get("name", "")
        )

        if (
            visitante.lower()
            == equipo.lower()
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

    for nombre_api, nombre_salida in (
        nombres.items()
    ):

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
    fecha_partido
):

    equipo_a = buscar_equipo(
        nombre_equipo_a
    )

    equipo_b = buscar_equipo(
        nombre_equipo_b
    )

    if not equipo_a:

        return {
            "error": (
                f"No se encontró: "
                f"{nombre_equipo_a}"
            )
        }

    if not equipo_b:

        return {
            "error": (
                f"No se encontró: "
                f"{nombre_equipo_b}"
            )
        }

    id_a = equipo_a["id"]
    id_b = equipo_b["id"]

    nombre_a = equipo_a["name"]
    nombre_b = equipo_b["name"]

    historial_a = obtener_historial(
        id_a
    )

    historial_b = obtener_historial(
        id_b
    )

    h2h = obtener_dos_h2h(
        historial_a,
        historial_b,
        nombre_a,
        nombre_b,
        fecha_partido
    )

    local_a = ultimo_local(
        historial_a,
        nombre_a,
        fecha_partido
    )

    visitante_a = ultimo_visitante(
        historial_a,
        nombre_a,
        fecha_partido
    )

    local_b = ultimo_local(
        historial_b,
        nombre_b,
        fecha_partido
    )

    visitante_b = ultimo_visitante(
        historial_b,
        nombre_b,
        fecha_partido
    )

    return {

        "equipo_a": nombre_a,

        "equipo_b": nombre_b,

        "h2h": h2h,

        "local_a": local_a,

        "visitante_a": visitante_a,

        "local_b": local_b,

        "visitante_b": visitante_b
    }