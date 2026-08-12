from curl_cffi import requests
from datetime import datetime
from urllib.parse import quote
import time


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

        if not entidad:
            continue

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

    fecha = obtener_fecha(evento)

    if not fecha:
        return None

    return fecha.date()


# ============================================================
# ESTADO
# ============================================================

def obtener_estado(evento):

    if not evento:
        return ""

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

    if not es_finalizado(evento):
        return False

    return True


# ============================================================
# FECHA ANTERIOR A LA DEL PARTIDO
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

    if unique:

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

    if tournament:

        nombre = tournament.get(
            "name",
            ""
        )

        if nombre:
            return nombre

        unique2 = tournament.get(
            "uniqueTournament",
            {}
        )

        if unique2:

            nombre = unique2.get(
                "name",
                ""
            )

            if nombre:
                return nombre

    return ""


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

    nombre_evento = normalizar_texto(
        obtener_nombre_liga(evento)
    )

    liga_buscada = normalizar_texto(
        liga
    )

    if not nombre_evento:
        return False

    if not liga_buscada:
        return False

    # Exacta
    if nombre_evento == liga_buscada:
        return True

    # Parcial
    if (
        liga_buscada in nombre_evento
        or
        nombre_evento in liga_buscada
    ):
        return True

    return False


# ============================================================
# OBTENER HISTORIAL
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
            f"EQUIPO {team_id} | "
            f"PÁGINA {pagina} | "
            f"EVENTOS: {len(eventos)}"
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
        home_id == equipo_a_id
        and away_id == equipo_b_id
    ) or (
        home_id == equipo_b_id
        and away_id == equipo_a_id
    )


# ============================================================
# LIMPIAR DUPLICADOS
# ============================================================

def eliminar_duplicados(eventos):

    unicos = {}

    for evento in eventos:

        event_id = evento.get(
            "id"
        )

        if event_id:
            unicos[event_id] = evento

    return list(
        unicos.values()
    )


# ============================================================
# H2H EN LA LIGA INDICADA
# ============================================================

