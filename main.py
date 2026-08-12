from curl_cffi import requests
from datetime import datetime, timezone, date
from urllib.parse import quote


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_URL = "https://www.sofascore.com/api/v1"

session = requests.Session()

# IMPORTANTE:
# Nunca utilizar partidos anteriores a esta fecha.
FECHA_MINIMA = date(2020, 1, 1)


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

        print(
            "No se obtuvieron datos para:",
            nombre
        )

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
# OBTENER FECHA DE EVENTO
# ============================================================

def obtener_fecha(evento):

    if not evento:
        return None

    timestamp = evento.get(
        "startTimestamp"
    )

    if timestamp is None:
        return None

    try:

        return datetime.fromtimestamp(
            int(timestamp),
            tz=timezone.utc
        )

    except Exception:

        return None


# ============================================================
# OBTENER FECHA COMO DATE
# ============================================================

def obtener_fecha_date(evento):

    fecha = obtener_fecha(
        evento
    )

    if not fecha:
        return None

    return fecha.date()


# ============================================================
# CONVERTIR FECHA LÍMITE
# ============================================================

def convertir_fecha_limite(fecha_limite):

    if isinstance(
        fecha_limite,
        datetime
    ):

        return fecha_limite.date()

    if isinstance(
        fecha_limite,
        date
    ):

        return fecha_limite

    if isinstance(
        fecha_limite,
        str
    ):

        try:

            return datetime.strptime(
                fecha_limite,
                "%Y-%m-%d"
            ).date()

        except Exception:

            return None

    return None


# ============================================================
# OBTENER TIMESTAMP
# ============================================================

def obtener_timestamp(evento):

    if not evento:
        return 0

    timestamp = evento.get(
        "startTimestamp"
    )

    if timestamp is None:
        return 0

    try:

        return int(timestamp)

    except Exception:

        return 0


# ============================================================
# COMPROBAR RANGO DE FECHA
#
# Desde 01/01/2020 hasta el día anterior
# a la fecha del partido.
# ============================================================

def fecha_valida_para_analisis(
    evento,
    fecha_limite
):

    fecha_evento = obtener_fecha_date(
        evento
    )

    if not fecha_evento:
        return False

    fecha_limite_date = convertir_fecha_limite(
        fecha_limite
    )

    if not fecha_limite_date:
        return False

    # Nunca aceptar antes de 2020
    if fecha_evento < FECHA_MINIMA:
        return False

    # Nunca aceptar el mismo día o después
    if fecha_evento >= fecha_limite_date:
        return False

    return True


# ============================================================
# PARTIDO ANTERIOR A FECHA
# ============================================================

def es_anterior_a_fecha(
    evento,
    fecha_limite
):

    return fecha_valida_para_analisis(
        evento,
        fecha_limite
    )


# ============================================================
# ESTADO DEL PARTIDO
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

    if isinstance(
        unique,
        dict
    ):

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

    if isinstance(
        tournament,
        dict
    ):

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

        if isinstance(
            unique,
            dict
        ):

            nombre = unique.get(
                "name",
                ""
            )

            if nombre:
                return nombre

    return ""


# ============================================================
# NORMALIZAR LIGA
# ============================================================

