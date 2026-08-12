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

        if resultado.get(
            "type"
        ) != "team":

            continue

        entidad = resultado.get(
            "entity",
            {}
        )

        if not entidad:

            continue

        candidatos.append(
            entidad
        )

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
            .get(
                "name",
                ""
            )
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
            .get(
                "name",
                ""
            )
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
# FECHA
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


# ============================================================
# PARTIDO FINALIZADO
# ============================================================

def partido_valido(evento):

    if not evento:

        return False

    estado = obtener_estado(
        evento
    )

    if estado in {
        "postponed",
        "delayed",
        "canceled",
        "cancelled",
        "scheduled",
        "notstarted",
        "not_started"
    }:

        return False

    if estado not in {
        "finished",
        "ended"
    }:

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

    return (
        fecha.strftime(
            "%Y-%m-%d"
        )
        <
        fecha_limite
    )


# ============================================================
# OBTENER NOMBRE DE LIGA
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
    # tournament.uniqueTournament
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
# COMPROBAR LIGA
# ============================================================

def pertenece_a_liga(
    evento,
    liga
):

    if not evento:

        return False

    nombre_evento = (
        obtener_nombre_liga(
            evento
        )
        .strip()
        .lower()
    )

    nombre_buscado = (
        liga
        .strip()
        .lower()
    )

    if not nombre_evento:

        return False

    # Exacta

    if nombre_evento == nombre_buscado:

        return True

    # Parcial

    if (
        nombre_buscado in nombre_evento
        or
        nombre_evento in nombre_buscado
    ):

        return True

    return False


# ============================================================
# OBTENER HISTORIAL
# ============================================================

def obtener_historial(
    team_id,
    paginas=20
):

    partidos = []

    for pagina in range(
        paginas
    ):

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

    # --------------------------------------------------------
    # ELIMINAR DUPLICADOS
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # ORDENAR
    # --------------------------------------------------------

    partidos.sort(
        key=lambda x:
        x.get(
            "startTimestamp",
            0
        ),
        reverse=True
    )

    return partidos


# ============================================================
# BUSCAR PARTIDO ACTUAL
#
# Busca directamente en los partidos del día indicado.
#
# Esto nos permite obtener el EVENT ID que necesitamos
# para consultar el H2H oficial del partido.
# ============================================================

def buscar_evento_partido(
    id_a,
    id_b,
    fecha_partido,
    liga
):

    print(
        "===================================="
    )

    print(
        "BUSCANDO PARTIDO ACTUAL"
    )

    print(
        "Equipo A ID:",
        id_a
    )

    print(
        "Equipo B ID:",
        id_b
    )

    print(
        "Fecha:",
        fecha_partido
    )

    print(
        "Liga:",
        liga
    )

    print(
        "===================================="
    )

    # ========================================================
    # MÉTODO 1
    # EVENTOS PROGRAMADOS DEL DÍA
    # ========================================================

    url = (
        f"{BASE_URL}/sport/football/"
        f"scheduled-events/"
        f"{fecha_partido}"
    )

    datos = obtener_json(
        url
    )

    if datos:

        eventos = datos.get(
            "events",
            []
        )

        print(
            "EVENTOS DEL DÍA:",
            len(eventos)
        )

        for evento in eventos:

            home_id = (
                evento
                .get(
                    "homeTeam",
                    {}
                )
                .get("id")
            )

            away_id = (
                evento
                .get(
                    "awayTeam",
                    {}
                )
                .get("id")
            )

            # ------------------------------------------------
            # A vs B
            # ------------------------------------------------

            coincide = (

                (
                    home_id == id_a
                    and
                    away_id == id_b
                )

                or

                (
                    home_id == id_b
                    and
                    away_id == id_a
                )

            )

            if not coincide:

                continue

            nombre_liga = (
                obtener_nombre_liga(
                    evento
                )
            )

            print(
                "PARTIDO ENCONTRADO:",
                evento
                .get(
                    "homeTeam",
                    {}
                )
                .get("name"),
                "vs",
                evento
                .get(
                    "awayTeam",
                    {}
                )
                .get("name")
            )

            print(
                "LIGA:",
                nombre_liga
            )

            # ------------------------------------------------
            # Comprobar liga
            # ------------------------------------------------

            if pertenece_a_liga(
                evento,
                liga
            ):

                print(
                    "EVENT ID:",
                    evento.get("id")
                )

                return evento

    # ========================================================
    # MÉTODO 2
    # BUSCAR EN HISTORIAL DE AMBOS EQUIPOS
    #
    # Esto sirve como respaldo.
    # ========================================================

    print(
        "NO ENCONTRADO EN SCHEDULED-EVENTS."
    )

    print(
        "BUSCANDO COMO RESPALDO EN HISTORIALES..."
    )

    historial_a = obtener_historial(
        id_a,
        paginas=10
    )

    historial_b = obtener_historial(
        id_b,
        paginas=10
    )

    todos = (
        historial_a
        +
        historial_b
    )

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

    for evento in todos:

        home_id = (
            evento
            .get(
                "homeTeam",
                {}
            )
            .get("id")
        )

        away_id = (
            evento
            .get(
                "awayTeam",
                {}
            )
            .get("id")
        )

        coincide = (

            (
                home_id == id_a
                and
                away_id == id_b
            )

            or

            (
                home_id == id_b
                and
                away_id == id_a
            )

        )

        if not coincide:

            continue

        fecha = obtener_fecha(
            evento
        )

        if not fecha:

            continue

        if fecha.strftime(
            "%Y-%m-%d"
        ) != fecha_partido:

            continue

        if not pertenece_a_liga(
            evento,
            liga
        ):

            continue

        print(
            "PARTIDO ENCONTRADO EN HISTORIAL:",
            evento.get("id")
        )

        return evento

    print(
        "NO SE ENCONTRÓ EL PARTIDO ACTUAL."
    )

    return None


