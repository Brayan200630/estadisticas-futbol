from curl_cffi import requests
from datetime import datetime
from urllib.parse import quote

# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_URL = "https://www.sofascore.com/api/v1"

# No buscar partidos anteriores a esta fecha
FECHA_MINIMA = datetime.strptime(
    "2020-01-01",
    "%Y-%m-%d"
).date()

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
# BUSCAR EQUIPOS
# ============================================================

def buscar_equipos(texto):

    texto = str(
        texto
    ).strip()

    if not texto:
        return []

    url = (
        f"{BASE_URL}/search/all"
        f"?q={quote(texto)}"
    )

    datos = obtener_json(
        url
    )

    if not datos:
        return []

    resultados = datos.get(
        "results",
        []
    )

    equipos = []

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

        equipo_id = entidad.get(
            "id"
        )

        nombre = entidad.get(
            "name"
        )

        if not equipo_id or not nombre:
            continue

        country = entidad.get(
            "country",
            {}
        )

        if isinstance(
            country,
            dict
        ):

            country_name = country.get(
                "name",
                ""
            )

        else:

            country_name = ""

        equipos.append({

            "id":
                equipo_id,

            "name":
                nombre,

            "slug":
                entidad.get(
                    "slug",
                    ""
                ),

            "country":
                country_name

        })

    # ========================================================
    # ELIMINAR DUPLICADOS
    # ========================================================

    unicos = {}

    for equipo in equipos:

        equipo_id = equipo.get(
            "id"
        )

        if equipo_id:

            unicos[
                equipo_id
            ] = equipo

    return list(
        unicos.values()
    )


# ============================================================
# BUSCAR LIGAS / COMPETICIONES
# ============================================================

