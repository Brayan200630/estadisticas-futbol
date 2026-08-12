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

        print("ERROR:", error)

        return None


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
            candidatos.append(
                entidad
            )

    buscado = normalizar_texto(
        nombre
    )

    # Exacta
    for equipo in candidatos:

        encontrado = normalizar_texto(
            equipo.get("name", "")
        )

        if encontrado == buscado:

            print(
                "EQUIPO ENCONTRADO:",
                equipo.get("name"),
                equipo.get("id")
            )

            return equipo

    # Parcial
    for equipo in candidatos:

        encontrado = normalizar_texto(
            equipo.get("name", "")
        )

        if (
            buscado in encontrado
            or
            encontrado in buscado
        ):

            print(
                "EQUIPO ENCONTRADO:",
                equipo.get("name"),
                equipo.get("id")
            )

            return equipo

    print(
        "NO SE ENCONTRÓ:",
        nombre
    )

    return None


# ============================================================
# BUSCAR TORNEO / LIGA
# ============================================================

def buscar_liga(nombre_liga):

    url = (
        f"{BASE_URL}/search/all"
        f"?q={quote(nombre_liga)}"
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

        tipo = resultado.get(
            "type",
            ""
        )

        entidad = resultado.get(
            "entity",
            {}
        )

        if not entidad:
            continue

        # SofaScore puede devolver uniqueTournament
        # como tipo de resultado.
        if tipo in {
            "uniqueTournament",
            "tournament"
        }:

            candidatos.append(
                entidad
            )

    buscado = normalizar_texto(
        nombre_liga
    )

    # Coincidencia exacta
    for liga in candidatos:

        nombre = normalizar_texto(
            liga.get("name", "")
        )

        if nombre == buscado:

            print(
                "LIGA ENCONTRADA:",
                liga.get("name"),
                "| ID:",
                liga.get("id")
            )

            return liga

    # Coincidencia parcial
    for liga in candidatos:

        nombre = normalizar_texto(
            liga.get("name", "")
        )

        if (
            buscado in nombre
            or
            nombre in buscado
        ):

            print(
                "LIGA ENCONTRADA POR COINCIDENCIA:",
                liga.get("name"),
                "| ID:",
                liga.get("id")
            )

            return liga

    print(
        "NO SE ENCONTRÓ LA LIGA:",
        nombre_liga
    )

    return None


# ============================================================
# OBTENER TEMPORADAS DE UNA LIGA
# ============================================================

def obtener_temporadas(tournament_id):

    url = (
        f"{BASE_URL}/unique-tournament/"
        f"{tournament_id}/seasons"
    )

    datos = obtener_json(
        url
    )

    if not datos:
        return []

    temporadas = datos.get(
        "seasons",
        []
    )

    return temporadas


# ============================================================
# CONVERTIR FECHA
# ============================================================

def convertir_fecha(fecha):

    if isinstance(
        fecha,
        datetime
    ):

        return fecha.date()

    if hasattr(
        fecha,
        "strftime"
    ):

        return fecha

    if isinstance(
        fecha,
        str
    ):

        try:

            return datetime.strptime(
                fecha,
                "%Y-%m-%d"
            ).date()

        except Exception:

            return None

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

    if timestamp is None:
        return None

    try:

        return datetime.fromtimestamp(
            int(timestamp)
        )

    except Exception:

        return None


# ============================================================
# FECHA DATE
# ============================================================

def obtener_fecha_date(evento):

    fecha = obtener_fecha(
        evento
    )

    if not fecha:
        return None

    return fecha.date()


# ============================================================
# TIMESTAMP
# ============================================================

def obtener_timestamp(evento):

    if not evento:
        return 0

    try:

        return int(
            evento.get(
                "startTimestamp",
                0
            )
        )

    except Exception:

        return 0


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

    return normalizar_texto(
        status.get(
            "type",
            ""
        )
    )


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

    return es_finalizado(
        evento
    )


# ============================================================
# ANTERIOR A FECHA
# ============================================================

def es_anterior_a_fecha(
    evento,
    fecha_limite
):

    fecha_evento = obtener_fecha_date(
        evento
    )

    fecha_limite = convertir_fecha(
        fecha_limite
    )

    if not fecha_evento:
        return False

    if not fecha_limite:
        return False

    return fecha_evento < fecha_limite


# ============================================================
# OBTENER NOMBRE DE LIGA DEL EVENTO
# ============================================================

def obtener_nombre_liga(evento):

    if not evento:
        return ""

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

            return unique.get(
                "name",
                ""
            )

    return ""


# ============================================================
# ID DE TORNEO DEL EVENTO
# ============================================================

def obtener_tournament_id(evento):

    if not evento:
        return None

    unique = evento.get(
        "uniqueTournament",
        {}
    )

    if isinstance(
        unique,
        dict
    ):

        if unique.get("id"):
            return unique.get("id")

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

            if unique.get("id"):
                return unique.get("id")

        if tournament.get("id"):
            return tournament.get("id")

    return None


# ============================================================
# PERTENECE A LIGA
# ============================================================

def pertenece_a_liga(
    evento,
    liga_id=None,
    liga_nombre=None
):

    if not evento:
        return False

    # Primero ID: es la comprobación más fiable.
    if liga_id is not None:

        evento_liga_id = (
            obtener_tournament_id(
                evento
            )
        )

        try:

            if int(evento_liga_id) == int(liga_id):
                return True

        except Exception:
            pass

    # Respaldo por nombre.
    if liga_nombre:

        evento_nombre = normalizar_texto(
            obtener_nombre_liga(
                evento
            )
        )

        buscada = normalizar_texto(
            liga_nombre
        )

        if evento_nombre == buscada:
            return True

        if (
            buscada in evento_nombre
            or
            evento_nombre in buscada
        ):

            return True

    return False


# ============================================================
# OBTENER EVENTOS DE UNA TEMPORADA
# ============================================================

def obtener_eventos_temporada(
    tournament_id,
    season_id
):

    todos = []

    pagina = 0

    max_paginas = 30

    while pagina < max_paginas:

        # Endpoint de partidos anteriores
        url = (
            f"{BASE_URL}/unique-tournament/"
            f"{tournament_id}/season/"
            f"{season_id}/events/last/"
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
            "TORNEO:",
            tournament_id,
            "| TEMPORADA:",
            season_id,
            "| PAGINA:",
            pagina,
            "| EVENTOS:",
            len(eventos)
        )

        todos.extend(
            eventos
        )

        if not datos.get(
            "hasNextPage",
            False
        ):

            break

        pagina += 1

    # ========================================================
    # DEDUPLICAR
    # ========================================================

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

    todos.sort(
        key=obtener_timestamp,
        reverse=True
    )

    return todos


# ============================================================
# OBTENER TEMPORADA CORRECTA
# ============================================================

def seleccionar_temporada(
    temporadas,
    fecha_partido
):

    fecha = convertir_fecha(
        fecha_partido
    )

    if not fecha:
        return None

    if not temporadas:
        return None

    # ========================================================
    # INTENTAR POR AÑO
    # ========================================================

    candidatas = []

    for temporada in temporadas:

        nombre = str(
            temporada.get(
                "name",
                ""
            )
        )

        year = str(
            temporada.get(
                "year",
                ""
            )
        )

        inicio = (
            temporada.get(
                "startDate"
            )
        )

        fin = (
            temporada.get(
                "endDate"
            )
        )

        # ----------------------------------------------------
        # Si tiene fechas de temporada
        # ----------------------------------------------------

        try:

            if inicio and fin:

                inicio_dt = datetime.fromisoformat(
                    inicio.replace(
                        "Z",
                        "+00:00"
                    )
                ).date()

                fin_dt = datetime.fromisoformat(
                    fin.replace(
                        "Z",
                        "+00:00"
                    )
                ).date()

                if (
                    inicio_dt <= fecha <= fin_dt
                ):

                    return temporada

        except Exception:
            pass

        # ----------------------------------------------------
        # Buscar por año
        # ----------------------------------------------------

        if str(fecha.year) in nombre:
            candidatas.append(
                temporada
            )
            continue

        if str(fecha.year) == year:
            candidatas.append(
                temporada
            )
            continue

        # Temporadas tipo 2025/2026
        if (
            str(fecha.year) in nombre
        ):

            candidatas.append(
                temporada
            )

    if candidatas:

        return candidatas[0]

    # ========================================================
    # ORDENAR POR ID COMO ÚLTIMO RESPALDO
    # ========================================================

    temporadas_ordenadas = sorted(
        temporadas,
        key=lambda x: int(
            x.get(
                "id",
                0
            )
        ),
        reverse=True
    )

    if temporadas_ordenadas:

        return temporadas_ordenadas[0]

    return None


# ============================================================
# OBTENER PARTIDOS DE LA LIGA
# ============================================================

def obtener_partidos_de_liga(
    tournament_id,
    season_id
):

    return obtener_eventos_temporada(
        tournament_id,
        season_id
    )


# ============================================================
# FILTRAR PARTIDOS DEL EQUIPO
# ============================================================

def partidos_del_equipo(
    eventos,
    equipo_id,
    fecha_limite,
    torneo_id
):

    candidatos = []

    for evento in eventos:

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
            liga_id=torneo_id
        ):
            continue

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
            home_id != equipo_id
            and
            away_id != equipo_id
        ):

            continue

        candidatos.append(
            evento
        )

    candidatos.sort(
        key=obtener_timestamp,
        reverse=True
    )

    return candidatos


