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

        print(
            "SOFASCORE NO DEVOLVIÓ DATOS"
        )

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

        if tipo == "team":

            candidatos.append(
                entidad
            )

            print(
                "EQUIPO ENCONTRADO:",
                nombre_encontrado,
                "| ID:",
                entidad.get("id")
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

    fecha = obtener_fecha(
        evento
    )

    if not fecha:

        return False

    return (
        fecha.strftime("%Y-%m-%d")
        <
        str(fecha_limite)
    )


# ============================================================
# OBTENER NOMBRE DE LA LIGA
# ============================================================

def obtener_nombre_liga(evento):

    if not evento:

        return ""

    # --------------------------------------------------------
    # uniqueTournament
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # tournament
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # tournament.uniqueTournament
    # --------------------------------------------------------

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
# NORMALIZAR TEXTO
# ============================================================

def normalizar_texto(texto):

    if not texto:

        return ""

    return (
        str(texto)
        .strip()
        .lower()
    )


# ============================================================
# PERTENECE A LA LIGA
# ============================================================

def pertenece_a_liga(
    evento,
    liga
):

    if not evento:

        return False

    liga_buscada = normalizar_texto(
        liga
    )

    liga_evento = normalizar_texto(
        obtener_nombre_liga(evento)
    )

    print(
        "LIGA:",
        repr(liga_evento),
        "| BUSCADA:",
        repr(liga_buscada)
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

        print(
            "EQUIPO",
            team_id,
            "| PÁGINA",
            pagina,
            "| PARTIDOS:",
            len(eventos)
        )

        if not datos.get(
            "hasNextPage",
            False
        ):

            break

        pagina += 1

        # Máximo 20 páginas
        if pagina >= 20:

            break

    print(
        "TOTAL HISTORIAL EQUIPO",
        team_id,
        ":",
        len(partidos)
    )

    return partidos


# ============================================================
# COMPROBAR SI ES H2H
# ============================================================

def es_h2h(
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

    # --------------------------------------------------------
    # IMPORTANTE:
    #
    # No importa quién fue local.
    #
    # {A, B} == {B, A}
    # --------------------------------------------------------

    return {
        home_id,
        away_id
    } == {
        equipo_a_id,
        equipo_b_id
    }


# ============================================================
# BUSCAR H2H EN UN HISTORIAL
# ============================================================

def buscar_h2h_en_historial(
    historial,
    equipo_a_id,
    equipo_b_id,
    liga,
    fecha_limite
):

    encontrados = []

    for evento in historial:

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
        # AMBOS EQUIPOS
        # ----------------------------------------------------

        if not es_h2h(
            evento,
            equipo_a_id,
            equipo_b_id
        ):

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
            "LOCAL:",
            evento
            .get("homeTeam", {})
            .get("name", "")
        )

        print(
            "VISITANTE:",
            evento
            .get("awayTeam", {})
            .get("name", "")
        )

        print(
            "LIGA:",
            obtener_nombre_liga(evento)
        )

        print(
            "ID EVENTO:",
            evento.get("id")
        )

        print(
            "===================================="
        )

        encontrados.append(
            evento
        )

    return encontrados


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
    # BUSCAR EN HISTORIAL A
    # ========================================================

    encontrados.extend(
        buscar_h2h_en_historial(
            historial_a,
            equipo_a_id,
            equipo_b_id,
            liga,
            fecha_limite
        )
    )

    # ========================================================
    # BUSCAR EN HISTORIAL B
    # ========================================================

    encontrados.extend(
        buscar_h2h_en_historial(
            historial_b,
            equipo_a_id,
            equipo_b_id,
            liga,
            fecha_limite
        )
    )

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

    # ========================================================
    # DOS MÁS RECIENTES
    # ========================================================

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
        "===================================="
    )

    print(
        "TOTAL H2H ENCONTRADOS:",
        len(h2h)
    )

    print(
        "===================================="
    )

    # ========================================================
    # EQUIPO A COMO LOCAL
    # ========================================================

    local_a = ultimo_local(
        historial_a,
        id_a,
        fecha_partido,
        liga
    )

    # ========================================================
    # EQUIPO A COMO VISITANTE
    # ========================================================

    visitante_a = ultimo_visitante(
        historial_a,
        id_a,
        fecha_partido,
        liga
    )

    # ========================================================
    # EQUIPO B COMO LOCAL
    # ========================================================

    local_b = ultimo_local(
        historial_b,
        id_b,
        fecha_partido,
        liga
    )

    # ========================================================
    # EQUIPO B COMO VISITANTE
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