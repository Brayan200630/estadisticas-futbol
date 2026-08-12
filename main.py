# ============================================================
# MAIN.PY
# ============================================================

from datetime import datetime, date
from curl_cffi import requests
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

        if respuesta.status_code != 200:
            return None

        return respuesta.json()

    except Exception:

        return None


# ============================================================
# BUSCAR EQUIPO
# ============================================================

def buscar_equipo(nombre):

    if not nombre:
        return None

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

    equipos = []

    for resultado in resultados:

        if resultado.get("type") != "team":
            continue

        entidad = resultado.get(
            "entity",
            {}
        )

        if not entidad:
            continue

        equipo_id = entidad.get("id")
        nombre_equipo = entidad.get("name")

        if not equipo_id or not nombre_equipo:
            continue

        pais = ""

        country = entidad.get(
            "country",
            {}
        )

        if isinstance(country, dict):

            pais = country.get(
                "name",
                ""
            )

        equipos.append(
            {
                "id": equipo_id,
                "name": nombre_equipo,
                "country": pais
            }
        )

    if not equipos:
        return None

    # ========================================================
    # INTENTAR COINCIDENCIA EXACTA
    # ========================================================

    nombre_lower = nombre.strip().lower()

    for equipo in equipos:

        if (
            equipo["name"]
            .strip()
            .lower()
            == nombre_lower
        ):

            return equipo

    # ========================================================
    # COINCIDENCIA CONTENIDA
    # ========================================================

    for equipo in equipos:

        nombre_resultado = (
            equipo["name"]
            .strip()
            .lower()
        )

        if (
            nombre_lower in nombre_resultado
            or
            nombre_resultado in nombre_lower
        ):

            return equipo

    return equipos[0]


# ============================================================
# OBTENER EVENTO POR ID
# ============================================================

def obtener_evento(event_id):

    if not event_id:
        return None

    url = (
        f"{BASE_URL}/event/"
        f"{event_id}"
    )

    datos = obtener_json(url)

    if not datos:
        return None

    evento = datos.get(
        "event"
    )

    return evento


# ============================================================
# OBTENER ESTADÍSTICAS DE EVENTO
# ============================================================

def obtener_estadisticas(evento):

    if not evento:
        return {}

    event_id = evento.get(
        "id"
    )

    if not event_id:
        return {}

    url = (
        f"{BASE_URL}/event/"
        f"{event_id}/statistics"
    )

    datos = obtener_json(url)

    if not datos:
        return {}

    bloques = datos.get(
        "statistics",
        []
    )

    bloque_all = None

    # ========================================================
    # BUSCAR PERÍODO COMPLETO
    # ========================================================

    for bloque in bloques:

        if bloque.get("period") == "ALL":

            bloque_all = bloque
            break

    if not bloque_all and bloques:

        bloque_all = bloques[0]

    if not bloque_all:
        return {}

    resultado = {}

    grupos = bloque_all.get(
        "groups",
        []
    )

    # ========================================================
    # MAPEO DE ESTADÍSTICAS
    # ========================================================

    nombres = {
        "Ball possession": "Posesión",
        "Corner kicks": "Córners",
        "Fouls": "Faltas",
        "Yellow cards": "Tarjetas amarillas",
        "Shots on target": "Tiros a puerta",
        "Offsides": "Fueras de juego"
    }

    # También aceptamos algunas variantes.
    variantes = {
        "Ball possession": [
            "Ball possession",
            "Possession"
        ],
        "Corner kicks": [
            "Corner kicks",
            "Corners"
        ],
        "Fouls": [
            "Fouls"
        ],
        "Yellow cards": [
            "Yellow cards"
        ],
        "Shots on target": [
            "Shots on target"
        ],
        "Offsides": [
            "Offsides"
        ]
    }

    for grupo in grupos:

        items = grupo.get(
            "statisticsItems",
            []
        )

        for item in items:

            nombre = item.get(
                "name",
                ""
            )

            key = item.get(
                "key",
                ""
            )

            nombre_detectado = None

            for clave, lista in variantes.items():

                if (
                    nombre in lista
                    or
                    key in [
                        "ballPossession",
                        "cornerKicks",
                        "fouls",
                        "yellowCards",
                        "shotsOnTarget",
                        "offsides"
                    ]
                ):

                    nombre_detectado = clave
                    break

            if not nombre_detectado:
                continue

            nombre_final = nombres[
                nombre_detectado
            ]

            home = item.get(
                "home"
            )

            away = item.get(
                "away"
            )

            if home is None:
                home = item.get(
                    "homeValue"
                )

            if away is None:
                away = item.get(
                    "awayValue"
                )

            if home is None or away is None:
                continue

            resultado[
                nombre_final
            ] = [
                str(home),
                str(away)
            ]

    return resultado


