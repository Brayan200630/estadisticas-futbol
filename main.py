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

    for equipo in candidatos:

        nombre_encontrado = equipo.get(
            "name",
            ""
        )

        if (
            nombre_encontrado.strip().lower()
            ==
            nombre.strip().lower()
        ):

            print(
                "COINCIDENCIA EXACTA:",
                nombre_encontrado
            )

            return equipo

    # ========================================================
    # COINCIDENCIA PARCIAL
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
# ESTADOS
# ============================================================

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
# OBTENER LIGA DE UN EVENTO
# ============================================================

def obtener_nombre_liga(evento):

    if not evento:
        return ""

    # Primero uniqueTournament
    torneo = evento.get(
        "uniqueTournament",
        {}
    )

    nombre = torneo.get(
        "name",
        ""
    )

    if nombre:
        return nombre.strip()

    # Segundo tournament
    torneo = evento.get(
        "tournament",
        {}
    )

    nombre = torneo.get(
        "name",
        ""
    )

    if nombre:
        return nombre.strip()

    # Tercero uniqueTournament dentro de tournament
    unique = torneo.get(
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

    nombre_liga = obtener_nombre_liga(
        evento
    )

    liga_buscada = (
        liga.strip().lower()
    )

    liga_evento = (
        nombre_liga.strip().lower()
    )

    print(
        "LIGA ENCONTRADA:",
        repr(nombre_liga),
        "| LIGA BUSCADA:",
        repr(liga)
    )

    if not liga_evento:
        return False

    # Coincidencia exacta
    if liga_evento == liga_buscada:
        return True

    # Coincidencia parcial
    if (
        liga_buscada in liga_evento
        or
        liga_evento in liga_buscada
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

        partidos.extend(
            eventos
        )

        if not datos.get(
            "hasNextPage",
            False
        ):
            break

        pagina += 1

        # Máximo 10 páginas
        if pagina >= 10:
            break

    print(
        "TOTAL PARTIDOS HISTORIAL:",
        len(partidos)
    )

    return partidos


# ============================================================
# OBTENER H2H
#
# IMPORTANTE:
#
# Busca:
#
# EQUIPO A LOCAL vs EQUIPO B
#
# Y también:
#
# EQUIPO B LOCAL vs EQUIPO A
#
# Por lo tanto el orden de localía NO importa.
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
    # COMBINAR HISTORIALES
    # ========================================================

    todos_eventos = (
        historial_a +
        historial_b
    )

    # ========================================================
    # ELIMINAR DUPLICADOS
    # ========================================================

    eventos_unicos = {}

    for evento in todos_eventos:

        event_id = evento.get(
            "id"
        )

        if event_id:

            eventos_unicos[
                event_id
            ] = evento

    todos_eventos = list(
        eventos_unicos.values()
    )

    print(
        "EVENTOS ÚNICOS PARA H2H:",
        len(todos_eventos)
    )

    # ========================================================
    # RECORRER PARTIDOS
    # ========================================================

    for evento in todos_eventos:

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

        home_team = evento.get(
            "homeTeam",
            {}
        )

        away_team = evento.get(
            "awayTeam",
            {}
        )

        home_id = home_team.get(
            "id"
        )

        away_id = away_team.get(
            "id"
        )

        # ----------------------------------------------------
        # NOMBRES
        # ----------------------------------------------------

        home_name = home_team.get(
            "name",
            ""
        )

        away_name = away_team.get(
            "name",
            ""
        )

        # ====================================================
        # COMPROBAR H2H
        #
        # Caso 1:
        # A vs B
        #
        # Caso 2:
        # B vs A
        # ====================================================

        es_h2h = (

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

        if not es_h2h:
            continue

        # ====================================================
        # COMPROBAR LIGA
        # ====================================================

        nombre_liga = obtener_nombre_liga(
            evento
        )

        print(
            "===================================="
        )

        print(
            "H2H ENCONTRADO:"
        )

        print(
            home_name,
            "vs",
            away_name
        )

        print(
            "LIGA DEL PARTIDO:",
            repr(nombre_liga)
        )

        print(
            "LIGA BUSCADA:",
            repr(liga)
        )

        # ====================================================
        # FILTRO LIGA
        # ====================================================

        if not pertenece_a_liga(
            evento,
            liga
        ):
            print(
                "H2H DESCARTADO POR LIGA"
            )
            continue

        # ====================================================
        # GUARDAR
        # ====================================================

        encontrados.append(
            evento
        )

    # ========================================================
    # ORDENAR POR FECHA
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
        "H2H FINALES ENCONTRADOS:",
        len(encontrados)
    )

    for evento in encontrados[:2]:

        home = evento.get(
            "homeTeam",
            {}
        ).get(
            "name",
            ""
        )

        away = evento.get(
            "awayTeam",
            {}
        ).get(
            "name",
            ""
        )

        print(
            "H2H:",
            home,
            "vs",
            away
        )

    print(
        "===================================="
    )

    # Solo los 2 últimos
    return encontrados[:2]


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

        local_id = (
            evento
            .get("homeTeam", {})
            .get("id")
        )

        if local_id != equipo_id:
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

        visitante_id = (
            evento
            .get("awayTeam", {})
            .get("id")
        )

        if visitante_id != equipo_id:
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
        "name"
    )

    nombre_b = equipo_b.get(
        "name"
    )

    print(
        "===================================="
    )

    print(
        "ANÁLISIS"
    )

    print(
        "Equipo A:",
        nombre_a,
        "| ID:",
        id_a
    )

    print(
        "Equipo B:",
        nombre_b,
        "| ID:",
        id_b
    )

    print(
        "Liga:",
        liga
    )

    print(
        "Fecha:",
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
    # AQUÍ SE BUSCAN:
    #
    # A LOCAL vs B
    #
    # B LOCAL vs A
    # ========================================================

    h2h = obtener_h2h(
        historial_a,
        historial_b,
        id_a,
        id_b,
        fecha_partido,
        liga
    )

    # ========================================================
    # EQUIPO A LOCAL
    # ========================================================

    local_a = ultimo_local(
        historial_a,
        id_a,
        fecha_partido,
        liga
    )

    # ========================================================
    # EQUIPO A VISITANTE
    # ========================================================

    visitante_a = ultimo_visitante(
        historial_a,
        id_a,
        fecha_partido,
        liga
    )

    # ========================================================
    # EQUIPO B LOCAL
    # ========================================================

    local_b = ultimo_local(
        historial_b,
        id_b,
        fecha_partido,
        liga
    )

    # ========================================================
    # EQUIPO B VISITANTE
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