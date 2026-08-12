from curl_cffi import requests
from datetime import datetime, timedelta
from urllib.parse import quote


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_URL = "https://www.sofascore.com/api/v1"

session = requests.Session()

# No buscar partidos indefinidamente hacia atrás.
# Los partidos utilizados como "últimos" deben estar dentro
# de este periodo respecto a la fecha del partido.
MAX_ANTIGUEDAD_DIAS = 730


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

            print(
                "ERROR HTTP:",
                respuesta.status_code
            )

            return None

        return respuesta.json()

    except Exception as error:

        print(
            "ERROR:",
            error
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

    candidatos = []

    for resultado in resultados:

        if resultado.get("type") != "team":
            continue

        entidad = resultado.get(
            "entity",
            {}
        )

        if entidad:
            candidatos.append(entidad)

    nombre_buscado = (
        nombre
        .strip()
        .lower()
    )

    # ========================================================
    # COINCIDENCIA EXACTA
    # ========================================================

    for equipo in candidatos:

        nombre_encontrado = (
            equipo
            .get("name", "")
            .strip()
            .lower()
        )

        if nombre_encontrado == nombre_buscado:

            print(
                "EQUIPO ENCONTRADO:",
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
                "EQUIPO ENCONTRADO:",
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
# FECHA DEL EVENTO
# ============================================================

def obtener_fecha(evento):

    if not evento:
        return None

    timestamp = evento.get(
        "startTimestamp"
    )

    if not timestamp:
        return None

    try:

        return datetime.fromtimestamp(
            timestamp
        )

    except Exception:

        return None


# ============================================================
# FECHA COMO DATE
# ============================================================

def obtener_fecha_date(evento):

    fecha = obtener_fecha(
        evento
    )

    if not fecha:
        return None

    return fecha.date()


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

    return es_finalizado(evento)


# ============================================================
# CONVERTIR FECHA LÍMITE
# ============================================================

def convertir_fecha(fecha_limite):

    if isinstance(
        fecha_limite,
        datetime
    ):

        return fecha_limite.date()

    if hasattr(
        fecha_limite,
        "year"
    ) and hasattr(
        fecha_limite,
        "month"
    ):

        return fecha_limite

    return datetime.strptime(
        str(fecha_limite),
        "%Y-%m-%d"
    ).date()


# ============================================================
# PARTIDO ANTERIOR A LA FECHA DEL PARTIDO
# ============================================================

def es_anterior_a_fecha(
    evento,
    fecha_limite
):

    fecha = obtener_fecha_date(
        evento
    )

    if not fecha:
        return False

    limite = convertir_fecha(
        fecha_limite
    )

    return fecha < limite


# ============================================================
# PARTIDO DENTRO DEL PERIODO RECIENTE
# ============================================================

def es_reciente(
    evento,
    fecha_limite
):

    fecha = obtener_fecha_date(
        evento
    )

    if not fecha:
        return False

    limite = convertir_fecha(
        fecha_limite
    )

    fecha_minima = (
        limite -
        timedelta(
            days=MAX_ANTIGUEDAD_DIAS
        )
    )

    return (
        fecha_minima
        <= fecha
        < limite
    )


# ============================================================
# NOMBRE DE LIGA
# ============================================================

def obtener_nombre_liga(evento):

    if not evento:
        return ""

    unique = evento.get(
        "uniqueTournament",
        {}
    )

    nombre = unique.get(
        "name",
        ""
    )

    if nombre:
        return nombre

    tournament = evento.get(
        "tournament",
        {}
    )

    nombre = tournament.get(
        "name",
        ""
    )

    if nombre:
        return nombre

    unique = tournament.get(
        "uniqueTournament",
        {}
    )

    return unique.get(
        "name",
        ""
    )


# ============================================================
# NORMALIZAR TEXTO DE LIGA
# ============================================================

def normalizar_texto(texto):

    return (
        str(texto)
        .strip()
        .lower()
        .replace("-", " ")
        .replace("_", " ")
    )


# ============================================================
# COMPROBAR LIGA
# ============================================================

def pertenece_a_liga(
    evento,
    liga
):

    nombre_liga = normalizar_texto(
        obtener_nombre_liga(evento)
    )

    liga_buscada = normalizar_texto(
        liga
    )

    if not nombre_liga:
        return False

    if nombre_liga == liga_buscada:
        return True

    if (
        liga_buscada in nombre_liga
        or
        nombre_liga in liga_buscada
    ):
        return True

    return False


# ============================================================
# OBTENER HISTORIAL
# ============================================================

def obtener_historial(team_id):

    partidos = []

    pagina = 0

    # Máximo suficiente para encontrar partidos recientes
    # sin irnos indefinidamente hasta años demasiado antiguos.
    max_paginas = 10

    while pagina < max_paginas:

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
            f"EQUIPO {team_id} "
            f"| PÁGINA {pagina} "
            f"| EVENTOS: {len(eventos)}"
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

    # ========================================================
    # ELIMINAR DUPLICADOS
    # ========================================================

    unicos = {}

    for evento in partidos:

        event_id = evento.get(
            "id"
        )

        if event_id:
            unicos[event_id] = evento

    partidos = list(
        unicos.values()
    )

    # ========================================================
    # ORDENAR MÁS RECIENTE PRIMERO
    # ========================================================

    partidos.sort(
        key=lambda evento:
        evento.get(
            "startTimestamp",
            0
        ),
        reverse=True
    )

    return partidos


# ============================================================
# COMPROBAR H2H
# ============================================================

def es_enfrentamiento(
    evento,
    equipo_a_id,
    equipo_b_id
):

    if not evento:
        return False

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
        return False

    return (
        (
            home_id == equipo_a_id
            and
            away_id == equipo_b_id
        )
        or
        (
            home_id == equipo_b_id
            and
            away_id == equipo_a_id
        )
    )


# ============================================================
# OBTENER H2H DE LOS HISTORIALES
#
# IMPORTANTE:
# H2H significa:
#
# Equipo A vs Equipo B
# o
# Equipo B vs Equipo A
#
# PERO solamente dentro de la liga indicada.
# ============================================================

def obtener_h2h_desde_historiales(
    historial_a,
    historial_b,
    equipo_a_id,
    equipo_b_id,
    liga,
    fecha_limite
):

    candidatos = []

    # ========================================================
    # REVISAR HISTORIAL A
    # ========================================================

    for evento in historial_a:

        if not es_enfrentamiento(
            evento,
            equipo_a_id,
            equipo_b_id
        ):
            continue

        if not partido_valido(
            evento
        ):
            continue

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

        candidatos.append(
            evento
        )

    # ========================================================
    # REVISAR HISTORIAL B
    # ========================================================

    for evento in historial_b:

        if not es_enfrentamiento(
            evento,
            equipo_a_id,
            equipo_b_id
        ):
            continue

        if not partido_valido(
            evento
        ):
            continue

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

        candidatos.append(
            evento
        )

    # ========================================================
    # ELIMINAR DUPLICADOS
    # ========================================================

    unicos = {}

    for evento in candidatos:

        event_id = evento.get(
            "id"
        )

        if event_id:
            unicos[event_id] = evento

    candidatos = list(
        unicos.values()
    )

    # ========================================================
    # ORDENAR
    # ========================================================

    candidatos.sort(
        key=lambda evento:
        evento.get(
            "startTimestamp",
            0
        ),
        reverse=True
    )

    print(
        "===================================="
    )

    print(
        "H2H EN LA LIGA:",
        len(candidatos)
    )

    for evento in candidatos:

        print(
            obtener_fecha_date(evento),
            "|",
            evento
            .get("homeTeam", {})
            .get("name"),
            "vs",
            evento
            .get("awayTeam", {})
            .get("name"),
            "| LIGA:",
            obtener_nombre_liga(evento)
        )

    print(
        "===================================="
    )

    return candidatos[:2]


# ============================================================
# ÚLTIMO LOCAL
# ============================================================

def ultimo_local(
    historial,
    equipo_id,
    fecha_limite,
    liga
):

    candidatos = []

    for evento in historial:

        if not partido_valido(evento):
            continue

        if not es_reciente(
            evento,
            fecha_limite
        ):
            continue

        if not pertenece_a_liga(
            evento,
            liga
        ):
            continue

        home_id = (
            evento
            .get("homeTeam", {})
            .get("id")
        )

        if home_id != equipo_id:
            continue

        candidatos.append(
            evento
        )

    candidatos.sort(
        key=lambda evento:
        evento.get(
            "startTimestamp",
            0
        ),
        reverse=True
    )

    if candidatos:
        return candidatos[0]

    return None


# ============================================================
# ÚLTIMO VISITANTE
# ============================================================

def ultimo_visitante(
    historial,
    equipo_id,
    fecha_limite,
    liga
):

    candidatos = []

    for evento in historial:

        if not partido_valido(evento):
            continue

        if not es_reciente(
            evento,
            fecha_limite
        ):
            continue

        if not pertenece_a_liga(
            evento,
            liga
        ):
            continue

        away_id = (
            evento
            .get("awayTeam", {})
            .get("id")
        )

        if away_id != equipo_id:
            continue

        candidatos.append(
            evento
        )

    candidatos.sort(
        key=lambda evento:
        evento.get(
            "startTimestamp",
            0
        ),
        reverse=True
    )

    if candidatos:
        return candidatos[0]

    return None


# ============================================================
# OBTENER ESTADÍSTICAS
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

    print(
        "OBTENIENDO ESTADÍSTICAS:",
        event_id
    )

    datos = obtener_json(
        url
    )

    if not datos:
        print(
            "NO HAY ESTADÍSTICAS:",
            event_id
        )

        return resultado

    periodos = datos.get(
        "statistics",
        []
    )

    periodo = None

    # ========================================================
    # BUSCAR ALL
    # ========================================================

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

    # ========================================================
    # EXTRAER ESTADÍSTICAS
    # ========================================================

    for grupo in grupos:

        for item in grupo.get(
            "statisticsItems",
            []
        ):

            nombre = normalizar_texto(
                item.get(
                    "name",
                    ""
                )
            )

            if nombre:
                estadisticas[nombre] = item

    # ========================================================
    # NOMBRES
    # ========================================================

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

        # Algunos valores pueden venir
        # como strings.
        if (
            local is not None
            and
            visitante is not None
        ):

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
    # VALIDACIONES
    # ========================================================

    if not nombre_equipo_a.strip():

        return {
            "error":
            "Debes indicar el Equipo A."
        }

    if not nombre_equipo_b.strip():

        return {
            "error":
            "Debes indicar el Equipo B."
        }

    if not liga.strip():

        return {
            "error":
            "Debes indicar la liga."
        }

    # ========================================================
    # BUSCAR EQUIPO A
    # ========================================================

    equipo_a = buscar_equipo(
        nombre_equipo_a
    )

    if not equipo_a:

        return {
            "error":
            f"No se encontró: {nombre_equipo_a}"
        }

    # ========================================================
    # BUSCAR EQUIPO B
    # ========================================================

    equipo_b = buscar_equipo(
        nombre_equipo_b
    )

    if not equipo_b:

        return {
            "error":
            f"No se encontró: {nombre_equipo_b}"
        }

    # ========================================================
    # IDS
    # ========================================================

    id_a = equipo_a.get(
        "id"
    )

    id_b = equipo_b.get(
        "id"
    )

    nombre_a = equipo_a.get(
        "name",
        nombre_equipo_a
    )

    nombre_b = equipo_b.get(
        "name",
        nombre_equipo_b
    )

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
        "FECHA DEL PARTIDO:",
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
    #
    # SOLAMENTE:
    #
    # A vs B
    # B vs A
    #
    # EN LA LIGA INDICADA.
    # ========================================================

    h2h = obtener_h2h_desde_historiales(
        historial_a,
        historial_b,
        id_a,
        id_b,
        liga,
        fecha_partido
    )

    # ========================================================
    # ÚLTIMO LOCAL A
    # ========================================================

    local_a = ultimo_local(
        historial_a,
        id_a,
        fecha_partido,
        liga
    )

    # ========================================================
    # ÚLTIMO VISITANTE A
    # ========================================================

    visitante_a = ultimo_visitante(
        historial_a,
        id_a,
        fecha_partido,
        liga
    )

    # ========================================================
    # ÚLTIMO LOCAL B
    # ========================================================

    local_b = ultimo_local(
        historial_b,
        id_b,
        fecha_partido,
        liga
    )

    # ========================================================
    # ÚLTIMO VISITANTE B
    # ========================================================

    visitante_b = ultimo_visitante(
        historial_b,
        id_b,
        fecha_partido,
        liga
    )

    # ========================================================
    # ESTADÍSTICAS DE LOS H2H
    #
    # AQUÍ ESTÁ LA CORRECCIÓN IMPORTANTE.
    #
    # No se intenta sacar las estadísticas desde el endpoint
    # H2H. Se consulta directamente:
    #
    # /event/{event_id}/statistics
    #
    # para cada H2H.
    # ========================================================

    h2h_con_estadisticas = []

    for evento in h2h:

        evento_copia = dict(
            evento
        )

        evento_copia[
            "_estadisticas"
        ] = obtener_estadisticas(
            evento
        )

        h2h_con_estadisticas.append(
            evento_copia
        )

    # ========================================================
    # ESTADÍSTICAS DE LOS ÚLTIMOS PARTIDOS
    #
    # También se precargan aquí para que app.py pueda
    # utilizarlas si quiere.
    # ========================================================

    partidos = [

        local_a,

        visitante_a,

        local_b,

        visitante_b
    ]

    partidos_con_estadisticas = {}

    for evento in partidos:

        if not evento:
            continue

        event_id = evento.get(
            "id"
        )

        if not event_id:
            continue

        partidos_con_estadisticas[
            event_id
        ] = obtener_estadisticas(
            evento
        )

    # ========================================================
    # RESULTADO
    # ========================================================

    print(
        "===================================="
    )

    print(
        "H2H ENCONTRADOS:",
        len(h2h_con_estadisticas)
    )

    for evento in h2h_con_estadisticas:

        print(
            obtener_fecha_date(
                evento
            ),
            "|",
            evento
            .get("homeTeam", {})
            .get("name"),
            "vs",
            evento
            .get("awayTeam", {})
            .get("name")
        )

    print(
        "===================================="
    )

    return {

        "equipo_a":
            nombre_a,

        "equipo_b":
            nombre_b,

        "liga":
            liga,

        "h2h":
            h2h_con_estadisticas,

        "local_a":
            local_a,

        "visitante_a":
            visitante_a,

        "local_b":
            local_b,

        "visitante_b":
            visitante_b,

        "estadisticas_partidos":
            partidos_con_estadisticas
    }