# ============================================================
# OBTENER INCIDENTES
# ============================================================

def obtener_incidentes(evento):

    if not evento:
        return []

    event_id = evento.get(
        "id"
    )

    if not event_id:
        return []

    url = (
        f"{BASE_URL}/event/"
        f"{event_id}/incidents"
    )

    datos = obtener_json(url)

    if not datos:
        return []

    return datos.get(
        "incidents",
        []
    )


# ============================================================
# OBTENER ALINEACIONES
# ============================================================

def obtener_lineups(evento):

    if not evento:
        return {}

    event_id = evento.get(
        "id"
    )

    if not event_id:
        return {}

    url = (
        f"{BASE_URL}/event/"
        f"{event_id}/lineups"
    )

    datos = obtener_json(url)

    if not datos:
        return {}

    return datos


# ============================================================
# IDENTIFICAR POSICIÓN
# ============================================================

def obtener_posicion_jugador(jugador):

    position = jugador.get(
        "position"
    )

    if not position:
        return ""

    mapa = {
        "G": "G",
        "D": "D",
        "M": "M",
        "F": "F",

        "GK": "G",
        "DF": "D",
        "MF": "M",
        "FW": "F"
    }

    return mapa.get(
        position,
        position
    )


# ============================================================
# NORMALIZAR ALINEACIONES
# ============================================================

