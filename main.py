from curl_cffi import requests
from datetime import datetime, timezone
from urllib.parse import quote
from zoneinfo import ZoneInfo


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_URL = "https://www.sofascore.com/api/v1"

# No buscar partidos anteriores a esta fecha
FECHA_MINIMA = datetime.strptime(
    "2020-01-01",
    "%Y-%m-%d"
).date()

# Zona horaria de Perú
ZONA_HORARIA = ZoneInfo("America/Lima")

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
        normalizar_texto(nombre)
    )

    # ========================================================
    # COINCIDENCIA EXACTA
    # ========================================================

    for equipo in candidatos:

        nombre_encontrado = normalizar_texto(
            equipo.get("name", "")
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

        nombre_encontrado = normalizar_texto(
            equipo.get("name", "")
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
# NORMALIZAR TEXTO
# ============================================================

def normalizar_texto(texto):

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
# CREAR CLAVE DE LIGA
#
# Sirve para considerar equivalentes nombres como:
#
# Liga 1 Te Apuesto
# Liga 1, Clausura
# Liga 1, Apertura
# Liga 1
#
# La identificación definitiva se hace mediante
# uniqueTournament.id.
# ============================================================

def obtener_clave_liga(nombre):

    nombre = normalizar_texto(
        nombre
    )

    palabras_excluidas = {

        "te",
        "apuesto",
        "apertura",
        "clausura",
        "fase",
        "final",
        "playoff",
        "playoffs"

    }

    palabras = nombre.replace(
        ",",
        " "
    ).split()

    palabras_filtradas = []

    for palabra in palabras:

        if palabra in palabras_excluidas:
            continue

        if palabra.isdigit():
            continue

        palabras_filtradas.append(
            palabra
        )

    return " ".join(
        palabras_filtradas
    )


# ============================================================
# COMPROBAR SI UNA LIGA CORRESPONDE A OTRA
# ============================================================

def pertenece_a_liga(evento, liga):

    if not evento:
        return False

    nombre_liga = obtener_nombre_liga(
        evento
    )

    if not nombre_liga:
        return False

    clave_evento = obtener_clave_liga(
        nombre_liga
    )

    clave_buscada = obtener_clave_liga(
        liga
    )

    print(
        "LIGA EVENTO:",
        repr(clave_evento),
        "| LIGA BUSCADA:",
        repr(clave_buscada)
    )

    if not clave_evento:
        return False

    if not clave_buscada:
        return False

    if clave_evento == clave_buscada:
        return True

    if (
        clave_evento in clave_buscada
        or
        clave_buscada in clave_evento
    ):
        return True

    return False


# ============================================================
# OBTENER FECHA DEL EVENTO
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

        fecha_utc = datetime.fromtimestamp(
            int(timestamp),
            tz=timezone.utc
        )

        return fecha_utc.astimezone(
            ZONA_HORARIA
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

    if hasattr(
        fecha_limite,
        "year"
    ) and hasattr(
        fecha_limite,
        "month"
    ) and hasattr(
        fecha_limite,
        "day"
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
# FECHA VÁLIDA
#
# Ejemplo:
#
# Fecha partido: 12/08/2026
#
# 11/08/2026 -> válido
# 10/08/2026 -> válido
# 01/01/2020 -> válido
# 12/08/2026 -> NO
# 13/08/2026 -> NO
# 2019 -> NO
# ============================================================

def es_fecha_valida(
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

    # No aceptar el mismo día ni posteriores
    if fecha_evento >= fecha_limite_date:
        return False

    # No aceptar antes de 2020
    if fecha_evento < FECHA_MINIMA:
        return False

    return True


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

    if not es_finalizado(
        evento
    ):
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
# OBTENER UNIQUE TOURNAMENT ID
# ============================================================

def obtener_unique_tournament_id(evento):

    if not evento:
        return None

    # --------------------------------------------------------
    # uniqueTournament directamente
    # --------------------------------------------------------

    unique = evento.get(
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

        if tournament_id is not None:
            return tournament_id

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

        unique = tournament.get(
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

            if tournament_id is not None:
                return tournament_id

    return None


# ============================================================
# OBTENER HISTORIAL DEL EQUIPO
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
# ORDENAR POR FECHA DESCENDENTE
#
# MÁS RECIENTE
# ↓
# MÁS ANTIGUO
#
# Ejemplo:
#
# 11/08/2026
# 10/08/2026
# 09/08/2026
# 01/08/2026
# ============================================================

def ordenar_por_fecha(eventos):

    eventos = eliminar_duplicados(
        eventos
    )

    eventos.sort(
        key=lambda evento:
        evento.get(
            "startTimestamp",
            0
        ),
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
# IDENTIFICAR COMPETICIÓN REAL
#
# Busca el partido más reciente del historial que coincida
# con la liga solicitada.
#
# Después utiliza UNIQUE TOURNAMENT ID.
#
# Esto evita depender de que el nombre sea exactamente:
#
# "Liga 1 Te Apuesto"
#
# cuando SofaScore puede devolver:
#
# "Liga 1, Clausura"
#
# ============================================================

def obtener_tournament_id_de_liga(
    historial_a,
    historial_b,
    liga,
    fecha_limite
):

    todos = []

    todos.extend(
        historial_a
    )

    todos.extend(
        historial_b
    )

    candidatos = []

    for evento in todos:

        if not evento:
            continue

        fecha_evento = obtener_fecha_date(
            evento
        )

        if not fecha_evento:
            continue

        # Debe ser anterior al partido analizado
        if fecha_evento >= fecha_limite:
            continue

        # Desde 2020
        if fecha_evento < FECHA_MINIMA:
            continue

        # Partido terminado
        if not partido_valido(
            evento
        ):
            continue

        # Coincidencia de liga
        if not pertenece_a_liga(
            evento,
            liga
        ):
            continue

        tournament_id = (
            obtener_unique_tournament_id(
                evento
            )
        )

        if tournament_id is None:
            continue

        candidatos.append({
            "fecha": fecha_evento,
            "tournament_id": tournament_id,
            "nombre_liga": obtener_nombre_liga(
                evento
            )
        })

    # ========================================================
    # MÁS RECIENTE PRIMERO
    # ========================================================

    candidatos.sort(
        key=lambda x: x["fecha"],
        reverse=True
    )

    if candidatos:

        candidato = candidatos[0]

        fecha_detectada = candidato[
            "fecha"
        ]

        tournament_id = candidato[
            "tournament_id"
        ]

        nombre_liga = candidato[
            "nombre_liga"
        ]

        print("====================================")
        print("TORNEO DETECTADO")
        print("Nombre:", nombre_liga)
        print("Tournament ID:", tournament_id)
        print("Fecha:", fecha_detectada)
        print("====================================")

        return tournament_id

    print(
        "NO SE PUDO IDENTIFICAR "
        "EL UNIQUE TOURNAMENT DE:",
        liga
    )

    return None


# ============================================================
# H2H POR LOCALÍA
#
# DEVUELVE:
#
# 1. Último enfrentamiento con Equipo A LOCAL
# 2. Último enfrentamiento con Equipo A VISITANTE
#
# FILTROS:
#
# - Equipo A vs Equipo B
# - Partido terminado
# - Desde 01/01/2020
# - Antes de la fecha indicada
# - Mismo uniqueTournament.id
# ============================================================

def obtener_h2h_por_localia(
    historial_a,
    historial_b,
    equipo_a_id,
    equipo_b_id,
    liga,
    fecha_limite
):

    # ========================================================
    # IDENTIFICAR COMPETICIÓN
    # ========================================================

    tournament_id_objetivo = (
        obtener_tournament_id_de_liga(
            historial_a,
            historial_b,
            liga,
            fecha_limite
        )
    )

    if tournament_id_objetivo is None:

        print(
            "NO SE ENCONTRÓ EL ID "
            "DE LA COMPETICIÓN"
        )

        return (
            None,
            None
        )

    # ========================================================
    # UNIR HISTORIALES
    # ========================================================

    todos = []

    todos.extend(
        historial_a
    )

    todos.extend(
        historial_b
    )

    candidatos = []

    # ========================================================
    # FILTRAR H2H
    # ========================================================

    for evento in todos:

        if not evento:
            continue

        # Exactamente Equipo A vs Equipo B
        if not es_enfrentamiento(
            evento,
            equipo_a_id,
            equipo_b_id
        ):
            continue

        # Partido terminado
        if not partido_valido(
            evento
        ):
            continue

        # Fecha válida
        if not es_fecha_valida(
            evento,
            fecha_limite
        ):
            continue

        # Tournament ID
        tournament_id_evento = (
            obtener_unique_tournament_id(
                evento
            )
        )

        if tournament_id_evento != tournament_id_objetivo:
            continue

        candidatos.append(
            evento
        )

    # ========================================================
    # MÁS RECIENTE PRIMERO
    # ========================================================

    candidatos = ordenar_por_fecha(
        candidatos
    )

    # ========================================================
    # DEBUG H2H
    # ========================================================

    print("====================================")
    print(
        "H2H VÁLIDOS:",
        len(candidatos)
    )

    for evento in candidatos:

        fecha_evento = obtener_fecha_date(
            evento
        )

        local = (
            evento
            .get("homeTeam", {})
            .get("name")
        )

        visitante = (
            evento
            .get("awayTeam", {})
            .get("name")
        )

        torneo = obtener_nombre_liga(
            evento
        )

        tournament_id = (
            obtener_unique_tournament_id(
                evento
            )
        )

        print(
            fecha_evento,
            "|",
            local,
            "vs",
            visitante,
            "| Liga:",
            torneo,
            "| Tournament ID:",
            tournament_id
        )

    print("====================================")

    # ========================================================
    # ÚLTIMO A COMO LOCAL
    #
    # Como candidatos está ordenado DESC,
    # el primer resultado encontrado es el más reciente.
    # ========================================================

    h2h_a_local = None

    for evento in candidatos:

        home_id = (
            evento
            .get("homeTeam", {})
            .get("id")
        )

        if home_id == equipo_a_id:

            h2h_a_local = evento

            break

    # ========================================================
    # ÚLTIMO A COMO VISITANTE
    # ========================================================

    h2h_a_visitante = None

    for evento in candidatos:

        away_id = (
            evento
            .get("awayTeam", {})
            .get("id")
        )

        if away_id == equipo_a_id:

            h2h_a_visitante = evento

            break

    # ========================================================
    # DEBUG FINAL
    # ========================================================

    print("====================================")

    print(
        "ÚLTIMO H2H A LOCAL:"
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
        "ÚLTIMO H2H A VISITANTE:"
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

    print("====================================")

    return (
        h2h_a_local,
        h2h_a_visitante
    )


# ============================================================
# ÚLTIMO PARTIDO COMO LOCAL
#
# MISMA COMPETICIÓN
#
# Busca:
#
# 11/08/2026
# 10/08/2026
# 09/08/2026
# ...
#
# y toma el primero que cumpla.
# ============================================================

def ultimo_local(
    historial,
    equipo_id,
    fecha_limite,
    tournament_id
):

    candidatos = []

    for evento in historial:

        if not evento:
            continue

        if not partido_valido(
            evento
        ):
            continue

        if not es_fecha_valida(
            evento,
            fecha_limite
        ):
            continue

        tournament_id_evento = (
            obtener_unique_tournament_id(
                evento
            )
        )

        if tournament_id_evento != tournament_id:
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

        evento = candidatos[0]

        print(
            "ÚLTIMO LOCAL:",
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
            .get("name"),
            "| LIGA:",
            obtener_nombre_liga(
                evento
            )
        )

        return evento

    return None


# ============================================================
# ÚLTIMO PARTIDO COMO VISITANTE
#
# MISMA COMPETICIÓN
# ============================================================

def ultimo_visitante(
    historial,
    equipo_id,
    fecha_limite,
    tournament_id
):

    candidatos = []

    for evento in historial:

        if not evento:
            continue

        if not partido_valido(
            evento
        ):
            continue

        if not es_fecha_valida(
            evento,
            fecha_limite
        ):
            continue

        tournament_id_evento = (
            obtener_unique_tournament_id(
                evento
            )
        )

        if tournament_id_evento != tournament_id:
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

        evento = candidatos[0]

        print(
            "ÚLTIMO VISITANTE:",
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
            .get("name"),
            "| LIGA:",
            obtener_nombre_liga(
                evento
            )
        )

        return evento

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

    print("====================================")
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
        fecha_partido_str
    )

    print(
        "FECHA MÍNIMA:",
        FECHA_MINIMA
    )

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
    # IDENTIFICAR EL TOURNAMENT ID
    #
    # Se hace UNA VEZ y se utiliza para:
    #
    # H2H
    # Último local A
    # Último visitante A
    # Último local B
    # Último visitante B
    # ========================================================

    tournament_id = (
        obtener_tournament_id_de_liga(
            historial_a,
            historial_b,
            liga,
            fecha_limite
        )
    )

    if tournament_id is None:

        return {
            "error":
            "No se pudo identificar "
            "la competición solicitada."
        }

    # ========================================================
    # H2H
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
    # ÚLTIMOS PARTIDOS EQUIPO A
    # ========================================================

    local_a = ultimo_local(
        historial_a,
        id_a,
        fecha_limite,
        tournament_id
    )

    visitante_a = ultimo_visitante(
        historial_a,
        id_a,
        fecha_limite,
        tournament_id
    )

    # ========================================================
    # ÚLTIMOS PARTIDOS EQUIPO B
    # ========================================================

    local_b = ultimo_local(
        historial_b,
        id_b,
        fecha_limite,
        tournament_id
    )

    visitante_b = ultimo_visitante(
        historial_b,
        id_b,
        fecha_limite,
        tournament_id
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

    print("====================================")
    print("RESULTADO FINAL")
    print("====================================")

    print(
        "TOURNAMENT ID:",
        tournament_id
    )

    print(
        "H2H A LOCAL:"
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
            .get("name"),
            "|",
            obtener_nombre_liga(
                h2h_a_local
            )
        )

    else:

        print(
            "NO ENCONTRADO"
        )

    print(
        "H2H A VISITANTE:"
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
            .get("name"),
            "|",
            obtener_nombre_liga(
                h2h_a_visitante
            )
        )

    else:

        print(
            "NO ENCONTRADO"
        )

    print("====================================")

    return {

        "equipo_a":
            nombre_a,

        "equipo_b":
            nombre_b,

        "liga":
            liga,

        "fecha_partido":
            fecha_partido_str,

        "tournament_id":
            tournament_id,

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