def normalizar_liga(texto):

    if not texto:
        return ""

    texto = str(
        texto
    ).strip().lower()

    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u"
    }

    for viejo, nuevo in reemplazos.items():

        texto = texto.replace(
            viejo,
            nuevo
        )

    return " ".join(
        texto.split()
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

    nombre_liga = normalizar_liga(
        obtener_nombre_liga(evento)
    )

    liga_buscada = normalizar_liga(
        liga
    )

    print(
        "LIGA EVENTO:",
        repr(nombre_liga),
        "| LIGA BUSCADA:",
        repr(liga_buscada)
    )

    if not nombre_liga:
        return False

    if not liga_buscada:
        return False

    # Coincidencia exacta
    if nombre_liga == liga_buscada:
        return True

    # Coincidencia parcial
    if (
        liga_buscada in nombre_liga
        or
        nombre_liga in liga_buscada
    ):

        return True

    return False


# ============================================================
# OBTENER HISTORIAL DEL EQUIPO
# ============================================================

def obtener_historial(team_id):

    partidos = []

    pagina = 0

    # Ya no necesitamos 30 páginas.
    # 10 páginas = suficiente margen para llegar hasta 2020
    # en la mayoría de equipos.
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

        # ----------------------------------------------------
        # Si ya encontramos eventos que llegan a 2020,
        # podemos dejar de pedir páginas.
        # ----------------------------------------------------

        fechas = []

        for evento in eventos:

            fecha = obtener_fecha_date(
                evento
            )

            if fecha:
                fechas.append(
                    fecha
                )

        if fechas:

            fecha_mas_antigua = min(
                fechas
            )

            print(
                "FECHA MÁS ANTIGUA DE ESTA PÁGINA:",
                fecha_mas_antigua
            )

            if fecha_mas_antigua <= FECHA_MINIMA:

                print(
                    "SE ALCANZÓ EL LÍMITE DEL 01/01/2020"
                )

                break

        if not datos.get(
            "hasNextPage",
            False
        ):

            break

        pagina += 1

    return partidos


# ============================================================
# ELIMINAR DUPLICADOS
# ============================================================

def eliminar_duplicados(eventos):

    unicos = {}

    for evento in eventos:

        if not evento:
            continue

        event_id = evento.get(
            "id"
        )

        if event_id:

            unicos[event_id] = evento

    return list(
        unicos.values()
    )


# ============================================================
# ORDENAR POR FECHA
# ============================================================

def ordenar_por_fecha(eventos):

    eventos = eliminar_duplicados(
        eventos
    )

    eventos.sort(
        key=obtener_timestamp,
        reverse=True
    )

    return eventos


# ============================================================
# COMPROBAR ENFRENTAMIENTO
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
# H2H POR LOCALÍA
#
# Devuelve:
#
# 1. Último enfrentamiento con A LOCAL
# 2. Último enfrentamiento con A VISITANTE
#
# SOLO:
#
# 01/01/2020 <= fecha < fecha del partido
# ============================================================

def obtener_h2h_por_localia(
    historial_a,
    historial_b,
    equipo_a_id,
    equipo_b_id,
    liga,
    fecha_limite
):

    candidatos = []

    todos = []

    todos.extend(
        historial_a
    )

    todos.extend(
        historial_b
    )

    for evento in todos:

        if not evento:
            continue

        # Exactamente los dos equipos
        if not es_enfrentamiento(
            evento,
            equipo_a_id,
            equipo_b_id
        ):

            continue

        # Finalizado
        if not partido_valido(
            evento
        ):

            continue

        # Desde 2020 y antes del partido
        if not es_anterior_a_fecha(
            evento,
            fecha_limite
        ):

            continue

        # Misma liga
        if not pertenece_a_liga(
            evento,
            liga
        ):

            continue

        candidatos.append(
            evento
        )

    candidatos = ordenar_por_fecha(
        candidatos
    )

    print(
        "===================================="
    )

    print(
        "H2H VÁLIDOS:",
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
            .get("name")
        )

    print(
        "===================================="
    )

    # ========================================================
    # ÚLTIMO A COMO LOCAL
    # ========================================================

    h2h_a_local = None

    # ========================================================
    # ÚLTIMO A COMO VISITANTE
    # ========================================================

    h2h_a_visitante = None

    for evento in candidatos:

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

        if (
            h2h_a_local is None
            and
            home_id == equipo_a_id
        ):

            h2h_a_local = evento

        if (
            h2h_a_visitante is None
            and
            away_id == equipo_a_id
        ):

            h2h_a_visitante = evento

        if (
            h2h_a_local is not None
            and
            h2h_a_visitante is not None
        ):

            break

    return (
        h2h_a_local,
        h2h_a_visitante
    )


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

        if not evento:
            continue

        # Finalizado
        if not partido_valido(
            evento
        ):

            continue

        # Desde 2020 y antes de la fecha
        if not es_anterior_a_fecha(
            evento,
            fecha_limite
        ):

            continue

        # Misma liga
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

    candidatos = ordenar_por_fecha(
        candidatos
    )

    if candidatos:

        print(
            "ÚLTIMO LOCAL:",
            obtener_fecha_date(
                candidatos[0]
            ),
            "|",
            candidatos[0]
            .get("homeTeam", {})
            .get("name"),
            "vs",
            candidatos[0]
            .get("awayTeam", {})
            .get("name")
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

        if not evento:
            continue

        # Finalizado
        if not partido_valido(
            evento
        ):

            continue

        # Desde 2020 y antes de la fecha
        if not es_anterior_a_fecha(
            evento,
            fecha_limite
        ):

            continue

        # Misma liga
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

    candidatos = ordenar_por_fecha(
        candidatos
    )

    if candidatos:

        print(
            "ÚLTIMO VISITANTE:",
            obtener_fecha_date(
                candidatos[0]
            ),
            "|",
            candidatos[0]
            .get("homeTeam", {})
            .get("name"),
            "vs",
            candidatos[0]
            .get("awayTeam", {})
            .get("name")
        )

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

    # ========================================================
    # BUSCAR ALL
    # ========================================================

    for item in periodos:

        if item.get(
            "period"
        ) == "ALL":

            periodo = item

            break

    # ========================================================
    # RESPALDO
    # ========================================================

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

            nombre = (
                item
                .get("name", "")
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

    # ========================================================
    # CONVERTIR
    # ========================================================

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
    # FECHA
    # ========================================================

    fecha_limite = convertir_fecha_limite(
        fecha_partido
    )

    if not fecha_limite:

        return {
            "error":
            "La fecha del partido no es válida."
        }

    fecha_partido_str = (
        fecha_limite.strftime(
            "%Y-%m-%d"
        )
    )

    # ========================================================
    # VALIDAR QUE LA FECHA SEA POSTERIOR A 2020
    # ========================================================

    if fecha_limite <= FECHA_MINIMA:

        return {
            "error":
            "La fecha del partido debe ser posterior al 01/01/2020."
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
        fecha_partido_str
    )

    print(
        "RANGO HISTÓRICO:",
        FECHA_MINIMA,
        "→",
        fecha_limite
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
    # ÚLTIMO A LOCAL
    # ÚLTIMO A VISITANTE
    # ========================================================

    (
        h2h_a_local,
        h2h_a_visitante
    ) = obtener_h2h_por_localia(
        historial_a,
        historial_b,
        id_a,
        id_b,
        liga,
        fecha_limite
    )

    # ========================================================
    # EQUIPO A LOCAL
    # ========================================================

    local_a = ultimo_local(
        historial_a,
        id_a,
        fecha_limite,
        liga
    )

    # ========================================================
    # EQUIPO A VISITANTE
    # ========================================================

    visitante_a = ultimo_visitante(
        historial_a,
        id_a,
        fecha_limite,
        liga
    )

    # ========================================================
    # EQUIPO B LOCAL
    # ========================================================

    local_b = ultimo_local(
        historial_b,
        id_b,
        fecha_limite,
        liga
    )

    # ========================================================
    # EQUIPO B VISITANTE
    # ========================================================

    visitante_b = ultimo_visitante(
        historial_b,
        id_b,
        fecha_limite,
        liga
    )

    # ========================================================
    # H2H COMO LISTA
    # ========================================================

    h2h = []

    if h2h_a_local:

        h2h.append(
            h2h_a_local
        )

    if (
        h2h_a_visitante
        and
        (
            not h2h_a_local
            or
            h2h_a_visitante.get("id")
            !=
            h2h_a_local.get("id")
        )
    ):

        h2h.append(
            h2h_a_visitante
        )

    # ========================================================
    # DEBUG FINAL
    # ========================================================

    print(
        "===================================="
    )

    print(
        "H2H A COMO LOCAL:"
    )

    if h2h_a_local:

        print(
            obtener_fecha_date(
                h2h_a_local
            ),
            "|",
            h2h_a_local
            .get("homeTeam", {})
            .get("name"),
            "vs",
            h2h_a_local
            .get("awayTeam", {})
            .get("name")
        )

    else:

        print(
            "NO ENCONTRADO"
        )

    print(
        "H2H A COMO VISITANTE:"
    )

    if h2h_a_visitante:

        print(
            obtener_fecha_date(
                h2h_a_visitante
            ),
            "|",
            h2h_a_visitante
            .get("homeTeam", {})
            .get("name"),
            "vs",
            h2h_a_visitante
            .get("awayTeam", {})
            .get("name")
        )

    else:

        print(
            "NO ENCONTRADO"
        )

    print(
        "===================================="
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

        "fecha_partido":
            fecha_partido_str,

        "h2h":
            h2h,

        "h2h_a_local":
            h2h_a_local,

        "h2h_a_visitante":
            h2h_a_visitante,

        "local_a":
            local_a,

        "visitante_a":
            visitante_a,

        "local_b":
            local_b,

        "visitante_b":
            visitante_b
    }