# ============================================================
# H2H DIRECTO
#
# ESTA ES LA PARTE NUEVA E IMPORTANTE.
#
# Sofascore tiene un endpoint específico:
#
# /event/{eventId}/h2h/events
#
# No reconstruimos los H2H manualmente.
# ============================================================

def obtener_h2h(
    event_id,
    liga
):

    print(
        "===================================="
    )

    print(
        "BUSCANDO H2H DIRECTAMENTE"
    )

    print(
        "EVENT ID:",
        event_id
    )

    print(
        "===================================="
    )

    url = (
        f"{BASE_URL}/event/"
        f"{event_id}/h2h/events"
    )

    datos = obtener_json(
        url
    )

    if not datos:

        print(
            "SOFASCORE NO DEVOLVIÓ H2H"
        )

        return []

    eventos = datos.get(
        "events",
        []
    )

    print(
        "H2H RECIBIDOS:",
        len(eventos)
    )

    # --------------------------------------------------------
    # El endpoint ya devuelve únicamente enfrentamientos
    # entre los dos equipos.
    #
    # Ahora solo filtramos:
    # - finalizados
    # - anteriores al partido
    # - liga seleccionada
    # --------------------------------------------------------

    encontrados = []

    for evento in eventos:

        if not evento:

            continue

        if not partido_valido(
            evento
        ):

            continue

        # ----------------------------------------------------
        # FILTRO DE LIGA
        # ----------------------------------------------------

        nombre_liga_evento = (
            obtener_nombre_liga(
                evento
            )
        )

        print(
            "H2H:",
            evento
            .get(
                "homeTeam",
                {}
            )
            .get("name"),
            "vs",
            evento
            .get(
                "awayTeam",
                {}
            )
            .get("name"),
            "| LIGA:",
            nombre_liga_evento
        )

        if not pertenece_a_liga(
            evento,
            liga
        ):

            continue

        encontrados.append(
            evento
        )

    # --------------------------------------------------------
    # ORDENAR
    # --------------------------------------------------------

    encontrados.sort(
        key=lambda x:
        x.get(
            "startTimestamp",
            0
        ),
        reverse=True
    )

    print(
        "H2H DESPUÉS DEL FILTRO:",
        len(encontrados)
    )

    return encontrados[:2]


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
            .get(
                "homeTeam",
                {}
            )
            .get("id")
        )

        if home_id != equipo_id:

            continue

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
            .get(
                "awayTeam",
                {}
            )
            .get("id")
        )

        if away_id != equipo_id:

            continue

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

def obtener_estadisticas(
    evento
):

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

    if not partido_valido(
        evento
    ):

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

            nombre = (
                item
                .get(
                    "name",
                    ""
                )
                .strip()
                .lower()
            )

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
    # VALIDAR
    # ========================================================

    if not liga or not liga.strip():

        return {
            "error":
            "Debes indicar una liga."
        }

    liga = liga.strip()

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
    # DATOS
    # ========================================================

    id_a = equipo_a.get(
        "id"
    )

    id_b = equipo_b.get(
        "id"
    )

    nombre_a = equipo_a.get(
        "name"
    )

    nombre_b = equipo_b.get(
        "name"
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
        "FECHA:",
        fecha_partido
    )

    print(
        "===================================="
    )

    # ========================================================
    # HISTORIALES
    #
    # Se mantienen para los últimos partidos LOCAL/VISITA.
    # ========================================================

    historial_a = obtener_historial(
        id_a
    )

    historial_b = obtener_historial(
        id_b
    )

    # ========================================================
    # BUSCAR PARTIDO ACTUAL
    # ========================================================

    evento_actual = buscar_evento_partido(
        id_a,
        id_b,
        fecha_partido,
        liga
    )

    # ========================================================
    # H2H
    #
    # AHORA USAMOS EL EVENT ID DIRECTAMENTE.
    # ========================================================

    h2h = []

    if evento_actual:

        event_id = evento_actual.get(
            "id"
        )

        if event_id:

            h2h = obtener_h2h(
                event_id,
                liga
            )

    else:

        print(
            "NO SE PUEDE CONSULTAR H2H:"
        )

        print(
            "No se encontró el event_id "
            "del partido actual."
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
    # RESULTADO
    # ========================================================

    return {

        "equipo_a":
            nombre_a,

        "equipo_b":
            nombre_b,

        "liga":
            liga,

        "evento_actual":
            evento_actual,

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