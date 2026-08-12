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
        print("RESPUESTA:", respuesta.text[:500])
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
        print("URL:", url)

        return None

    resultados = datos.get(
        "results",
        []
    )

    print(
        "RESULTADOS ENCONTRADOS:",
        len(resultados)
    )

    candidatos = []

    for resultado in resultados:

        entidad = resultado.get(
            "entity",
            {}
        )

        if not entidad:
            continue

        nombre_encontrado = entidad.get(
            "name",
            ""
        )

        tipo = resultado.get(
            "type",
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
        nombre
        .strip()
        .lower()
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
                equipo.get("name")
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
                equipo.get("name")
            )

            return equipo

    # ========================================================
    # NO ENCONTRADO
    # ========================================================

    print(
        "NO SE ENCONTRÓ EL EQUIPO:",
        nombre
    )

    return None


# ============================================================
# OBTENER FECHA
# ============================================================

def obtener_fecha(evento):

    if not evento:
        return None

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
# OBTENER NOMBRES DE TODAS LAS POSIBLES LIGAS
# ============================================================

def obtener_nombres_liga(evento):

    nombres = []

    if not evento:
        return nombres

    # ========================================================
    # uniqueTournament
    # ========================================================

    unique_tournament = evento.get(
        "uniqueTournament",
        {}
    )

    if unique_tournament:

        nombre = unique_tournament.get(
            "name",
            ""
        )

        if nombre:
            nombres.append(
                nombre
            )

    # ========================================================
    # tournament
    # ========================================================

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
            nombres.append(
                nombre
            )

        # ====================================================
        # uniqueTournament dentro de tournament
        # ====================================================

        unique = tournament.get(
            "uniqueTournament",
            {}
        )

        if unique:

            nombre = unique.get(
                "name",
                ""
            )

            if nombre:
                nombres.append(
                    nombre
                )

    return nombres


# ============================================================
# OBTENER NOMBRE DE LIGA
# ============================================================

def obtener_nombre_liga(evento):

    nombres = obtener_nombres_liga(
        evento
    )

    if nombres:

        return nombres[0]

    return "Liga desconocida"


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

    liga_buscada = (
        liga
        .strip()
        .lower()
    )

    nombres = obtener_nombres_liga(
        evento
    )

    for nombre_liga in nombres:

        nombre_liga = (
            nombre_liga
            .strip()
            .lower()
        )

        print(
            "COMPARANDO LIGA:",
            repr(nombre_liga),
            "<->",
            repr(liga_buscada)
        )

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

        print(
            "HISTORIAL:",
            "Equipo",
            team_id,
            "| Página:",
            pagina,
            "| Partidos:",
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

        # ====================================================
        # Buscar hasta 30 páginas
        # ====================================================

        if pagina >= 30:
            break

    return partidos


# ============================================================
# H2H DIRECTO
#
# IMPORTANTE:
# NO FILTRAMOS POR LIGA.
#
# Buscamos los enfrentamientos entre los dos equipos
# independientemente de la competición.
# ============================================================

def obtener_h2h_directo(
    historial_a,
    equipo_a_id,
    equipo_b_id,
    fecha_limite
):

    encontrados = []

    # ========================================================
    # RECORRER HISTORIAL
    # ========================================================

    for evento in historial_a:

        if not evento:
            continue

        # ====================================================
        # FECHA
        # ====================================================

        if not es_anterior_a_fecha(
            evento,
            fecha_limite
        ):
            continue

        # ====================================================
        # FINALIZADO
        # ====================================================

        if not partido_valido(evento):
            continue

        # ====================================================
        # EQUIPOS
        # ====================================================

        home = evento.get(
            "homeTeam",
            {}
        )

        away = evento.get(
            "awayTeam",
            {}
        )

        home_id = home.get(
            "id"
        )

        away_id = away.get(
            "id"
        )

        # ====================================================
        # COMPROBAR LOS DOS EQUIPOS
        #
        # Esto permite:
        #
        # A vs B
        #
        # B vs A
        # ====================================================

        if (
            home_id == equipo_a_id
            and
            away_id == equipo_b_id
        ):

            encontrados.append(
                evento
            )

            continue

        if (
            home_id == equipo_b_id
            and
            away_id == equipo_a_id
        ):

            encontrados.append(
                evento
            )

            continue

    # ========================================================
    # ELIMINAR DUPLICADOS
    # ========================================================

    unicos = {}

    for evento in encontrados:

        event_id = evento.get(
            "id"
        )

        if event_id:

            unicos[event_id] = evento

    encontrados = list(
        unicos.values()
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

    print(
        "===================================="
    )

    print(
        "H2H ENCONTRADOS:",
        len(encontrados)
    )

    for evento in encontrados[:5]:

        home = evento.get(
            "homeTeam",
            {}
        )

        away = evento.get(
            "awayTeam",
            {}
        )

        print(
            home.get("name"),
            "vs",
            away.get("name"),
            "| Liga:",
            obtener_nombre_liga(
                evento
            )
        )

    print(
        "===================================="
    )

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

        # ====================================================
        # SOLO LA LIGA SELECCIONADA
        # ====================================================

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
            local.strip().lower()
            ==
            equipo.strip().lower()
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

        # ====================================================
        # SOLO LA LIGA SELECCIONADA
        # ====================================================

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
            visitante.strip().lower()
            ==
            equipo.strip().lower()
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
        "LIGA SELECCIONADA:",
        liga
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
    # SE BUSCA SIN FILTRO DE LIGA
    # ========================================================

    h2h = obtener_h2h_directo(
        historial_a,
        id_a,
        id_b,
        fecha_partido
    )

    # ========================================================
    # EQUIPO A - LOCAL
    #
    # AQUÍ SÍ SE FILTRA LA LIGA
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