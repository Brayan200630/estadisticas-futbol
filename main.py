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

    nombre_buscado = nombre.strip().lower()

    for equipo in candidatos:

        nombre_encontrado = (
            equipo.get(
                "name",
                ""
            )
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
            equipo.get(
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

    return obtener_estado(evento) in {
        "postponed",
        "delayed"
    }


# ============================================================
# PARTIDO CANCELADO
# ============================================================

def es_cancelado(evento):

    return obtener_estado(evento) in {
        "canceled",
        "cancelled"
    }


# ============================================================
# PARTIDO NO INICIADO
# ============================================================

def es_no_iniciado(evento):

    return obtener_estado(evento) in {
        "scheduled",
        "notstarted",
        "not_started"
    }


# ============================================================
# PARTIDO FINALIZADO
# ============================================================

def es_finalizado(evento):

    estado = obtener_estado(evento)

    if estado in {
        "finished",
        "ended"
    }:
        return True

    # Algunos eventos usan status code 100
    status = evento.get(
        "status",
        {}
    )

    if status.get("code") == 100:
        return True

    return False


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

    if unique.get("name"):

        return unique.get(
            "name"
        )

    # --------------------------------------------------------
    # tournament
    # --------------------------------------------------------

    tournament = evento.get(
        "tournament",
        {}
    )

    if tournament.get("name"):

        return tournament.get(
            "name"
        )

    # --------------------------------------------------------
    # tournament.uniqueTournament
    # --------------------------------------------------------

    unique = tournament.get(
        "uniqueTournament",
        {}
    )

    if unique.get("name"):

        return unique.get(
            "name"
        )

    return ""


# ============================================================
# COMPROBAR LIGA
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

    if not nombre_liga:
        return False

    liga_buscada = (
        liga
        .strip()
        .lower()
    )

    nombre_liga = (
        nombre_liga
        .strip()
        .lower()
    )

    print(
        "LIGA ENCONTRADA:",
        repr(nombre_liga),
        "| LIGA BUSCADA:",
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
# OBTENER HISTORIAL
# ============================================================

def obtener_historial(
    team_id,
    paginas_maximas=20
):

    partidos = []

    pagina = 0

    while pagina < paginas_maximas:

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

    print(
        "TOTAL PARTIDOS HISTORIAL:",
        len(partidos)
    )

    return partidos


# ============================================================
# COMPROBAR SI SON LOS DOS EQUIPOS
# ============================================================

def son_h2h(
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

    # Esto permite ambas orientaciones:
    #
    # A vs B
    # B vs A

    return {
        home_id,
        away_id
    } == {
        equipo_a_id,
        equipo_b_id
    }


# ============================================================
# H2H DESDE HISTORIALES
# ============================================================

def buscar_h2h_en_historiales(
    historial_a,
    historial_b,
    equipo_a_id,
    equipo_b_id,
    liga,
    fecha_limite
):

    encontrados = []

    todos = (
        historial_a
        +
        historial_b
    )

    vistos = set()

    for evento in todos:

        if not evento:
            continue

        event_id = evento.get(
            "id"
        )

        if event_id in vistos:
            continue

        vistos.add(
            event_id
        )

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

        if not partido_valido(
            evento
        ):
            continue

        # ----------------------------------------------------
        # AMBOS EQUIPOS
        # ----------------------------------------------------

        if not son_h2h(
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
            "H2H ENCONTRADO:",
            evento.get("homeTeam", {}).get("name"),
            "vs",
            evento.get("awayTeam", {}).get("name"),
            "| LIGA:",
            obtener_nombre_liga(evento)
        )

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

    return encontrados


# ============================================================
# OBTENER H2H DESDE UN EVENTO
# ============================================================

def obtener_h2h_desde_evento(
    event_id
):

    if not event_id:
        return []

    url = (
        f"{BASE_URL}/event/"
        f"{event_id}/h2h/events"
    )

    datos = obtener_json(
        url
    )

    if not datos:
        return []

    eventos = datos.get(
        "events",
        []
    )

    print(
        "H2H DEL ENDPOINT:",
        len(eventos)
    )

    return eventos


# ============================================================
# BUSCAR H2H
# ============================================================

def obtener_dos_h2h(
    historial_a,
    historial_b,
    equipo_a_id,
    equipo_b_id,
    liga,
    fecha_limite
):

    # ========================================================
    # PRIMER MÉTODO
    #
    # Buscar directamente en los historiales.
    # ========================================================

    encontrados = buscar_h2h_en_historiales(
        historial_a,
        historial_b,
        equipo_a_id,
        equipo_b_id,
        liga,
        fecha_limite
    )

    # ========================================================
    # SEGUNDO MÉTODO
    #
    # Si no encontramos suficientes H2H,
    # usamos los eventos del historial y consultamos
    # el endpoint específico de H2H de Sofascore.
    # ========================================================

    if len(encontrados) < 2:

        candidatos_eventos = (
            historial_a
            +
            historial_b
        )

        candidatos_eventos.sort(
            key=lambda x:
            x.get(
                "startTimestamp",
                0
            ),
            reverse=True
        )

        eventos_consultados = set()

        for evento in candidatos_eventos:

            if not evento:
                continue

            event_id = evento.get(
                "id"
            )

            if not event_id:
                continue

            if event_id in eventos_consultados:
                continue

            eventos_consultados.add(
                event_id
            )

            # Solo tiene sentido consultar H2H
            # desde partidos anteriores.

            if not es_anterior_a_fecha(
                evento,
                fecha_limite
            ):
                continue

            h2h_eventos = obtener_h2h_desde_evento(
                event_id
            )

            for h2h in h2h_eventos:

                if not h2h:
                    continue

                h2h_id = h2h.get(
                    "id"
                )

                if any(
                    x.get("id") == h2h_id
                    for x in encontrados
                ):
                    continue

                if not son_h2h(
                    h2h,
                    equipo_a_id,
                    equipo_b_id
                ):
                    continue

                if not es_anterior_a_fecha(
                    h2h,
                    fecha_limite
                ):
                    continue

                if not partido_valido(
                    h2h
                ):
                    continue

                if not pertenece_a_liga(
                    h2h,
                    liga
                ):
                    continue

                encontrados.append(
                    h2h
                )

                print(
                    "H2H ENCONTRADO POR ENDPOINT:",
                    h2h
                    .get("homeTeam", {})
                    .get("name"),
                    "vs",
                    h2h
                    .get("awayTeam", {})
                    .get("name")
                )

            if len(encontrados) >= 2:
                break

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
    # SOLO LOS DOS MÁS RECIENTES
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
                item.get(
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

    print("====================================")
    print("EQUIPO A:", nombre_a)
    print("ID A:", id_a)
    print("EQUIPO B:", nombre_b)
    print("ID B:", id_b)
    print("LIGA:", liga)
    print("FECHA:", fecha_partido)
    print("====================================")

    # ========================================================
    # HISTORIALES
    # ========================================================

    historial_a = obtener_historial(
        id_a,
        paginas_maximas=20
    )

    historial_b = obtener_historial(
        id_b,
        paginas_maximas=20
    )

    # ========================================================
    # H2H
    #
    # IMPORTANTE:
    #
    # Se comparan los IDs, no los nombres.
    #
    # Por tanto:
    #
    # Universitario vs Alianza
    #
    # y
    #
    # Alianza vs Universitario
    #
    # cuentan como H2H.
    # ========================================================

    h2h = obtener_dos_h2h(
        historial_a,
        historial_b,
        id_a,
        id_b,
        liga,
        fecha_partido
    )

    print(
        "===================================="
    )

    print(
        "H2H FINALES ENCONTRADOS:",
        len(h2h)
    )

    for evento in h2h:

        print(
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

    # ========================================================
    # ÚLTIMO LOCAL EQUIPO A
    # ========================================================

    local_a = ultimo_local(
        historial_a,
        id_a,
        fecha_partido,
        liga
    )

    # ========================================================
    # ÚLTIMO VISITANTE EQUIPO A
    # ========================================================

    visitante_a = ultimo_visitante(
        historial_a,
        id_a,
        fecha_partido,
        liga
    )

    # ========================================================
    # ÚLTIMO LOCAL EQUIPO B
    # ========================================================

    local_b = ultimo_local(
        historial_b,
        id_b,
        fecha_partido,
        liga
    )

    # ========================================================
    # ÚLTIMO VISITANTE EQUIPO B
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