def normalizar_lineups(
    evento,
    lineups
):

    if not lineups:
        return []

    resultado = []

    home_team = evento.get(
        "homeTeam",
        {}
    )

    away_team = evento.get(
        "awayTeam",
        {}
    )

    lados = [
        (
            "home",
            home_team
        ),
        (
            "away",
            away_team
        )
    ]

    for lado, equipo in lados:

        alineacion = lineups.get(
            lado,
            {}
        )

        if not alineacion:
            continue

        nombre_equipo = equipo.get(
            "name",
            "Desconocido"
        )

        formacion = alineacion.get(
            "formation"
        )

        jugadores = alineacion.get(
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

            nombre = jugador.get(
                "name"
            )

            if not nombre:
                continue

            numero = item.get(
                "shirtNumber"
            )

            posicion = obtener_posicion_jugador(
                item
            )

            texto = ""

            if numero is not None:

                texto += (
                    f"#{numero} "
                )

            texto += nombre

            if posicion:

                texto += (
                    f" ({posicion})"
                )

            # =================================================
            # TITULAR
            # =================================================

            es_titular = item.get(
                "substitute"
            )

            if es_titular is False:

                titulares.append(
                    texto
                )

            else:

                suplentes.append(
                    texto
                )

        resultado.append(
            {
                "team": nombre_equipo,
                "formation": formacion,
                "titulares": titulares,
                "suplentes": suplentes
            }
        )

    return resultado


# ============================================================
# ENRIQUECER EVENTO
# ============================================================

def enriquecer_evento(
    evento,
    incluir_lineups=True,
    incluir_incidentes=True
):

    if not evento:
        return None

    evento = dict(
        evento
    )

    # ========================================================
    # ESTADÍSTICAS
    # ========================================================

    evento["_estadisticas"] = (
        obtener_estadisticas(
            evento
        )
    )

    # ========================================================
    # INCIDENTES
    # ========================================================

    if incluir_incidentes:

        incidentes = obtener_incidentes(
            evento
        )

        evento["_incidentes"] = incidentes

    else:

        evento["_incidentes"] = []

    # ========================================================
    # ALINEACIONES
    # ========================================================

    if incluir_lineups:

        lineups = obtener_lineups(
            evento
        )

        evento["_lineups"] = (
            normalizar_lineups(
                evento,
                lineups
            )
        )

    else:

        evento["_lineups"] = []

    return evento


# ============================================================
# FECHA DE EVENTO
# ============================================================

def fecha_evento(evento):

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
# EVENTO TERMINADO
# ============================================================

def evento_terminado(evento):

    if not evento:
        return False

    status = evento.get(
        "status",
        {}
    )

    tipo = status.get(
        "type"
    )

    codigo = status.get(
        "code"
    )

    if tipo == "finished":
        return True

    if codigo == 100:
        return True

    return False


# ============================================================
# EVENTO FUTURO
# ============================================================

def evento_futuro(evento):

    if not evento:
        return False

    status = evento.get(
        "status",
        {}
    )

    tipo = status.get(
        "type"
    )

    if tipo in {
        "notstarted",
        "scheduled"
    }:

        return True

    fecha = fecha_evento(
        evento
    )

    if fecha and fecha > datetime.now():

        return True

    return False


# ============================================================
# OBTENER EVENTOS DE EQUIPO
#
# Sofascore utiliza páginas en /events/last/{page}
# ============================================================

def obtener_eventos_equipo(
    team_id,
    max_paginas=50
):

    if not team_id:
        return []

    todos = []

    vistos = set()

    for pagina in range(
        max_paginas
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

        nuevos = 0

        for evento in eventos:

            event_id = evento.get(
                "id"
            )

            if not event_id:
                continue

            if event_id in vistos:
                continue

            vistos.add(
                event_id
            )

            todos.append(
                evento
            )

            nuevos += 1

        if nuevos == 0:
            break

        # ====================================================
        # No pedir páginas innecesarias
        # ====================================================

        fechas = [
            fecha_evento(e)
            for e in eventos
        ]

        fechas = [
            f for f in fechas
            if f is not None
        ]

        if fechas:

            fecha_mas_antigua = min(
                fechas
            )

            if fecha_mas_antigua.year <= 2019:

                break

        # ====================================================
        # Pequeña pausa
        # ====================================================

        time.sleep(
            0.05
        )

    return todos


# ============================================================
# OBTENER PRÓXIMOS EVENTOS
# ============================================================

def obtener_proximos_eventos(
    team_id,
    paginas=2
):

    if not team_id:
        return []

    eventos = []

    vistos = set()

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

        lista = datos.get(
            "events",
            []
        )

        if not lista:
            break

        for evento in lista:

            event_id = evento.get(
                "id"
            )

            if not event_id:
                continue

            if event_id in vistos:
                continue

            vistos.add(
                event_id
            )

            eventos.append(
                evento
            )

    eventos.sort(
        key=lambda x:
        x.get(
            "startTimestamp",
            0
        )
    )

    return eventos


# ============================================================
# COMPROBAR COMPETICIÓN
# ============================================================

def coincide_competicion(
    evento,
    liga
):

    if not liga:
        return True

    if liga.strip().upper() == "TODAS":
        return True

    liga_buscada = (
        liga
        .strip()
        .lower()
    )

    unique = evento.get(
        "uniqueTournament",
        {}
    )

    nombre_unique = unique.get(
        "name",
        ""
    )

    tournament = evento.get(
        "tournament",
        {}
    )

    nombre_tournament = tournament.get(
        "name",
        ""
    )

    nombres = [
        nombre_unique,
        nombre_tournament
    ]

    for nombre in nombres:

        if not nombre:
            continue

        nombre_lower = (
            nombre
            .strip()
            .lower()
        )

        if (
            liga_buscada
            == nombre_lower
        ):

            return True

        if (
            liga_buscada in nombre_lower
            or
            nombre_lower in liga_buscada
        ):

            return True

    return False


# ============================================================
# ENCONTRAR ÚLTIMO PARTIDO LOCAL
# ============================================================

def encontrar_ultimo_local(
    eventos,
    team_id,
    fecha_limite,
    liga
):

    candidatos = []

    for evento in eventos:

        if not evento_terminado(
            evento
        ):
            continue

        fecha = fecha_evento(
            evento
        )

        if not fecha:
            continue

        if fecha.date() >= fecha_limite:
            continue

        home_team = evento.get(
            "homeTeam",
            {}
        )

        if home_team.get(
            "id"
        ) != team_id:

            continue

        if not coincide_competicion(
            evento,
            liga
        ):

            continue

        candidatos.append(
            evento
        )

    if not candidatos:
        return None

    candidatos.sort(
        key=lambda x:
        x.get(
            "startTimestamp",
            0
        ),
        reverse=True
    )

    return candidatos[0]


# ============================================================
# ENCONTRAR ÚLTIMO PARTIDO VISITANTE
# ============================================================

def encontrar_ultimo_visitante(
    eventos,
    team_id,
    fecha_limite,
    liga
):

    candidatos = []

    for evento in eventos:

        if not evento_terminado(
            evento
        ):
            continue

        fecha = fecha_evento(
            evento
        )

        if not fecha:
            continue

        if fecha.date() >= fecha_limite:
            continue

        away_team = evento.get(
            "awayTeam",
            {}
        )

        if away_team.get(
            "id"
        ) != team_id:

            continue

        if not coincide_competicion(
            evento,
            liga
        ):

            continue

        candidatos.append(
            evento
        )

    if not candidatos:
        return None

    candidatos.sort(
        key=lambda x:
        x.get(
            "startTimestamp",
            0
        ),
        reverse=True
    )

    return candidatos[0]


# ============================================================
# OBTENER PRÓXIMO PARTIDO
# ============================================================

def encontrar_proximo_partido(
    eventos,
    liga
):

    ahora = datetime.now()

    candidatos = []

    for evento in eventos:

        fecha = fecha_evento(
            evento
        )

        if not fecha:
            continue

        if fecha <= ahora:
            continue

        if not coincide_competicion(
            evento,
            liga
        ):

            continue

        candidatos.append(
            evento
        )

    if not candidatos:
        return None

    candidatos.sort(
        key=lambda x:
        x.get(
            "startTimestamp",
            0
        )
    )

    return candidatos[0]


# ============================================================
# OBTENER H2H
# ============================================================

def obtener_h2h(
    team_a_id,
    team_b_id,
    fecha_limite,
    liga
):

    if not team_a_id or not team_b_id:
        return []

    url = (
        f"{BASE_URL}/team/"
        f"{team_a_id}/"
        f"h2h/{team_b_id}"
    )

    datos = obtener_json(
        url
    )

    if datos:

        eventos = datos.get(
            "events",
            []
        )

        if eventos:

            return eventos

    # ========================================================
    # RESPALDO:
    # buscar eventos históricos de equipo A
    # ========================================================

    eventos_a = obtener_eventos_equipo(
        team_a_id,
        max_paginas=50
    )

    h2h = []

    for evento in eventos_a:

        if not evento_terminado(
            evento
        ):
            continue

        fecha = fecha_evento(
            evento
        )

        if not fecha:
            continue

        if fecha.date() >= fecha_limite:
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

        if {
            home_id,
            away_id
        } != {
            team_a_id,
            team_b_id
        }:

            continue

        if not coincide_competicion(
            evento,
            liga
        ):

            continue

        h2h.append(
            evento
        )

    h2h.sort(
        key=lambda x:
        x.get(
            "startTimestamp",
            0
        ),
        reverse=True
    )

    return h2h


# ============================================================
# H2H CON EQUIPO A LOCAL
# ============================================================

def encontrar_h2h_local(
    h2h,
    team_a_id,
    fecha_limite
):

    for evento in sorted(
        h2h,
        key=lambda x:
        x.get(
            "startTimestamp",
            0
        ),
        reverse=True
    ):

        if not evento_terminado(
            evento
        ):
            continue

        fecha = fecha_evento(
            evento
        )

        if not fecha:
            continue

        if fecha.date() >= fecha_limite:
            continue

        home_id = (
            evento
            .get("homeTeam", {})
            .get("id")
        )

        if home_id == team_a_id:

            return evento

    return None


# ============================================================
# H2H CON EQUIPO A VISITANTE
# ============================================================

def encontrar_h2h_visitante(
    h2h,
    team_a_id,
    fecha_limite
):

    for evento in sorted(
        h2h,
        key=lambda x:
        x.get(
            "startTimestamp",
            0
        ),
        reverse=True
    ):

        if not evento_terminado(
            evento
        ):
            continue

        fecha = fecha_evento(
            evento
        )

        if not fecha:
            continue

        if fecha.date() >= fecha_limite:
            continue

        away_id = (
            evento
            .get("awayTeam", {})
            .get("id")
        )

        if away_id == team_a_id:

            return evento

    return None


# ============================================================
# FORMATEAR FECHA Y HORA
# ============================================================

def formatear_fecha_hora(
    evento
):

    fecha = fecha_evento(
        evento
    )

    if not fecha:
        return None

    return fecha.strftime(
        "%d/%m/%Y %H:%M"
    )


# ============================================================
# OBTENER NOMBRE DE COMPETICIÓN
# ============================================================

def obtener_nombre_competicion(
    evento
):

    if not evento:
        return ""

    unique = evento.get(
        "uniqueTournament",
        {}
    )

    nombre = unique.get(
        "name"
    )

    if nombre:
        return nombre

    tournament = evento.get(
        "tournament",
        {}
    )

    return tournament.get(
        "name",
        ""
    )


# ============================================================
# PREPARAR PRÓXIMO PARTIDO
# ============================================================

def preparar_proximo_partido(
    evento,
    incluir_lineups=True
):

    if not evento:
        return None

    enriquecido = enriquecer_evento(
        evento,
        incluir_lineups=incluir_lineups,
        incluir_incidentes=False
    )

    return enriquecido


# ============================================================
# PREPARAR PARTIDO HISTÓRICO
# ============================================================

def preparar_partido_historico(
    evento
):

    if not evento:
        return None

    return enriquecer_evento(
        evento,
        incluir_lineups=True,
        incluir_incidentes=True
    )


# ============================================================
# ANALIZAR PARTIDO
# ============================================================

def analizar_partido(
    equipo_a_nombre,
    equipo_b_nombre,
    fecha_partido,
    liga="TODAS"
):

    # ========================================================
    # VALIDACIÓN
    # ========================================================

    if not equipo_a_nombre:
        return {
            "error":
            "No se indicó el Equipo A."
        }

    if not equipo_b_nombre:
        return {
            "error":
            "No se indicó el Equipo B."
        }

    # ========================================================
    # FECHA
    # ========================================================

    try:

        fecha_limite = datetime.strptime(
            fecha_partido,
            "%Y-%m-%d"
        ).date()

    except Exception:

        return {
            "error":
            "La fecha proporcionada "
            "no es válida."
        }

    # ========================================================
    # BUSCAR EQUIPOS
    # ========================================================

    equipo_a = buscar_equipo(
        equipo_a_nombre
    )

    equipo_b = buscar_equipo(
        equipo_b_nombre
    )

    if not equipo_a:

        return {
            "error":
            f"No se encontró el equipo: "
            f"{equipo_a_nombre}"
        }

    if not equipo_b:

        return {
            "error":
            f"No se encontró el equipo: "
            f"{equipo_b_nombre}"
        }

    team_a_id = equipo_a[
        "id"
    ]

    team_b_id = equipo_b[
        "id"
    ]

    # ========================================================
    # OBTENER EVENTOS DE AMBOS EQUIPOS
    # ========================================================

    eventos_a = obtener_eventos_equipo(
        team_a_id,
        max_paginas=50
    )

    eventos_b = obtener_eventos_equipo(
        team_b_id,
        max_paginas=50
    )

    # ========================================================
    # ÚLTIMO LOCAL / VISITANTE
    # ========================================================

    local_a = encontrar_ultimo_local(
        eventos_a,
        team_a_id,
        fecha_limite,
        liga
    )

    visitante_a = encontrar_ultimo_visitante(
        eventos_a,
        team_a_id,
        fecha_limite,
        liga
    )

    local_b = encontrar_ultimo_local(
        eventos_b,
        team_b_id,
        fecha_limite,
        liga
    )

    visitante_b = encontrar_ultimo_visitante(
        eventos_b,
        team_b_id,
        fecha_limite,
        liga
    )

    # ========================================================
    # H2H
    # ========================================================

    h2h = obtener_h2h(
        team_a_id,
        team_b_id,
        fecha_limite,
        liga
    )

    h2h_a_local = encontrar_h2h_local(
        h2h,
        team_a_id,
        fecha_limite
    )

    h2h_a_visitante = encontrar_h2h_visitante(
        h2h,
        team_a_id,
        fecha_limite
    )

    # ========================================================
    # PREPARAR PARTIDOS HISTÓRICOS
    # ========================================================

    local_a = preparar_partido_historico(
        local_a
    )

    visitante_a = preparar_partido_historico(
        visitante_a
    )

    local_b = preparar_partido_historico(
        local_b
    )

    visitante_b = preparar_partido_historico(
        visitante_b
    )

    h2h_a_local = preparar_partido_historico(
        h2h_a_local
    )

    h2h_a_visitante = preparar_partido_historico(
        h2h_a_visitante
    )

    # ========================================================
    # PRÓXIMO PARTIDO DE EQUIPO A
    # ========================================================

    proximos_a = obtener_proximos_eventos(
        team_a_id,
        paginas=2
    )

    proximo_a = encontrar_proximo_partido(
        proximos_a,
        liga
    )

    # ========================================================
    # PRÓXIMO PARTIDO DE EQUIPO B
    # ========================================================

    proximos_b = obtener_proximos_eventos(
        team_b_id,
        paginas=2
    )

    proximo_b = encontrar_proximo_partido(
        proximos_b,
        liga
    )

    # ========================================================
    # PRÓXIMO ENFRENTAMIENTO ENTRE AMBOS
    # ========================================================

    proximo_enfrentamiento = None

    candidatos_enfrentamiento = []

    for evento in proximos_a:

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
            home_id == team_b_id
            and
            away_id == team_a_id
        ) or (
            home_id == team_a_id
            and
            away_id == team_b_id
        ):

            if coincide_competicion(
                evento,
                liga
            ):

                candidatos_enfrentamiento.append(
                    evento
                )

    candidatos_enfrentamiento.sort(
        key=lambda x:
        x.get(
            "startTimestamp",
            0
        )
    )

    if candidatos_enfrentamiento:

        proximo_enfrentamiento = (
            preparar_proximo_partido(
                candidatos_enfrentamiento[0],
                incluir_lineups=False
            )
        )

    # ========================================================
    # CONSTRUIR RESULTADO
    # ========================================================

    datos = {

        "equipo_a":
            equipo_a["name"],

        "equipo_b":
            equipo_b["name"],

        "liga":
            liga,

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
            visitante_b,

        "proximo_a":
            preparar_proximo_partido(
                proximo_a,
                incluir_lineups=True
            ),

        "proximo_b":
            preparar_proximo_partido(
                proximo_b,
                incluir_lineups=True
            ),

        "proximo_enfrentamiento":
            proximo_enfrentamiento
    }

    return datos


# ============================================================
# FUNCIONES AUXILIARES PARA EL APP
# ============================================================

def obtener_goles(evento):

    if not evento:
        return []

    incidentes = evento.get(
        "_incidentes",
        []
    )

    goles = []

    local = (
        evento
        .get("homeTeam", {})
        .get("name", "Desconocido")
    )

    visitante = (
        evento
        .get("awayTeam", {})
        .get("name", "Desconocido")
    )

    for incidente in incidentes:

        tipo = incidente.get(
            "incidentType"
        )

        clase = incidente.get(
            "incidentClass"
        )

        if tipo != "goal":
            continue

        jugador = incidente.get(
            "player",
            {}
        )

        nombre = jugador.get(
            "name",
            "Jugador desconocido"
        )

        minuto = incidente.get(
            "time"
        )

        is_home = incidente.get(
            "isHome"
        )

        if is_home is True:

            equipo = local

        elif is_home is False:

            equipo = visitante

        else:

            equipo = ""

        texto = {
            "minuto": minuto,
            "jugador": nombre,
            "equipo": equipo,
            "tipo": clase or "regular"
        }

        goles.append(
            texto
        )

    goles.sort(
        key=lambda x:
        (
            x["minuto"]
            if isinstance(
                x["minuto"],
                (int, float)
            )
            else 999
        )
    )

    return goles


# ============================================================
# OBTENER CAMBIOS
# ============================================================

def obtener_cambios(evento):

    if not evento:
        return []

    incidentes = evento.get(
        "_incidentes",
        []
    )

    cambios = []

    for incidente in incidentes:

        if incidente.get(
            "incidentType"
        ) != "substitution":

            continue

        jugador_entrante = incidente.get(
            "playerIn",
            {}
        )

        jugador_saliente = incidente.get(
            "playerOut",
            {}
        )

        nombre_entrante = (
            jugador_entrante.get(
                "name"
            )
        )

        nombre_saliente = (
            jugador_saliente.get(
                "name"
            )
        )

        if not nombre_entrante:
            continue

        if not nombre_saliente:
            continue

        equipo = incidente.get(
            "isHome"
        )

        if equipo is True:

            nombre_equipo = (
                evento
                .get("homeTeam", {})
                .get("name")
            )

        else:

            nombre_equipo = (
                evento
                .get("awayTeam", {})
                .get("name")
            )

        cambios.append(
            {
                "minuto":
                    incidente.get(
                        "time"
                    ),

                "entra":
                    nombre_entrante,

                "sale":
                    nombre_saliente,

                "equipo":
                    nombre_equipo
            }
        )

    cambios.sort(
        key=lambda x:
        (
            x["minuto"]
            if isinstance(
                x["minuto"],
                (int, float)
            )
            else 999
        )
    )

    return cambios


# ============================================================
# OBTENER ALINEACIONES PARA EL APP
# ============================================================

def obtener_alineaciones(evento):

    if not evento:
        return []

    return evento.get(
        "_lineups",
        []
    )


# ============================================================
# OBTENER INFORMACIÓN DE PRÓXIMO PARTIDO
# ============================================================

def obtener_info_proximo(
    evento
):

    if not evento:
        return None

    fecha = formatear_fecha_hora(
        evento
    )

    local = (
        evento
        .get("homeTeam", {})
        .get("name", "Desconocido")
    )

    visitante = (
        evento
        .get("awayTeam", {})
        .get("name", "Desconocido")
    )

    competicion = (
        obtener_nombre_competicion(
            evento
        )
    )

    return {
        "fecha_hora":
            fecha,

        "partido":
            f"{local} vs {visitante}",

        "competicion":
            competicion,

        "evento":
            evento
    }