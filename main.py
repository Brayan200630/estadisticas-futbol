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
            print("ERROR HTTP:", respuesta.status_code)
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
        return None

    resultados = datos.get("results", [])

    candidatos = []

    for resultado in resultados:

        if resultado.get("type") != "team":
            continue

        entidad = resultado.get("entity", {})

        if entidad:
            candidatos.append(entidad)

    nombre_buscado = (
        nombre.strip().lower()
    )

    # Coincidencia exacta
    for equipo in candidatos:

        nombre_encontrado = (
            equipo.get("name", "")
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

    # Coincidencia parcial
    for equipo in candidatos:

        nombre_encontrado = (
            equipo.get("name", "")
            .strip()
            .lower()
        )

        if (
            nombre_buscado in nombre_encontrado
            or
            nombre_encontrado in nombre_buscado
        ):

            print(
                "EQUIPO ENCONTRADO POR COINCIDENCIA:",
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
# FECHA
# ============================================================

def obtener_fecha(evento):

    if not evento:
        return None

    timestamp = evento.get("startTimestamp")

    if not timestamp:
        return None

    try:
        return datetime.fromtimestamp(timestamp)

    except Exception:
        return None


def obtener_fecha_date(evento):

    fecha = obtener_fecha(evento)

    if not fecha:
        return None

    return fecha.date()


# ============================================================
# ESTADO
# ============================================================

def obtener_estado(evento):

    status = evento.get("status", {})

    return str(
        status.get("type", "")
    ).lower()


def es_finalizado(evento):

    estado = obtener_estado(evento)

    return estado in {
        "finished",
        "ended"
    }


def partido_valido(evento):

    if not evento:
        return False

    return es_finalizado(evento)


# ============================================================
# FECHA LÍMITE
# ============================================================

def es_anterior_a_fecha(evento, fecha_limite):

    fecha = obtener_fecha_date(evento)

    if not fecha:
        return False

    try:

        limite = datetime.strptime(
            fecha_limite,
            "%Y-%m-%d"
        ).date()

    except Exception:

        return False

    return fecha < limite


# ============================================================
# NOMBRE DE LA LIGA
# ============================================================

def obtener_nombre_liga(evento):

    if not evento:
        return ""

    # --------------------------------------------------------
    # uniqueTournament
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # tournament
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
        return nombre

    # --------------------------------------------------------
    # uniqueTournament dentro de tournament
    # --------------------------------------------------------

    unique = tournament.get(
        "uniqueTournament",
        {}
    )

    return unique.get(
        "name",
        ""
    )


# ============================================================
# NORMALIZAR TEXTO
# ============================================================

def normalizar_texto(texto):

    if texto is None:
        return ""

    return (
        str(texto)
        .strip()
        .lower()
    )


# ============================================================
# COMPROBAR LIGA
# ============================================================

def pertenece_a_liga(evento, liga):

    if not evento:
        return False

    nombre_liga_evento = normalizar_texto(
        obtener_nombre_liga(evento)
    )

    liga_buscada = normalizar_texto(
        liga
    )

    print(
        "LIGA EVENTO:",
        repr(nombre_liga_evento),
        "| LIGA BUSCADA:",
        repr(liga_buscada)
    )

    if not nombre_liga_evento:
        return False

    if not liga_buscada:
        return False

    # Coincidencia exacta
    if nombre_liga_evento == liga_buscada:
        return True

    # Coincidencia parcial
    if (
        liga_buscada in nombre_liga_evento
        or
        nombre_liga_evento in liga_buscada
    ):
        return True

    return False


# ============================================================
# HISTORIAL DEL EQUIPO
# ============================================================

def obtener_historial(team_id):

    partidos = []

    pagina = 0

    max_paginas = 30

    while pagina < max_paginas:

        url = (
            f"{BASE_URL}/team/"
            f"{team_id}/events/last/"
            f"{pagina}"
        )

        datos = obtener_json(url)

        if not datos:
            break

        eventos = datos.get(
            "events",
            []
        )

        if not eventos:
            break

        print(
            f"EQUIPO {team_id} | "
            f"PÁGINA {pagina} | "
            f"EVENTOS: {len(eventos)}"
        )

        partidos.extend(eventos)

        if not datos.get(
            "hasNextPage",
            False
        ):
            break

        pagina += 1

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
        {home_id, away_id}
        ==
        {equipo_a_id, equipo_b_id}
    )


# ============================================================
# BUSCAR H2H EN LOS HISTORIALES
# ============================================================

def buscar_h2h_en_historial(
    historial,
    equipo_a_id,
    equipo_b_id,
    liga,
    fecha_limite
):

    candidatos = []

    for evento in historial:

        # Solo A vs B
        if not es_enfrentamiento(
            evento,
            equipo_a_id,
            equipo_b_id
        ):
            continue

        # Solo partidos anteriores
        if not es_anterior_a_fecha(
            evento,
            fecha_limite
        ):
            continue

        # Solo finalizados
        if not partido_valido(evento):
            continue

        # SOLO LA LIGA INDICADA
        if not pertenece_a_liga(
            evento,
            liga
        ):
            continue

        candidatos.append(evento)

    return candidatos


# ============================================================
# OBTENER H2H
# ============================================================

def obtener_h2h(
    historial_a,
    historial_b,
    equipo_a_id,
    equipo_b_id,
    liga,
    fecha_limite
):

    candidatos = []

    # Historial A
    candidatos.extend(
        buscar_h2h_en_historial(
            historial_a,
            equipo_a_id,
            equipo_b_id,
            liga,
            fecha_limite
        )
    )

    # Historial B
    candidatos.extend(
        buscar_h2h_en_historial(
            historial_b,
            equipo_a_id,
            equipo_b_id,
            liga,
            fecha_limite
        )
    )

    # --------------------------------------------------------
    # ELIMINAR DUPLICADOS
    # --------------------------------------------------------

    unicos = {}

    for evento in candidatos:

        event_id = evento.get("id")

        if event_id:

            unicos[event_id] = evento

    candidatos = list(
        unicos.values()
    )

    # --------------------------------------------------------
    # ORDENAR DEL MÁS RECIENTE AL MÁS ANTIGUO
    # --------------------------------------------------------

    candidatos.sort(
        key=lambda evento:
        evento.get(
            "startTimestamp",
            0
        ),
        reverse=True
    )

    print("====================================")
    print("H2H ENCONTRADOS EN LA LIGA:", len(candidatos))

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
            "|",
            obtener_nombre_liga(evento),
            "| EVENT ID:",
            evento.get("id")
        )

    print("====================================")

    # SOLO LOS DOS ÚLTIMOS
    return candidatos[:2]