def buscar_ligas(texto):

    texto = str(
        texto
    ).strip()

    resultados_finales = []

    # ========================================================
    # TODAS LAS COMPETICIONES
    # ========================================================

    resultados_finales.append({

        "id":
            None,

        "name":
            "🌎 Todas las competiciones",

        "slug":
            ""

    })

    # ========================================================
    # SI NO SE ESCRIBIÓ NADA
    # ========================================================

    if not texto:

        return resultados_finales

    # ========================================================
    # BUSCAR EN SOFASCORE
    # ========================================================

    url = (
        f"{BASE_URL}/search/all"
        f"?q={quote(texto)}"
    )

    datos = obtener_json(
        url
    )

    if not datos:

        return resultados_finales

    resultados = datos.get(
        "results",
        []
    )

    ligas = []

    for resultado in resultados:

        tipo = resultado.get(
            "type",
            ""
        )

        if tipo not in {
            "uniqueTournament",
            "tournament"
        }:

            continue

        entidad = resultado.get(
            "entity",
            {}
        )

        if not entidad:
            continue

        tournament_id = entidad.get(
            "id"
        )

        nombre = entidad.get(
            "name"
        )

        if not tournament_id:
            continue

        if not nombre:
            continue

        ligas.append({

            "id":
                tournament_id,

            "name":
                nombre,

            "slug":
                entidad.get(
                    "slug",
                    ""
                )

        })

    # ========================================================
    # ELIMINAR DUPLICADOS
    # ========================================================

    unicos = {}

    for liga in ligas:

        liga_id = liga.get(
            "id"
        )

        if liga_id:

            unicos[
                liga_id
            ] = liga

    resultados_finales.extend(
        unicos.values()
    )

    return resultados_finales


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

        return datetime.fromtimestamp(
            int(timestamp)
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

def convertir_fecha_limite(
    fecha_limite
):

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

    # No aceptar partidos del mismo día
    # ni posteriores.

    if fecha_evento >= fecha_limite_date:
        return False

    # No aceptar partidos anteriores a 2020.

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
# OBTENER NOMBRE DE LIGA
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

            nombre = unique.get(
                "name",
                ""
            )

            if nombre:
                return nombre

    return ""


# ============================================================
# DETECTAR PARTIDOS AMISTOSOS
# ============================================================

def es_amistoso(evento):

    if not evento:
        return False

    nombre_liga = normalizar_texto(
        obtener_nombre_liga(
            evento
        )
    )

    if not nombre_liga:
        return False

    amistosos = {

        "club friendly games",
        "club friendlies",
        "friendly games",
        "friendly match",
        "international friendlies",
        "international friendly games",
        "international friendly",
        "amistosos",
        "amistoso"

    }

    if nombre_liga in amistosos:

        return True

    palabras_amistoso = [

        "friendly",
        "friendlies",
        "amistoso",
        "amistosos"

    ]

    for palabra in palabras_amistoso:

        if palabra in nombre_liga:

            return True

    return False


# ============================================================
# PARTIDO VÁLIDO
#
# FILTRA:
#
# - Solo finalizados
# - Solo desde 01/01/2020
# - Nunca amistosos
# ============================================================

def partido_valido(evento):

    if not evento:
        return False

    if not es_finalizado(
        evento
    ):

        return False

    if es_amistoso(
        evento
    ):

        return False

    fecha = obtener_fecha_date(
        evento
    )

    if not fecha:
        return False

    if fecha < FECHA_MINIMA:
        return False

    return True


# ============================================================
# OBTENER UNIQUE TOURNAMENT ID
# ============================================================

def obtener_unique_tournament_id(evento):

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

        tournament_id = unique.get(
            "id"
        )

        if tournament_id:

            return tournament_id

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

            if tournament_id:

                return tournament_id

    return None


# ============================================================
# OBTENER COMPETICIÓN DE UN EVENTO
# ============================================================

def obtener_competicion(evento):

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

        tournament_id = unique.get(
            "id"
        )

        nombre = unique.get(
            "name",
            ""
        )

        if tournament_id:

            return {

                "id":
                    tournament_id,

                "name":
                    nombre

            }

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

            nombre = unique.get(
                "name",
                ""
            )

            if tournament_id:

                return {

                    "id":
                        tournament_id,

                    "name":
                        nombre

                }

    return None


# ============================================================
# COMPROBAR COMPETICIÓN POR ID
# ============================================================

def pertenece_a_competicion(
    evento,
    tournament_id
):

    if tournament_id is None:

        return True

    competicion = obtener_competicion(
        evento
    )

    if not competicion:

        return False

    return (
        competicion.get("id")
        ==
        tournament_id
    )


# ============================================================
# COMPROBAR LIGA POR NOMBRE
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

    if liga_buscada in {
        "todas",
        "todas las competiciones",
        "🌎 todas las competiciones"
    }:

        return (
            not es_amistoso(
                evento
            )
        )

    nombre_liga = normalizar_texto(
        obtener_nombre_liga(
            evento
        )
    )

    if not nombre_liga:
        return False

    if not liga_buscada:
        return False

    if nombre_liga == liga_buscada:

        return True

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
# OBTENER PRÓXIMOS PARTIDOS
# ============================================================

def obtener_proximos_partidos(
    team_id,
    paginas=3
):

    partidos = []

    for pagina in range(
        paginas
    ):

        url = (
            f"{BASE_URL}/team/"
            f"{team_id}/events/next/"
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

    return ordenar_por_fecha_asc(
        partidos
    )


# ============================================================
# ORDENAR MÁS RECIENTE
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
# ORDENAR MÁS PRÓXIMO
# ============================================================

def ordenar_por_fecha_asc(eventos):

    eventos = eliminar_duplicados(
        eventos
    )

    eventos.sort(
        key=lambda evento:
        evento.get(
            "startTimestamp",
            0
        )
    )

    return eventos


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

            unicos[
                event_id
            ] = evento

    return list(
        unicos.values()
    )


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
# IDENTIFICAR TORNEO REAL DE LA LIGA
# ============================================================

def obtener_tournament_id_de_liga(
    historial_a,
    historial_b,
    liga,
    fecha_limite
):

    liga_normalizada = normalizar_texto(
        liga
    )

    if liga_normalizada in {
        "todas",
        "todas las competiciones",
        "🌎 todas las competiciones"
    }:

        return None

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

        if fecha_evento >= fecha_limite:
            continue

        if fecha_evento < FECHA_MINIMA:
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

        tournament_id = (
            obtener_unique_tournament_id(
                evento
            )
        )

        if tournament_id:

            candidatos.append(
                (
                    fecha_evento,
                    tournament_id,
                    obtener_nombre_liga(
                        evento
                    )
                )
            )

    candidatos.sort(
        key=lambda x: x[0],
        reverse=True
    )

    if candidatos:

        fecha, tournament_id, nombre_liga = (
            candidatos[0]
        )

        print(
            "===================================="
        )

        print(
            "TORNEO DETECTADO"
        )

        print(
            "Nombre:",
            nombre_liga
        )

        print(
            "Tournament ID:",
            tournament_id
        )

        print(
            "Fecha:",
            fecha
        )

        print(
            "===================================="
        )

        return tournament_id

    print(
        "NO SE PUDO IDENTIFICAR "
        "EL UNIQUE TOURNAMENT DE:",
        liga
    )

    return None


# ============================================================
# H2H POR LOCALÍA
# ============================================================

def obtener_h2h_por_localia(
    historial_a,
    historial_b,
    equipo_a_id,
    equipo_b_id,
    liga,
    fecha_limite
):

    liga_normalizada = normalizar_texto(
        liga
    )

    modo_todas = liga_normalizada in {
        "todas",
        "todas las competiciones",
        "🌎 todas las competiciones"
    }

    if modo_todas:

        tournament_id_objetivo = None

    else:

        tournament_id_objetivo = (
            obtener_tournament_id_de_liga(
                historial_a,
                historial_b,
                liga,
                fecha_limite
            )
        )

        if tournament_id_objetivo is None:

            return (
                None,
                None
            )

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

        if not es_enfrentamiento(
            evento,
            equipo_a_id,
            equipo_b_id
        ):

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

        if modo_todas:

            pass

        else:

            tournament_id_evento = (
                obtener_unique_tournament_id(
                    evento
                )
            )

            if (
                tournament_id_evento
                !=
                tournament_id_objetivo
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

    print(
        "===================================="
    )

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

        if not partido_valido(
            evento
        ):

            continue

        if not es_fecha_valida(
            evento,
            fecha_limite
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

    candidatos = ordenar_por_fecha(
        candidatos
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

        return candidatos[0]

    return None


# ============================================================
# OBTENER PRÓXIMO PARTIDO DEL EQUIPO
# ============================================================

def obtener_proximo_partido_equipo(
    proximos,
    equipo_id,
    fecha_limite,
    liga
):

    fecha_limite = convertir_fecha_limite(
        fecha_limite
    )

    candidatos = []

    for evento in proximos:

        if not evento:
            continue

        fecha_evento = obtener_fecha_date(
            evento
        )

        if not fecha_evento:
            continue

        # El próximo partido debe ser
        # igual o posterior a la fecha límite.

        if fecha_evento < fecha_limite:
            continue

        if es_amistoso(
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

        away_id = (
            evento
            .get("awayTeam", {})
            .get("id")
        )

        if equipo_id not in {
            home_id,
            away_id
        }:

            continue

        candidatos.append(
            evento
        )

    candidatos = ordenar_por_fecha_asc(
        candidatos
    )

    if candidatos:

        return candidatos[0]

    return None


# ============================================================
# PRÓXIMO H2H ENTRE AMBOS
# ============================================================

def obtener_proximo_h2h(
    proximos_a,
    equipo_a_id,
    equipo_b_id,
    fecha_limite,
    liga
):

    fecha_limite = convertir_fecha_limite(
        fecha_limite
    )

    candidatos = []

    for evento in proximos_a:

        if not evento:
            continue

        fecha_evento = obtener_fecha_date(
            evento
        )

        if not fecha_evento:
            continue

        if fecha_evento < fecha_limite:
            continue

        if es_amistoso(
            evento
        ):

            continue

        if not es_enfrentamiento(
            evento,
            equipo_a_id,
            equipo_b_id
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

    candidatos = ordenar_por_fecha_asc(
        candidatos
    )

    if candidatos:

        return candidatos[0]

    return None


# ============================================================
# OBTENER DETALLES DE PARTIDO
# ============================================================

def obtener_detalles_partido(
    evento
):

    if not evento:
        return None

    event_id = evento.get(
        "id"
    )

    if not event_id:
        return None

    url = (
        f"{BASE_URL}/event/"
        f"{event_id}"
    )

    datos = obtener_json(
        url
    )

    if datos:

        detalle = datos.get(
            "event"
        )

        if detalle:

            return detalle

    return evento


# ============================================================
# OBTENER ALINEACIONES
# ============================================================

def obtener_alineaciones(
    evento
):

    resultado = {

        "available":
            False,

        "confirmed":
            False,

        "home":
            None,

        "away":
            None

    }

    if not evento:
        return resultado

    event_id = evento.get(
        "id"
    )

    if not event_id:
        return resultado

    url = (
        f"{BASE_URL}/event/"
        f"{event_id}/lineups"
    )

    datos = obtener_json(
        url
    )

    if not datos:
        return resultado

    home = datos.get(
        "home"
    )

    away = datos.get(
        "away"
    )

    if not home and not away:
        return resultado

    resultado["available"] = True

    resultado["confirmed"] = bool(
        datos.get(
            "confirmed",
            False
        )
    )

    resultado["home"] = (
        procesar_alineacion_equipo(
            home
        )
        if home
        else None
    )

    resultado["away"] = (
        procesar_alineacion_equipo(
            away
        )
        if away
        else None
    )

    return resultado


# ============================================================
# PROCESAR ALINEACIÓN
# ============================================================

def procesar_alineacion_equipo(
    equipo
):

    if not equipo:
        return None

    jugadores = equipo.get(
        "players",
        []
    )

    titulares = []
    suplentes = []

    for item in jugadores:

        jugador = item.get(
            "player",
            {}
        )

        if not jugador:
            continue

        nombre = jugador.get(
            "name",
            "Desconocido"
        )

        numero = (
            item.get(
                "shirtNumber"
            )
            or
            jugador.get(
                "jerseyNumber"
            )
        )

        posicion = jugador.get(
            "position",
            ""
        )

        titular = item.get(
            "substitute"
        )

        entrada = {

            "name":
                nombre,

            "number":
                numero,

            "position":
                posicion,

            "substitute":
                bool(titular),

            "statistics":
                item.get(
                    "statistics",
                    {}
                )

        }

        if titular:

            suplentes.append(
                entrada
            )

        else:

            titulares.append(
                entrada
            )

    return {

        "formation":
            equipo.get(
                "formation"
            ),

        "titulares":
            titulares,

        "suplentes":
            suplentes

    }


# ============================================================
# OBTENER INCIDENTES
#
# GOLES
# TARJETAS
# CAMBIOS
# ============================================================

def obtener_incidentes(
    evento
):

    resultado = {

        "goles": [],
        "tarjetas": [],
        "cambios": []

    }

    if not evento:
        return resultado

    event_id = evento.get(
        "id"
    )

    if not event_id:
        return resultado

    url = (
        f"{BASE_URL}/event/"
        f"{event_id}/incidents"
    )

    datos = obtener_json(
        url
    )

    if not datos:
        return resultado

    incidentes = datos.get(
        "incidents",
        []
    )

    for incidente in incidentes:

        tipo = incidente.get(
            "incidentType",
            ""
        )

        # ====================================================
        # GOLES
        # ====================================================

        if tipo == "goal":

            jugador = incidente.get(
                "player",
                {}
            )

            asistencia = incidente.get(
                "assist1",
                {}
            )

            gol = {

                "minuto":
                    incidente.get(
                        "time"
                    ),

                "tiempo_adicional":
                    incidente.get(
                        "addedTime"
                    ),

                "equipo":
                    (
                        "Local"
                        if incidente.get(
                            "isHome"
                        )
                        else "Visitante"
                    ),

                "jugador":
                    jugador.get(
                        "name"
                    ),

                "asistencia":
                    asistencia.get(
                        "name"
                    )
                    if asistencia
                    else None,

                "tipo":
                    incidente.get(
                        "incidentClass",
                        ""
                    )

            }

            resultado[
                "goles"
            ].append(
                gol
            )

        # ====================================================
        # TARJETAS
        # ====================================================

        elif tipo in {
            "card",
            "yellowCard",
            "redCard"
        }:

            jugador = incidente.get(
                "player",
                {}
            )

            tarjeta = {

                "minuto":
                    incidente.get(
                        "time"
                    ),

                "jugador":
                    jugador.get(
                        "name"
                    ),

                "clase":
                    incidente.get(
                        "incidentClass",
                        ""
                    ),

                "equipo":
                    (
                        "Local"
                        if incidente.get(
                            "isHome"
                        )
                        else "Visitante"
                    )

            }

            resultado[
                "tarjetas"
            ].append(
                tarjeta
            )

        # ====================================================
        # SUSTITUCIONES
        # ====================================================

        elif tipo == "substitution":

            jugador_sale = incidente.get(
                "playerOut",
                {}
            )

            jugador_entra = incidente.get(
                "playerIn",
                {}
            )

            cambio = {

                "minuto":
                    incidente.get(
                        "time"
                    ),

                "sale":
                    jugador_sale.get(
                        "name"
                    ),

                "entra":
                    jugador_entra.get(
                        "name"
                    ),

                "equipo":
                    (
                        "Local"
                        if incidente.get(
                            "isHome"
                        )
                        else "Visitante"
                    )

            }

            resultado[
                "cambios"
            ].append(
                cambio
            )

    return resultado


# ============================================================
# OBTENER ENTRENADORES
# ============================================================

def obtener_entrenadores(
    evento
):

    resultado = {

        "home":
            None,

        "away":
            None

    }

    if not evento:
        return resultado

    event_id = evento.get(
        "id"
    )

    if not event_id:
        return resultado

    url = (
        f"{BASE_URL}/event/"
        f"{event_id}/managers"
    )

    datos = obtener_json(
        url
    )

    if not datos:
        return resultado

    home = datos.get(
        "homeManager"
    )

    away = datos.get(
        "awayManager"
    )

    if isinstance(
        home,
        dict
    ):

        jugador = home.get(
            "name"
        )

        if jugador:

            resultado[
                "home"
            ] = jugador

        else:

            player = home.get(
                "player",
                {}
            )

            if isinstance(
                player,
                dict
            ):

                resultado[
                    "home"
                ] = player.get(
                    "name"
                )

    if isinstance(
        away,
        dict
    ):

        jugador = away.get(
            "name"
        )

        if jugador:

            resultado[
                "away"
            ] = jugador

        else:

            player = away.get(
                "player",
                {}
            )

            if isinstance(
                player,
                dict
            ):

                resultado[
                    "away"
                ] = player.get(
                    "name"
                )

    return resultado


# ============================================================
# OBTENER INFORMACIÓN COMPLETA DE PARTIDO
# ============================================================

def obtener_informacion_completa(
    evento
):

    if not evento:
        return None

    detalles = obtener_detalles_partido(
        evento
    )

    alineaciones = obtener_alineaciones(
        detalles
    )

    incidentes = obtener_incidentes(
        detalles
    )

    entrenadores = obtener_entrenadores(
        detalles
    )

    return {

        "evento":
            detalles,

        "alineaciones":
            alineaciones,

        "incidentes":
            incidentes,

        "entrenadores":
            entrenadores

    }


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
# ENRIQUECER PARTIDO
#
# Esta función NO reemplaza las estadísticas anteriores.
# Solo añade:
#
# - goles
# - alineaciones
# - suplentes
# - cambios
# - tarjetas
# - entrenadores
# ============================================================

def enriquecer_partido(
    evento
):

    if not evento:
        return None

    informacion = obtener_informacion_completa(
        evento
    )

    if not informacion:

        return evento

    nuevo = dict(
        evento
    )

    nuevo[
        "detalles_completos"
    ] = informacion.get(
        "evento"
    )

    nuevo[
        "alineaciones"
    ] = informacion.get(
        "alineaciones"
    )

    nuevo[
        "incidentes"
    ] = informacion.get(
        "incidentes"
    )

    nuevo[
        "entrenadores"
    ] = informacion.get(
        "entrenadores"
    )

    return nuevo


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

    liga_normalizada = normalizar_texto(
        liga
    )

    modo_todas = liga_normalizada in {
        "todas",
        "todas las competiciones",
        "🌎 todas las competiciones"
    }

    if not modo_todas:

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
        fecha_partido_str
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
    # ÚLTIMO PARTIDO A LOCAL
    # ========================================================

    local_a = ultimo_local(
        historial_a,
        id_a,
        fecha_limite,
        liga
    )

    # ========================================================
    # ÚLTIMO PARTIDO A VISITANTE
    # ========================================================

    visitante_a = ultimo_visitante(
        historial_a,
        id_a,
        fecha_limite,
        liga
    )

    # ========================================================
    # ÚLTIMO PARTIDO B LOCAL
    # ========================================================

    local_b = ultimo_local(
        historial_b,
        id_b,
        fecha_limite,
        liga
    )

    # ========================================================
    # ÚLTIMO PARTIDO B VISITANTE
    # ========================================================

    visitante_b = ultimo_visitante(
        historial_b,
        id_b,
        fecha_limite,
        liga
    )

    # ========================================================
    # ENRIQUECER PARTIDOS HISTÓRICOS
    # ========================================================

    if h2h_a_local:

        h2h_a_local = enriquecer_partido(
            h2h_a_local
        )

    if h2h_a_visitante:

        h2h_a_visitante = enriquecer_partido(
            h2h_a_visitante
        )

    if local_a:

        local_a = enriquecer_partido(
            local_a
        )

    if visitante_a:

        visitante_a = enriquecer_partido(
            visitante_a
        )

    if local_b:

        local_b = enriquecer_partido(
            local_b
        )

    if visitante_b:

        visitante_b = enriquecer_partido(
            visitante_b
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
    # PRÓXIMOS PARTIDOS
    # ========================================================

    print(
        "BUSCANDO PRÓXIMOS PARTIDOS..."
    )

    proximos_a = obtener_proximos_partidos(
        id_a
    )

    proximos_b = obtener_proximos_partidos(
        id_b
    )

    # ========================================================
    # PRÓXIMO PARTIDO DE A
    # ========================================================

    proximo_a = obtener_proximo_partido_equipo(
        proximos_a,
        id_a,
        fecha_limite,
        liga
    )

    # ========================================================
    # PRÓXIMO PARTIDO DE B
    # ========================================================

    proximo_b = obtener_proximo_partido_equipo(
        proximos_b,
        id_b,
        fecha_limite,
        liga
    )

    # ========================================================
    # PRÓXIMO H2H
    # ========================================================

    proximo_h2h = obtener_proximo_h2h(
        proximos_a,
        id_a,
        id_b,
        fecha_limite,
        liga
    )

    # ========================================================
    # ENRIQUECER PRÓXIMOS PARTIDOS
    #
    # Si todavía no hay alineación,
    # alineaciones quedará disponible=False.
    # ========================================================

    if proximo_a:

        proximo_a = enriquecer_partido(
            proximo_a
        )

    if proximo_b:

        proximo_b = enriquecer_partido(
            proximo_b
        )

    if proximo_h2h:

        proximo_h2h = enriquecer_partido(
            proximo_h2h
        )

    # ========================================================
    # DEBUG
    # ========================================================

    print(
        "===================================="
    )

    print(
        "PRÓXIMO H2H:"
    )

    if proximo_h2h:

        print(
            obtener_fecha(
                proximo_h2h
            ),
            "|",
            proximo_h2h
            .get("homeTeam", {})
            .get("name"),
            "vs",
            proximo_h2h
            .get("awayTeam", {})
            .get("name"),
            "|",
            obtener_nombre_liga(
                proximo_h2h
            )
        )

    else:

        print(
            "NO ENCONTRADO"
        )

    print(
        "PRÓXIMO A:"
    )

    if proximo_a:

        print(
            obtener_fecha(
                proximo_a
            ),
            "|",
            proximo_a
            .get("homeTeam", {})
            .get("name"),
            "vs",
            proximo_a
            .get("awayTeam", {})
            .get("name")
        )

    else:

        print(
            "NO ENCONTRADO"
        )

    print(
        "PRÓXIMO B:"
    )

    if proximo_b:

        print(
            obtener_fecha(
                proximo_b
            ),
            "|",
            proximo_b
            .get("homeTeam", {})
            .get("name"),
            "vs",
            proximo_b
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
    # RESULTADO FINAL
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

        # ----------------------------------------------------
        # H2H EXISTENTE
        # ----------------------------------------------------

        "h2h":
            h2h,

        "h2h_a_local":
            h2h_a_local,

        "h2h_a_visitante":
            h2h_a_visitante,

        # ----------------------------------------------------
        # ÚLTIMOS PARTIDOS
        # ----------------------------------------------------

        "local_a":
            local_a,

        "visitante_a":
            visitante_a,

        "local_b":
            local_b,

        "visitante_b":
            visitante_b,

        # ----------------------------------------------------
        # NUEVO: PRÓXIMOS PARTIDOS
        # ----------------------------------------------------

        "proximo_h2h":
            proximo_h2h,

        "proximo_a":
            proximo_a,

        "proximo_b":
            proximo_b

    }