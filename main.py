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

def convertir_fecha_limite(fecha_limite):

    if hasattr(fecha_limite, "date"):
        try:
            return fecha_limite.date()
        except Exception:
            pass

    if isinstance(fecha_limite, str):

        try:

            return datetime.strptime(
                fecha_limite,
                "%Y-%m-%d"
            ).date()

        except Exception:

            return None

    return None


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

    if not evento:
        return False

    status = evento.get(
        "status",
        {}
    )

    codigo = status.get(
        "code"
    )

    tipo = str(
        status.get(
            "type",
            ""
        )
    ).lower()

    # SofaScore normalmente utiliza
    # code 100 para partidos finalizados.

    if codigo == 100:
        return True

    return tipo in {
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
# PARTIDO ANTERIOR A FECHA
# ============================================================

def es_anterior_a_fecha(
    evento,
    fecha_limite
):

    fecha_evento = obtener_fecha_date(
        evento
    )

    fecha_limite_date = convertir_fecha_limite(
        fecha_limite
    )

    if not fecha_evento:
        return False

    if not fecha_limite_date:
        return False

    # IMPORTANTE:
    #
    # Si el partido futuro es 2026-08-15,
    # solamente acepta:
    #
    # 2026-08-14
    # 2026-08-10
    # 2026-01-01
    #
    # NO acepta 2026-08-15.

    return fecha_evento < fecha_limite_date


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

    nombre = tournament.get(
        "name",
        ""
    )

    if nombre:
        return nombre

    # --------------------------------------------------------
    # uniqueTournament dentro de tournament
    # --------------------------------------------------------

    unique = tournament.get(
        "uniqueTournament",
        {}
    )

    nombre = unique.get(
        "name",
        ""
    )

    if nombre:
        return nombre

    return ""


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
# COMPROBAR LIGA
# ============================================================

def pertenece_a_liga(
    evento,
    liga
):

    if not evento:
        return False

    nombre_liga = normalizar_texto(
        obtener_nombre_liga(evento)
    )

    liga_buscada = normalizar_texto(
        liga
    )

    if not nombre_liga:
        return False

    if not liga_buscada:
        return False

    print(
        "LIGA EVENTO:",
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
# OBTENER HISTORIAL DEL EQUIPO
# ============================================================

def obtener_historial(team_id):

    partidos = []

    pagina = 0

    # ========================================================
    # IMPORTANTE
    #
    # Se buscan bastantes páginas porque el H2H puede estar
    # más atrás que los últimos partidos normales.
    # ========================================================

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
# COMPROBAR SI DOS EQUIPOS SE ENFRENTARON
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

    # ========================================================
    # A LOCAL VS B VISITANTE
    #
    # O
    #
    # B LOCAL VS A VISITANTE
    #
    # Ambas formas son válidas.
    # ========================================================

    return (
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


# ============================================================
# VALIDAR H2H
# ============================================================

def es_h2h_valido(
    evento,
    equipo_a_id,
    equipo_b_id,
    liga,
    fecha_limite
):

    if not evento:
        return False

    # --------------------------------------------------------
    # 1. TIENEN QUE SER LOS DOS EQUIPOS
    # --------------------------------------------------------

    if not es_enfrentamiento(
        evento,
        equipo_a_id,
        equipo_b_id
    ):
        return False

    # --------------------------------------------------------
    # 2. TIENE QUE SER ANTERIOR AL PARTIDO FUTURO
    # --------------------------------------------------------

    if not es_anterior_a_fecha(
        evento,
        fecha_limite
    ):
        return False

    # --------------------------------------------------------
    # 3. TIENE QUE ESTAR FINALIZADO
    # --------------------------------------------------------

    if not partido_valido(
        evento
    ):
        return False

    # --------------------------------------------------------
    # 4. TIENE QUE SER DE LA LIGA SELECCIONADA
    #
    # ESTE FILTRO SÍ SE MANTIENE PARA H2H.
    # --------------------------------------------------------

    if not pertenece_a_liga(
        evento,
        liga
    ):
        return False

    return True


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

    eventos = list(
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
# H2H DESDE HISTORIALES
# ============================================================

def obtener_h2h_desde_historiales(
    historial_a,
    historial_b,
    equipo_a_id,
    equipo_b_id,
    liga,
    fecha_limite
):

    candidatos = []

    # ========================================================
    # HISTORIAL EQUIPO A
    # ========================================================

    for evento in historial_a:

        if es_h2h_valido(
            evento,
            equipo_a_id,
            equipo_b_id,
            liga,
            fecha_limite
        ):

            candidatos.append(
                evento
            )

    # ========================================================
    # HISTORIAL EQUIPO B
    # ========================================================

    for evento in historial_b:

        if es_h2h_valido(
            evento,
            equipo_a_id,
            equipo_b_id,
            liga,
            fecha_limite
        ):

            candidatos.append(
                evento
            )

    # ========================================================
    # ELIMINAR DUPLICADOS
    # ========================================================

    candidatos = eliminar_duplicados(
        candidatos
    )

    # ========================================================
    # ORDENAR DEL MÁS NUEVO AL MÁS ANTIGUO
    # ========================================================

    candidatos = ordenar_por_fecha(
        candidatos
    )

    print(
        "===================================="
    )

    print(
        "H2H EN HISTORIALES:",
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
            .get("name"),
            "| LIGA:",
            obtener_nombre_liga(evento)
        )

    print(
        "===================================="
    )

    return candidatos


# ============================================================
# OBTENER EVENTO H2H BASE
# ============================================================

def encontrar_evento_h2h_base(
    historial_a,
    historial_b,
    equipo_a_id,
    equipo_b_id,
    liga,
    fecha_limite
):

    candidatos = obtener_h2h_desde_historiales(
        historial_a,
        historial_b,
        equipo_a_id,
        equipo_b_id,
        liga,
        fecha_limite
    )

    if not candidatos:

        print(
            "NO SE ENCONTRÓ EVENTO H2H BASE"
        )

        return None

    evento = candidatos[0]

    print(
        "===================================="
    )

    print(
        "EVENTO H2H BASE:"
    )

    print(
        "ID:",
        evento.get("id")
    )

    print(
        "FECHA:",
        obtener_fecha_date(evento)
    )

    print(
        evento
        .get("homeTeam", {})
        .get("name"),
        "vs",
        evento
        .get("awayTeam", {})
        .get("name")
    )

    print(
        "LIGA:",
        obtener_nombre_liga(evento)
    )

    print(
        "===================================="
    )

    return evento


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

    event_id = evento_base.get(
        "id"
    )

    if not event_id:
        return []

    url = (
        f"{BASE_URL}/event/"
        f"{event_id}/h2h/events"
    )

    print(
        "===================================="
    )

    print(
        "BUSCANDO H2H DIRECTO"
    )

    print(
        "EVENT ID:",
        event_id
    )

    print(
        "URL:",
        url
    )

    print(
        "===================================="
    )

    datos = obtener_json(
        url
    )

    if not datos:

        print(
            "SOFASCORE NO DEVOLVIÓ H2H"
        )

        return []

    eventos = datos.get(
        "events",
        []
    )

    print(
        "H2H RECIBIDOS:",
        len(eventos)
    )

    encontrados = []

    for evento in eventos:

        if not evento:
            continue

        # ----------------------------------------------------
        # LOS DOS EQUIPOS
        # ----------------------------------------------------

        if not es_enfrentamiento(
            evento,
            equipo_a_id,
            equipo_b_id
        ):
            continue

        # ----------------------------------------------------
        # FECHA
        # ----------------------------------------------------

        if not es_anterior_a_fecha(
            evento,
            fecha_limite
        ):

            print(
                "H2H DESCARTADO POR FECHA:",
                obtener_fecha_date(evento)
            )

            continue

        # ----------------------------------------------------
        # FINALIZADO
        # ----------------------------------------------------

        if not partido_valido(
            evento
        ):
            continue

        # ----------------------------------------------------
        # LIGA
        # ----------------------------------------------------

        if not pertenece_a_liga(
            evento,
            liga
        ):

            print(
                "H2H DESCARTADO POR LIGA:",
                obtener_nombre_liga(evento)
            )

            continue

        encontrados.append(
            evento
        )

    # ========================================================
    # ELIMINAR DUPLICADOS
    # ========================================================

    encontrados = eliminar_duplicados(
        encontrados
    )

    # ========================================================
    # ORDENAR
    # ========================================================

    encontrados = ordenar_por_fecha(
        encontrados
    )

    print(
        "===================================="
    )

    print(
        "H2H VÁLIDOS DESDE SOFASCORE:",
        len(encontrados)
    )

    for evento in encontrados:

        print(
            obtener_fecha_date(evento),
            "|",
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

    return encontrados


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

    # ========================================================
    # PRIMER MÉTODO
    #
    # Buscar directamente en los historiales.
    #
    # Esto garantiza que H2H funcione incluso si el endpoint
    # /event/{id}/h2h/events no devuelve información.
    # ========================================================

    h2h_historial = obtener_h2h_desde_historiales(
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
    # Si encontramos al menos un H2H, podemos intentar
    # consultar el endpoint oficial para obtener más.
    # ========================================================

    if h2h_historial:

        evento_base = h2h_historial[0]

        h2h_sofascore = obtener_h2h_desde_sofascore(
            evento_base,
            equipo_a_id,
            equipo_b_id,
            liga,
            fecha_limite
        )

        # ----------------------------------------------------
        # UNIR RESULTADOS
        # ----------------------------------------------------

        todos = []

        todos.extend(
            h2h_historial
        )

        todos.extend(
            h2h_sofascore
        )

        todos = eliminar_duplicados(
            todos
        )

        todos = ordenar_por_fecha(
            todos
        )

        # ----------------------------------------------------
        # VOLVER A FILTRAR
        #
        # Esto evita que el endpoint directo introduzca
        # partidos incorrectos.
        # ----------------------------------------------------

        finales = []

        for evento in todos:

            if es_h2h_valido(
                evento,
                equipo_a_id,
                equipo_b_id,
                liga,
                fecha_limite
            ):

                finales.append(
                    evento
                )

        finales = eliminar_duplicados(
            finales
        )

        finales = ordenar_por_fecha(
            finales
        )

        print(
            "===================================="
        )

        print(
            "H2H FINALES:",
            len(finales)
        )

        print(
            "===================================="
        )

        for evento in finales:

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

        return finales[:2]

    # ========================================================
    # SI NO SE ENCONTRÓ NADA
    # ========================================================

    print(
        "NO SE ENCONTRÓ H2H EN LOS HISTORIALES."
    )

    return []


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

    candidatos = ordenar_por_fecha(
        candidatos
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

    # ========================================================
    # BUSCAR PERIODO ALL
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
    # RECORRER ESTADÍSTICAS
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

    # ========================================================
    # NOMBRES
    # ========================================================

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
    # EXTRAER DATOS
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
    # VALIDAR EQUIPO A
    # ========================================================

    if not nombre_equipo_a.strip():

        return {
            "error":
            "Debes indicar el Equipo A."
        }

    # ========================================================
    # VALIDAR EQUIPO B
    # ========================================================

    if not nombre_equipo_b.strip():

        return {
            "error":
            "Debes indicar el Equipo B."
        }

    # ========================================================
    # VALIDAR LIGA
    # ========================================================

    if not liga.strip():

        return {
            "error":
            "Debes indicar la liga."
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

    if not id_a:

        return {
            "error":
            f"El equipo {nombre_equipo_a} no tiene ID válido."
        }

    if not id_b:

        return {
            "error":
            f"El equipo {nombre_equipo_b} no tiene ID válido."
        }

    # ========================================================
    # NOMBRES REALES
    # ========================================================

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
    # OBTENER HISTORIALES
    # ========================================================

    historial_a = obtener_historial(
        id_a
    )

    historial_b = obtener_historial(
        id_b
    )

    print(
        "HISTORIAL A:",
        len(historial_a)
    )

    print(
        "HISTORIAL B:",
        len(historial_b)
    )

    # ========================================================
    # H2H
    #
    # IMPORTANTE:
    #
    # A vs B
    # B vs A
    #
    # ambos válidos.
    #
    # Pero solamente en la liga indicada.
    # ========================================================

    h2h = obtener_h2h(
        historial_a,
        historial_b,
        id_a,
        id_b,
        liga,
        fecha_partido
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
    # DEBUG FINAL
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

    for evento in h2h:

        print(
            obtener_fecha_date(evento),
            "|",
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
        "LOCAL A:",
        (
            obtener_fecha_date(local_a)
            if local_a
            else None
        )
    )

    print(
        "VISITANTE A:",
        (
            obtener_fecha_date(visitante_a)
            if visitante_a
            else None
        )
    )

    print(
        "LOCAL B:",
        (
            obtener_fecha_date(local_b)
            if local_b
            else None
        )
    )

    print(
        "VISITANTE B:",
        (
            obtener_fecha_date(visitante_b)
            if visitante_b
            else None
        )
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