# ============================================================
# ÚLTIMO PARTIDO COMO LOCAL
# ============================================================

def ultimo_local(
    historial,
    equipo_id,
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

        if not partido_valido(evento):
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

        candidatos.append(evento)

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
# ÚLTIMO PARTIDO COMO VISITANTE
# ============================================================

def ultimo_visitante(
    historial,
    equipo_id,
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

        if not partido_valido(evento):
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

        candidatos.append(evento)

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
# CONVERTIR VALOR ESTADÍSTICO
# ============================================================

def extraer_valor_estadistica(item, campo):

    if not item:
        return None

    valor = item.get(campo)

    if valor is not None:
        return valor

    # Algunas respuestas pueden utilizar value
    if campo == "home":
        valor = item.get("homeValue")

        if valor is not None:
            return valor

    if campo == "away":
        valor = item.get("awayValue")

        if valor is not None:
            return valor

    return None


# ============================================================
# ESTADÍSTICAS DE UN PARTIDO
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

    event_id = evento.get("id")

    if not event_id:
        print(
            "NO HAY EVENT ID PARA ESTADÍSTICAS"
        )

        return resultado

    url = (
        f"{BASE_URL}/event/"
        f"{event_id}/statistics"
    )

    print("====================================")
    print("BUSCANDO ESTADÍSTICAS")
    print("EVENT ID:", event_id)
    print("URL:", url)
    print("====================================")

    datos = obtener_json(url)

    if not datos:

        print(
            "NO SE OBTUVIERON ESTADÍSTICAS:",
            event_id
        )

        return resultado

    periodos = datos.get(
        "statistics",
        []
    )

    if not periodos:

        print(
            "SOFASCORE NO DEVOLVIÓ PERIODOS:",
            event_id
        )

        return resultado

    # --------------------------------------------------------
    # BUSCAR ALL
    # --------------------------------------------------------

    periodo = None

    for item in periodos:

        if str(
            item.get("period", "")
        ).upper() == "ALL":

            periodo = item
            break

    # Si no existe ALL usamos el primero
    if periodo is None:
        periodo = periodos[0]

    grupos = periodo.get(
        "groups",
        []
    )

    estadisticas = {}

    for grupo in grupos:

        items = grupo.get(
            "statisticsItems",
            []
        )

        for item in items:

            nombre = normalizar_texto(
                item.get("name", "")
            )

            if nombre:
                estadisticas[nombre] = item

    print(
        "ESTADÍSTICAS ENCONTRADAS:",
        list(estadisticas.keys())
    )

    # --------------------------------------------------------
    # MAPEO
    # --------------------------------------------------------

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

    for nombre_api, nombre_salida in nombres.items():

        item = estadisticas.get(
            nombre_api
        )

        if not item:
            continue

        local = extraer_valor_estadistica(
            item,
            "home"
        )

        visitante = extraer_valor_estadistica(
            item,
            "away"
        )

        if (
            local is not None
            or
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

    # --------------------------------------------------------
    # VALIDACIONES
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # EQUIPO A
    # --------------------------------------------------------

    equipo_a = buscar_equipo(
        nombre_equipo_a
    )

    if not equipo_a:

        return {
            "error":
            f"No se encontró: {nombre_equipo_a}"
        }

    # --------------------------------------------------------
    # EQUIPO B
    # --------------------------------------------------------

    equipo_b = buscar_equipo(
        nombre_equipo_b
    )

    if not equipo_b:

        return {
            "error":
            f"No se encontró: {nombre_equipo_b}"
        }

    # --------------------------------------------------------
    # DATOS
    # --------------------------------------------------------

    id_a = equipo_a.get("id")
    id_b = equipo_b.get("id")

    nombre_a = equipo_a.get(
        "name",
        nombre_equipo_a
    )

    nombre_b = equipo_b.get(
        "name",
        nombre_equipo_b
    )

    print("====================================")
    print("EQUIPO A:", nombre_a, "| ID:", id_a)
    print("EQUIPO B:", nombre_b, "| ID:", id_b)
    print("LIGA:", liga)
    print("FECHA:", fecha_partido)
    print("====================================")

    # --------------------------------------------------------
    # HISTORIALES
    # --------------------------------------------------------

    historial_a = obtener_historial(id_a)

    historial_b = obtener_historial(id_b)

    # --------------------------------------------------------
    # H2H
    # --------------------------------------------------------

    h2h = obtener_h2h(
        historial_a,
        historial_b,
        id_a,
        id_b,
        liga,
        fecha_partido
    )

    # --------------------------------------------------------
    # LOCAL / VISITANTE
    # --------------------------------------------------------

    local_a = ultimo_local(
        historial_a,
        id_a,
        fecha_partido,
        liga
    )

    visitante_a = ultimo_visitante(
        historial_a,
        id_a,
        fecha_partido,
        liga
    )

    local_b = ultimo_local(
        historial_b,
        id_b,
        fecha_partido,
        liga
    )

    visitante_b = ultimo_visitante(
        historial_b,
        id_b,
        fecha_partido,
        liga
    )

    # --------------------------------------------------------
    # RESULTADO H2H
    # --------------------------------------------------------

    print("====================================")
    print("RESULTADO H2H:", len(h2h))

    for evento in h2h:

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
            "|",
            evento.get("id")
        )

    print("====================================")

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