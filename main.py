from datetime import datetime
from urllib.parse import quote
from curl_cffi import requests

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
            print("ERROR HTTP:", respuesta.status_code)
            return None

        return respuesta.json()

    except Exception as error:
        print("ERROR:", error)
        return None


# ============================================================
# BUSCAR EQUIPO
# ============================================================

def buscar_equipo(nombre):
    url = f"{BASE_URL}/search/all?q={quote(nombre)}"
    datos = obtener_json(url)

    if not datos:
        print("No se obtuvieron datos para:", nombre)
        return None

    resultados = datos.get("results", [])
    candidatos = []

    for resultado in resultados:
        if resultado.get("type") != "team":
            continue

        entidad = resultado.get("entity", {})
        if not entidad:
            continue

        candidatos.append(entidad)

    # ========================================================
    # COINCIDENCIA EXACTA
    # ========================================================
    nombre_buscado = nombre.strip().lower()

    for equipo in candidatos:
        nombre_encontrado = equipo.get("name", "").strip().lower()

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
        nombre_encontrado = equipo.get("name", "").strip().lower()

        if nombre_buscado in nombre_encontrado or nombre_encontrado in nombre_buscado:
            print(
                "EQUIPO ENCONTRADO POR COINCIDENCIA:",
                equipo.get("name"),
                "| ID:",
                equipo.get("id")
            )
            return equipo

    print("NO SE ENCONTRÓ EL EQUIPO:", nombre)
    return None


# ============================================================
# OBTENER FECHA DE EVENTO
# ============================================================

def obtener_fecha(evento):
    if not evento:
        return None

    timestamp = evento.get("startTimestamp")
    if not timestamp:
        return None

    try:
        return datetime.fromtimestamp(timestamp)
    except Exception:
        return None


# ============================================================
# OBTENER FECHA COMO DATE
# ============================================================

def obtener_fecha_date(evento):
    fecha = obtener_fecha(evento)
    if not fecha:
        return None
    return fecha.date()


# ============================================================
# ESTADO DEL PARTIDO
# ============================================================

def obtener_estado(evento):
    status = evento.get("status", {})
    return str(status.get("type", "")).lower()


# ============================================================
# PARTIDO FINALIZADO
# ============================================================

def es_finalizado(evento):
    estado = obtener_estado(evento)
    return estado in {"finished", "ended"}


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
# PARTIDO ANTERIOR A FECHA
# ============================================================

def es_anterior_a_fecha(evento, fecha_limite):
    fecha = obtener_fecha_date(evento)
    if not fecha:
        return False

    return fecha < datetime.strptime(fecha_limite, "%Y-%m-%d").date()


# ============================================================
# OBTENER NOMBRE DE LIGA
# ============================================================

def obtener_nombre_liga(evento):
    if not evento:
        return ""

    unique = evento.get("uniqueTournament", {})
    nombre = unique.get("name", "")
    if nombre:
        return nombre

    tournament = evento.get("tournament", {})
    nombre = tournament.get("name", "")
    if nombre:
        return nombre

    unique = tournament.get("uniqueTournament", {})
    return unique.get("name", "")


# ============================================================
# COMPROBAR LIGA
# ============================================================

def pertenece_a_liga(evento, liga):
    if not evento:
        return False

    nombre_liga = obtener_nombre_liga(evento).strip().lower()
    liga_buscada = liga.strip().lower()

    print(
        "LIGA EVENTO:",
        repr(nombre_liga),
        "| LIGA BUSCADA:",
        repr(liga_buscada)
    )

    if not nombre_liga:
        return False

    if nombre_liga == liga_buscada:
        return True

    if liga_buscada in nombre_liga or nombre_liga in liga_buscada:
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
        url = f"{BASE_URL}/team/{team_id}/events/last/{pagina}"
        datos = obtener_json(url)

        if not datos:
            break

        eventos = datos.get("events", [])
        if not eventos:
            break

        print(
            f"EQUIPO {team_id} | PÁGINA {pagina} | EVENTOS: {len(eventos)}"
        )

        partidos.extend(eventos)

        if not datos.get("hasNextPage", False):
            break

        pagina += 1

    return partidos


# ============================================================
# COMPROBAR SI DOS EQUIPOS SE ENFRENTARON
# ============================================================

def es_enfrentamiento(evento, equipo_a_id, equipo_b_id):
    if not evento:
        return False

    home_id = evento.get("homeTeam", {}).get("id")
    away_id = evento.get("awayTeam", {}).get("id")

    if not home_id or not away_id:
        return False

    return {home_id, away_id} == {equipo_a_id, equipo_b_id}