# ============================================================
# ÚLTIMO LOCAL
# ============================================================

def ultimo_local(
    eventos,
    equipo_id,
    fecha_limite,
    torneo_id
):

    candidatos = []

    for evento in eventos:

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
            liga_id=torneo_id
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
        key=obtener_timestamp,
        reverse=True
    )

    if candidatos:
        return candidatos[0]

    return None


# ============================================================
# ÚLTIMO VISITANTE
# ============================================================

def ultimo_visitante(
    eventos,
    equipo_id,
    fecha_limite,
    torneo_id
):

    candidatos = []

    for evento in eventos:

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
            liga_id=torneo_id
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
        key=obtener_timestamp,
        reverse=True
    )

    if candidatos:
        return candidatos[0]

    return None


# ============================================================
# H2H
# ============================================================

def obtener_h2h(
    eventos,
    equipo_a_id,
    equipo_b_id,
    fecha_limite,
    torneo_id
):

    candidatos = []

    for evento in eventos:

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
            liga_id=torneo_id
        ):
            continue

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

        # ====================================================
        # EXACTAMENTE A VS B
        # ====================================================

        if not (
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
        ):

            continue

        candidatos.append(
            evento
        )

    # ========================================================
    # DEDUPLICAR
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
    # MÁS RECIENTE PRIMERO
    # ========================================================

    candidatos.sort(
        key=obtener_timestamp,
        reverse=True
    )

    print(
        "===================================="
    )

    print(
        "H2H ENCONTRADOS:",
        len(candidatos)
    )

    for evento in candidatos[:10]:

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
            .get("name"),
            "|",
            obtener_nombre_liga(
                evento
            )
        )

    print(
        "===================================="
    )

    return candidatos[:2]


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

            nombre = normalizar_texto(
                item.get(
                    "name",
                    ""
                )
            )

            if nombre:
                estadisticas[nombre] = item

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

    fecha = convertir_fecha(
        fecha_partido
    )

    if not fecha:

        return {
            "error":
            "La fecha indicada no es válida."
        }


    # ========================================================
    # BUSCAR EQUIPOS
    # ========================================================

    equipo_a = buscar_equipo(
        nombre_equipo_a
    )

    if not equipo_a:

        return {
            "error":
            f"No se encontró: {nombre_equipo_a}"
        }


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


    # ========================================================
    # BUSCAR LIGA
    # ========================================================

    torneo = buscar_liga(
        liga
    )

    if not torneo:

        return {
            "error":
            f"No se encontró la liga: {liga}"
        }


    torneo_id = torneo.get(
        "id"
    )

    torneo_nombre = torneo.get(
        "name",
        liga
    )


    print(
        "===================================="
    )

    print(
        "EQUIPO A:",
        nombre_a,
        "|",
        id_a
    )

    print(
        "EQUIPO B:",
        nombre_b,
        "|",
        id_b
    )

    print(
        "TORNEO:",
        torneo_nombre,
        "|",
        torneo_id
    )

    print(
        "FECHA:",
        fecha
    )

    print(
        "===================================="
    )


    # ========================================================
    # TEMPORADAS
    # ========================================================

    temporadas = obtener_temporadas(
        torneo_id
    )

    if not temporadas:

        return {
            "error":
            f"No se encontraron temporadas "
            f"para {torneo_nombre}."
        }


    temporada = seleccionar_temporada(
        temporadas,
        fecha
    )

    if not temporada:

        return {
            "error":
            f"No se pudo determinar la temporada "
            f"de {torneo_nombre} para {fecha}."
        }


    season_id = temporada.get(
        "id"
    )

    season_name = temporada.get(
        "name",
        ""
    )


    print(
        "TEMPORADA:",
        season_name,
        "| ID:",
        season_id
    )


    # ========================================================
    # PARTIDOS DE LA COMPETICIÓN
    # ========================================================

    eventos = obtener_partidos_de_liga(
        torneo_id,
        season_id
    )

    if not eventos:

        return {
            "error":
            "Sofascore no devolvió partidos "
            "para la liga y temporada seleccionadas."
        }


    # ========================================================
    # PARTIDOS EQUIPO A
    # ========================================================

    eventos_a = partidos_del_equipo(
        eventos,
        id_a,
        fecha,
        torneo_id
    )


    # ========================================================
    # PARTIDOS EQUIPO B
    # ========================================================

    eventos_b = partidos_del_equipo(
        eventos,
        id_b,
        fecha,
        torneo_id
    )


    print(
        "PARTIDOS A:",
        len(eventos_a)
    )

    print(
        "PARTIDOS B:",
        len(eventos_b)
    )


    # ========================================================
    # H2H
    # ========================================================

    h2h = obtener_h2h(
        eventos,
        id_a,
        id_b,
        fecha,
        torneo_id
    )


    # ========================================================
    # LOCAL / VISITANTE
    # ========================================================

    local_a = ultimo_local(
        eventos_a,
        id_a,
        fecha,
        torneo_id
    )

    visitante_a = ultimo_visitante(
        eventos_a,
        id_a,
        fecha,
        torneo_id
    )

    local_b = ultimo_local(
        eventos_b,
        id_b,
        fecha,
        torneo_id
    )

    visitante_b = ultimo_visitante(
        eventos_b,
        id_b,
        fecha,
        torneo_id
    )


    # ========================================================
    # DEBUG
    # ========================================================

    print(
        "===================================="
    )

    print(
        "RESULTADO FINAL"
    )

    print(
        "H2H:",
        len(h2h)
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
            torneo_nombre,

        "liga_id":
            torneo_id,

        "temporada":
            season_name,

        "temporada_id":
            season_id,

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