def buscar_h2h_en_historiales(
    historial_a,
    historial_b,
    equipo_a_id,
    equipo_b_id,
    liga,
    fecha_limite
):

    candidatos = []

    # ========================================================
    # HISTORIAL A
    # ========================================================

    for evento in historial_a:

        if not es_enfrentamiento(
            evento,
            equipo_a_id,
            equipo_b_id
        ):
            continue

        if not es_anterior_a_fecha(
            evento,
            fecha_limite
        ):
            continue

        if not partido_valido(
            evento
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
    # HISTORIAL B
    # ========================================================

    for evento in historial_b:

        if not es_enfrentamiento(
            evento,
            equipo_a_id,
            equipo_b_id
        ):
            continue

        if not es_anterior_a_fecha(
            evento,
            fecha_limite
        ):
            continue

        if not partido_valido(
            evento
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

    candidatos = eliminar_duplicados(
        candidatos
    )

    # ========================================================
    # ORDENAR DEL MÁS RECIENTE AL MÁS ANTIGUO
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
        liga
    )

    print(
        "H2H ENCONTRADOS:",
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
            "|",
            obtener_nombre_liga(evento)
        )

    print(
        "===================================="
    )

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

        if not partido_valido(
            evento
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

    candidatos = eliminar_duplicados(
        candidatos
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

        print(
            "ÚLTIMO LOCAL:",
            obtener_fecha_date(
                candidatos[0]
            )
        )

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

        if not partido_valido(
            evento
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

    candidatos = eliminar_duplicados(
        candidatos
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

        print(
            "ÚLTIMO VISITANTE:",
            obtener_fecha_date(
                candidatos[0]
            )
        )

        return candidatos[0]

    return None


# ============================================================
# OBTENER ESTADÍSTICAS DEL EVENTO
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

    # ========================================================
    # ENDPOINT PRINCIPAL
    # ========================================================

    url = (
        f"{BASE_URL}/event/"
        f"{event_id}/statistics"
    )

    datos = obtener_json(
        url
    )

    if not datos:

        print(
            "NO HAY DATOS DE ESTADÍSTICAS:",
            event_id
        )

        return resultado

    periodos = datos.get(
        "statistics",
        []
    )

    if not periodos:
        return resultado

    periodo = None

    # Preferimos ALL
    for item in periodos:

        if str(
            item.get("period", "")
        ).upper() == "ALL":

            periodo = item

            break

    if periodo is None:
        periodo = periodos[0]

    grupos = periodo.get(
        "groups",
        []
    )

    # ========================================================
    # MAPA FLEXIBLE
    # ========================================================

    estadisticas = {}

    for grupo in grupos:

        items = grupo.get(
            "statisticsItems",
            []
        )

        for item in items:

            nombre = normalizar_texto(
                item.get(
                    "name",
                    ""
                )
            )

            if not nombre:
                continue

            estadisticas[
                nombre
            ] = item

    # ========================================================
    # NOMBRES POSIBLES
    # ========================================================

    equivalencias = {

        "posesión": [
            "ball possession",
            "possession"
        ],

        "córners": [
            "corner kicks",
            "corners",
            "corner"
        ],

        "faltas": [
            "fouls",
            "fouls committed"
        ],

        "tarjetas amarillas": [
            "yellow cards",
            "yellow card"
        ],

        "tiros a puerta": [
            "shots on target",
            "shots on goal"
        ],

        "fueras de juego": [
            "offsides",
            "offside"
        ]
    }

    # ========================================================
    # EXTRAER
    # ========================================================

    for nombre_salida, posibles in equivalencias.items():

        encontrado = None

        for posible in posibles:

            clave = normalizar_texto(
                posible
            )

            if clave in estadisticas:

                encontrado = estadisticas[
                    clave
                ]

                break

        if not encontrado:
            continue

        local = encontrado.get(
            "home"
        )

        visitante = encontrado.get(
            "away"
        )

        # Algunas respuestas pueden usar homeValue / awayValue
        if local is None:

            local = encontrado.get(
                "homeValue"
            )

        if visitante is None:

            visitante = encontrado.get(
                "awayValue"
            )

        resultado[
            nombre_salida
        ] = (
            local,
            visitante
        )

    print(
        "ESTADÍSTICAS EVENTO:",
        event_id,
        resultado
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
    # EQUIPO A
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
    # EQUIPO B
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

    print("====================================")
    print("EQUIPO A:", nombre_a, "| ID:", id_a)
    print("EQUIPO B:", nombre_b, "| ID:", id_b)
    print("LIGA:", liga)
    print("FECHA DEL PARTIDO:", fecha_partido)
    print("====================================")

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
    # IMPORTANTE:
    #
    # SOLO:
    # A vs B
    # B vs A
    #
    # DENTRO DE LA LIGA INDICADA
    #
    # ANTES DE LA FECHA DEL PARTIDO
    #
    # ORDENADOS DEL MÁS RECIENTE
    # ========================================================

    h2h = buscar_h2h_en_historiales(
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
    # DEBUG FINAL
    # ========================================================

    print("====================================")
    print("RESULTADO FINAL")
    print("====================================")

    print(
        "H2H:",
        len(h2h)
    )

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
            obtener_nombre_liga(evento)
        )

    print(
        "LOCAL A:",
        obtener_fecha_date(local_a)
        if local_a else None
    )

    print(
        "VISITANTE A:",
        obtener_fecha_date(visitante_a)
        if visitante_a else None
    )

    print(
        "LOCAL B:",
        obtener_fecha_date(local_b)
        if local_b else None
    )

    print(
        "VISITANTE B:",
        obtener_fecha_date(visitante_b)
        if visitante_b else None
    )

    print("====================================")

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