# ============================================================
# ENCONTRAR UN EVENTO H2H BASE
# ============================================================

def encontrar_evento_h2h_base(
    historial_a,
    historial_b,
    equipo_a_id,
    equipo_b_id,
    fecha_limite
):
    candidatos = []

    for evento in historial_a:
        if not es_enfrentamiento(evento, equipo_a_id, equipo_b_id):
            continue
        if not es_anterior_a_fecha(evento, fecha_limite):
            continue
        if not partido_valido(evento):
            continue
        candidatos.append(evento)

    for evento in historial_b:
        if not es_enfrentamiento(evento, equipo_a_id, equipo_b_id):
            continue
        if not es_anterior_a_fecha(evento, fecha_limite):
            continue
        if not partido_valido(evento):
            continue
        candidatos.append(evento)

    unicos = {}
    for evento in candidatos:
        event_id = evento.get("id")
        if event_id:
            unicos[event_id] = evento

    candidatos = list(unicos.values())
    candidatos.sort(
        key=lambda evento: evento.get("startTimestamp", 0),
        reverse=True
    )

    if candidatos:
        print("EVENTO H2H BASE ENCONTRADO:", candidatos[0].get("id"))
        return candidatos[0]

    print("NO SE ENCONTRÓ EVENTO H2H BASE")
    return None


# ============================================================
# OBTENER H2H DIRECTAMENTE DESDE SOFASCORE
# ============================================================

def obtener_h2h_desde_sofascore(
    evento_base,
    equipo_a_id,
    equipo_b_id,
    liga,
    fecha_limite
):
    if not evento_base:
        return []

    event_id = evento_base.get("id")
    if not event_id:
        return []

    url = f"{BASE_URL}/event/{event_id}/h2h/events"
    datos = obtener_json(url)

    if not datos:
        return []

    eventos = datos.get("events", [])
    encontrados = []
    ids = set()

    for evento in eventos:
        if not evento:
            continue

        if not es_enfrentamiento(evento, equipo_a_id, equipo_b_id):
            continue

        if not es_anterior_a_fecha(evento, fecha_limite):
            continue

        if not partido_valido(evento):
            continue

        if not pertenece_a_liga(evento, liga):
            continue

        event_id_actual = evento.get("id")
        if event_id_actual and event_id_actual in ids:
            continue

        if event_id_actual:
            ids.add(event_id_actual)

        encontrados.append(evento)

    encontrados.sort(
        key=lambda evento: evento.get("startTimestamp", 0),
        reverse=True
    )

    return encontrados[:2]


# ============================================================
# OBTENER H2H DE RESPALDO
# ============================================================

def obtener_h2h_respaldo(
    historial_a,
    historial_b,
    equipo_a_id,
    equipo_b_id,
    liga,
    fecha_limite
):
    candidatos = []

    for evento in historial_a:
        if not es_enfrentamiento(evento, equipo_a_id, equipo_b_id):
            continue
        if not es_anterior_a_fecha(evento, fecha_limite):
            continue
        if not partido_valido(evento):
            continue
        if not pertenece_a_liga(evento, liga):
            continue
        candidatos.append(evento)

    for evento in historial_b:
        if not es_enfrentamiento(evento, equipo_a_id, equipo_b_id):
            continue
        if not es_anterior_a_fecha(evento, fecha_limite):
            continue
        if not partido_valido(evento):
            continue
        if not pertenece_a_liga(evento, liga):
            continue
        candidatos.append(evento)

    unicos = {}
    for evento in candidatos:
        event_id = evento.get("id")
        if event_id:
            unicos[event_id] = evento

    candidatos = list(unicos.values())
    candidatos.sort(
        key=lambda evento: evento.get("startTimestamp", 0),
        reverse=True
    )

    return candidatos[:2]


# ============================================================
# OBTENER H2H
# ============================================================

def obtener_h2h(
    historial_a,
    historial_b,
    equipo_a_id,
    equipo_b_id,
    liga,
    fecha_limite
):
    evento_base = encontrar_evento_h2h_base(
        historial_a,
        historial_b,
        equipo_a_id,
        equipo_b_id,
        fecha_limite
    )

    if evento_base:
        h2h = obtener_h2h_desde_sofascore(
            evento_base,
            equipo_a_id,
            equipo_b_id,
            liga,
            fecha_limite
        )
        if h2h:
            return h2h

    print("USANDO H2H DE RESPALDO...")
    return obtener_h2h_respaldo(
        historial_a,
        historial_b,
        equipo_a_id,
        equipo_b_id,
        liga,
        fecha_limite
    )


# ============================================================
# ÚLTIMO PARTIDO COMO LOCAL
# ============================================================

def ultimo_local(historial, equipo_id, fecha_limite, liga):
    candidatos = []

    for evento in historial:
        if not es_anterior_a_fecha(evento, fecha_limite):
            continue
        if not partido_valido(evento):
            continue
        if not pertenece_a_liga(evento, liga):
            continue

        home_id = evento.get("homeTeam", {}).get("id")
        if home_id != equipo_id:
            continue

        candidatos.append(evento)

    candidatos.sort(
        key=lambda evento: evento.get("startTimestamp", 0),
        reverse=True
    )

    if candidatos:
        return candidatos[0]

    return None


# ============================================================
# ÚLTIMO PARTIDO COMO VISITANTE
# ============================================================

def ultimo_visitante(historial, equipo_id, fecha_limite, liga):
    candidatos = []

    for evento in historial:
        if not es_anterior_a_fecha(evento, fecha_limite):
            continue
        if not partido_valido(evento):
            continue
        if not pertenece_a_liga(evento, liga):
            continue

        away_id = evento.get("awayTeam", {}).get("id")
        if away_id != equipo_id:
            continue

        candidatos.append(evento)

    candidatos.sort(
        key=lambda evento: evento.get("startTimestamp", 0),
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

    event_id = evento.get("id")
    if not event_id:
        return resultado

    url = f"{BASE_URL}/event/{event_id}/statistics"
    datos = obtener_json(url)

    if not datos:
        return resultado

    periodos = datos.get("statistics", [])
    periodo = None

    for item in periodos:
        if item.get("period") == "ALL":
            periodo = item
            break

    if periodo is None:
        if periodos:
            periodo = periodos[0]
        else:
            return resultado

    grupos = periodo.get("groups", [])
    estadisticas = {}

    for grupo in grupos:
        for item in grupo.get("statisticsItems", []):
            nombre = item.get("name", "").strip().lower()
            if nombre:
                estadisticas[nombre] = item

    nombres = {
        "ball possession": "Posesión",
        "corner kicks": "Córners",
        "fouls": "Faltas",
        "yellow cards": "Tarjetas amarillas",
        "shots on target": "Tiros a puerta",
        "offsides": "Fueras de juego"
    }

    for nombre_api, nombre_salida in nombres.items():
        item = estadisticas.get(nombre_api)
        if not item:
            continue

        local = item.get("home")
        visitante = item.get("away")
        resultado[nombre_salida] = (local, visitante)

    return resultado


# ============================================================
# ANALIZAR PARTIDO
# ============================================================

def analizar_partido(nombre_equipo_a, nombre_equipo_b, fecha_partido, liga):
    if not nombre_equipo_a.strip():
        return {"error": "Debes indicar el Equipo A."}

    if not nombre_equipo_b.strip():
        return {"error": "Debes indicar el Equipo B."}

    if not liga.strip():
        return {"error": "Debes indicar la liga."}

    equipo_a = buscar_equipo(nombre_equipo_a)
    if not equipo_a:
        return {"error": f"No se encontró: {nombre_equipo_a}"}

    equipo_b = buscar_equipo(nombre_equipo_b)
    if not equipo_b:
        return {"error": f"No se encontró: {nombre_equipo_b}"}

    id_a = equipo_a.get("id")
    id_b = equipo_b.get("id")

    nombre_a = equipo_a.get("name", nombre_equipo_a)
    nombre_b = equipo_b.get("name", nombre_equipo_b)

    historial_a = obtener_historial(id_a)
    historial_b = obtener_historial(id_b)

    h2h = obtener_h2h(
        historial_a,
        historial_b,
        id_a,
        id_b,
        liga,
        fecha_partido
    )

    local_a = ultimo_local(
        historial_a,
        id_a,
        fecha_partido,
        liga
    )

    visitante_a = ultimo_visitante(
        historial_a,
        id_a,
        fecha_partido,
        liga
    )

    local_b = ultimo_local(
        historial_b,
        id_b,
        fecha_partido,
        liga
    )

    visitante_b = ultimo_visitante(
        historial_b,
        id_b,
        fecha_partido,
        liga
    )

    return {
        "equipo_a": nombre_a,
        "equipo_b": nombre_b,
        "liga": liga,
        "h2h": h2h,
        "local_a": local_a,
        "visitante_a": visitante_a,
        "local_b": local_b,
        "visitante_b": visitante_b
    }