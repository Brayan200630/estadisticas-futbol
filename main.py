from curl_cffi import requests
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
import time


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_URL = "https://www.sofascore.com/api/v1"

session = requests.Session()

# Cantidad máxima de páginas que se pueden consultar
MAX_PAGINAS_HISTORIAL = 30

# Ventana para considerar "últimos partidos"
# Esto evita que un partido de 2021 aparezca como último partido.
MESES_HISTORIAL_RECIENTE = 12

# Cantidad de H2H que queremos devolver
MAX_H2H = 2


# ============================================================
# PETICIÓN A SOFASCORE
# ============================================================

def obtener_json(url):

    try:

        respuesta = session.get(
            url,
            impersonate="chrome",
            timeout=20,
            headers={
                "Accept": "application/json",
                "Referer": "https://www.sofascore.com/",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/151.0.0.0 Safari/537.36"
                )
            }
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
            "ERROR OBTENIENDO JSON:",
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
# FECHA DE EVENTO
# ============================================================

def obtener_fecha(evento):

    if not evento:
        return None

    timestamp = evento.get(
        "startTimestamp"
    )

    if not timestamp:
        return None

    try:

        return datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc
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
# CONVERTIR FECHA LÍMITE
# ============================================================

def convertir_fecha(fecha_limite):

    if isinstance(
        fecha_limite,
        datetime
    ):

        if fecha_limite.tzinfo is None:

            return fecha_limite.replace(
                tzinfo=timezone.utc
            )

        return fecha_limite

    try:

        return datetime.strptime(
            str(fecha_limite),
            "%Y-%m-%d"
        ).replace(
            tzinfo=timezone.utc
        )

    except Exception:

        return None


# ============================================================
# EVENTO ANTES DE FECHA
# ============================================================

def es_anterior_a_fecha(
    evento,
    fecha_limite
):

    fecha_evento = obtener_fecha(
        evento
    )

    fecha_limite_dt = convertir_fecha(
        fecha_limite
    )

    if not fecha_evento:
        return False

    if not fecha_limite_dt:
        return False

    return fecha_evento < fecha_limite_dt


# ============================================================
# ESTADO
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
# NOMBRE DE LIGA
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

    if unique:

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

    if tournament:

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

        if unique:

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
        .replace("-", " ")
        .replace("_", " ")
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

    nombre_evento = normalizar_texto(
        obtener_nombre_liga(evento)
    )

    liga_buscada = normalizar_texto(
        liga
    )

    print(
        "LIGA EVENTO:",
        repr(nombre_evento),
        "| LIGA BUSCADA:",
        repr(liga_buscada)
    )

    if not nombre_evento:
        return False

    if not liga_buscada:
        return False

    # Exacta
    if nombre_evento == liga_buscada:
        return True

    # Parcial
    if (
        liga_buscada in nombre_evento
        or
        nombre_evento in liga_buscada
    ):
        return True

    return False


# ============================================================
# HISTORIAL DEL EQUIPO
# ============================================================

def obtener_historial(team_id):

    partidos = []

    ids_vistos = set()

    pagina = 0

    while pagina < MAX_PAGINAS_HISTORIAL:

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
            f"EQUIPO {team_id} | "
            f"PÁGINA {pagina} | "
            f"EVENTOS: {len(eventos)}"
        )

        nuevos = 0

        for evento in eventos:

            event_id = evento.get(
                "id"
            )

            if event_id:

                if event_id in ids_vistos:
                    continue

                ids_vistos.add(
                    event_id
                )

            partidos.append(
                evento
            )

            nuevos += 1

        print(
            "NUEVOS EVENTOS:",
            nuevos
        )

        has_next = datos.get(
            "hasNextPage",
            False
        )

        if not has_next:
            break

        pagina += 1

        # Evitar bombardear la API
        time.sleep(0.15)

    return partidos


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
# ORDENAR EVENTOS
# ============================================================

def ordenar_por_fecha_descendente(eventos):

    return sorted(
        eventos,
        key=lambda evento:
        evento.get(
            "startTimestamp",
            0
        ),
        reverse=True
    )


# ============================================================
# ELIMINAR DUPLICADOS
# ============================================================

def eliminar_duplicados(eventos):

    unicos = {}

    for evento in eventos:

        event_id = evento.get(
            "id"
        )

        if event_id:

            unicos[event_id] = evento

    return list(
        unicos.values()
    )


# ============================================================
# OBTENER ESTADÍSTICAS DE UN EVENTO
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

    event_id = evento.get(
        "id"
    )

    if not event_id:

        return resultado

    url = (
        f"{BASE_URL}/event/"
        f"{event_id}/statistics"
    )

    print(
        "BUSCANDO ESTADÍSTICAS:",
        event_id
    )

    datos = obtener_json(
        url
    )

    if not datos:

        print(
            "NO HAY DATOS DE ESTADÍSTICAS:",
            event_id
        )

        return resultado

    periodos = datos.get(
        "statistics",
        []
    )

    if not periodos:

        print(
            "SOFASCORE NO DEVOLVIÓ PERIODOS:",
            event_id
        )

        return resultado

    # ========================================================
    # BUSCAR PERIODO ALL
    # ========================================================

    periodo = None

    for item in periodos:

        if str(
            item.get("period", "")
        ).upper() == "ALL":

            periodo = item

            break

    # Si no existe ALL, tomar el primero
    if periodo is None:

        periodo = periodos[0]

    grupos = periodo.get(
        "groups",
        []
    )

    estadisticas = {}

    for grupo in grupos:

        items = grupo.get(
            "statisticsItems",
            []
        )

        for item in items:

            nombre = normalizar_texto(
                item.get(
                    "name",
                    ""
                )
            )

            key = normalizar_texto(
                item.get(
                    "key",
                    ""
                )
            )

            if nombre:

                estadisticas[
                    nombre
                ] = item

            if key:

                estadisticas[
                    key
                ] = item

    # ========================================================
    # POSIBLES NOMBRES
    # ========================================================

    equivalencias = {

        "Posesión": [
            "ball possession",
            "possession",
            "ball possession percentage"
        ],

        "Córners": [
            "corner kicks",
            "corners",
            "corner"
        ],

        "Faltas": [
            "fouls",
            "foul"
        ],

        "Tarjetas amarillas": [
            "yellow cards",
            "yellow card"
        ],

        "Tiros a puerta": [
            "shots on target",
            "shots on goal"
        ],

        "Fueras de juego": [
            "offsides",
            "offside"
        ]
    }

    for nombre_salida, posibles in equivalencias.items():

        item_encontrado = None

        for posible in posibles:

            posible_normalizado = normalizar_texto(
                posible
            )

            if posible_normalizado in estadisticas:

                item_encontrado = estadisticas[
                    posible_normalizado
                ]

                break

        if not item_encontrado:
            continue

        local = item_encontrado.get(
            "home"
        )

        visitante = item_encontrado.get(
            "away"
        )

        # Algunos formatos pueden utilizar homeValue/awayValue
        if local is None:

            local = item_encontrado.get(
                "homeValue"
            )

        if visitante is None:

            visitante = item_encontrado.get(
                "awayValue"
            )

        if (
            local is not None
            or
            visitante is not None
        ):

            resultado[
                nombre_salida
            ] = (
                local,
                visitante
            )

    print(
        "ESTADÍSTICAS ENCONTRADAS:",
        resultado
    )

    return resultado


# ============================================================
# AGREGAR ESTADÍSTICAS A H2H
# ============================================================

def agregar_estadisticas_h2h(eventos):

    resultado = []

    for evento in eventos:

        evento_copia = dict(
            evento
        )

        evento_copia[
            "estadisticas"
        ] = obtener_estadisticas(
            evento
        )

        resultado.append(
            evento_copia
        )

    return resultado


# ============================================================
# H2H DESDE HISTORIALES
#
# IMPORTANTE:
# Aquí NO ponemos una ventana de 12 meses.
#
# H2H puede ser antiguo.
# Lo importante es que:
# - sea entre los dos equipos
# - sea antes del partido
# - pertenezca a la liga
# - esté finalizado
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
    # HISTORIAL A
    # ========================================================

    for evento in historial_a:

        if not es_enfrentamiento(
            evento,
            equipo_a_id,
            equipo_b_id
        ):
            continue

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

        candidatos.append(
            evento
        )

    # ========================================================
    # HISTORIAL B
    # ========================================================

    for evento in historial_b:

        if not es_enfrentamiento(
            evento,
            equipo_a_id,
            equipo_b_id
        ):
            continue

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

        candidatos.append(
            evento
        )

    candidatos = eliminar_duplicados(
        candidatos
    )

    candidatos = ordenar_por_fecha_descendente(
        candidatos
    )

    print(
        "H2H ENCONTRADOS EN HISTORIALES:",
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
            "|",
            obtener_nombre_liga(evento)
        )

    return candidatos


# ============================================================
# OBTENER EVENTO BASE PARA H2H
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

    if candidatos:

        return candidatos[0]

    return None


# ============================================================
# H2H DIRECTO DESDE SOFASCORE
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
        "===================================="
    )

    datos = obtener_json(
        url
    )

    if not datos:

        print(
            "NO SE OBTUVO H2H DIRECTO"
        )

        return []

    eventos = datos.get(
        "events",
        []
    )

    encontrados = []

    ids = set()

    for evento in eventos:

        if not evento:
            continue

        if not es_enfrentamiento(
            evento,
            equipo_a_id,
            equipo_b_id
        ):
            continue

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

        event_id_actual = evento.get(
            "id"
        )

        if event_id_actual:

            if event_id_actual in ids:
                continue

            ids.add(
                event_id_actual
            )

        encontrados.append(
            evento
        )

    encontrados = ordenar_por_fecha_descendente(
        encontrados
    )

    print(
        "H2H DIRECTOS ENCONTRADOS:",
        len(encontrados)
    )

    return encontrados


# ============================================================
# OBTENER H2H FINAL
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
    # PRIMERA FUENTE:
    # historial de ambos equipos
    #
    # Esto es importante porque permite encontrar H2H
    # pertenecientes específicamente a la liga seleccionada.
    # ========================================================

    candidatos_historial = obtener_h2h_desde_historiales(
        historial_a,
        historial_b,
        equipo_a_id,
        equipo_b_id,
        liga,
        fecha_limite
    )

    # ========================================================
    # SEGUNDA FUENTE:
    # endpoint H2H de Sofascore
    # ========================================================

    evento_base = None

    if candidatos_historial:

        evento_base = candidatos_historial[0]

    if evento_base:

        candidatos_api = obtener_h2h_desde_sofascore(
            evento_base,
            equipo_a_id,
            equipo_b_id,
            liga,
            fecha_limite
        )

        # Combinar las dos fuentes
        candidatos_historial.extend(
            candidatos_api
        )

    # ========================================================
    # ELIMINAR DUPLICADOS
    # ========================================================

    candidatos = eliminar_duplicados(
        candidatos_historial
    )

    # ========================================================
    # ORDENAR POR FECHA
    # ========================================================

    candidatos = ordenar_por_fecha_descendente(
        candidatos
    )

    # ========================================================
    # TOMAR LOS 2 MÁS RECIENTES
    # ========================================================

    h2h_final = candidatos[
        :MAX_H2H
    ]

    print(
        "===================================="
    )

    print(
        "H2H FINALES:",
        len(h2h_final)
    )

    for evento in h2h_final:

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

    # ========================================================
    # OBTENER ESTADÍSTICAS DE CADA H2H
    # ========================================================

    h2h_con_estadisticas = []

    for evento in h2h_final:

        evento_copia = dict(
            evento
        )

        evento_copia[
            "estadisticas"
        ] = obtener_estadisticas(
            evento
        )

        h2h_con_estadisticas.append(
            evento_copia
        )

    return h2h_con_estadisticas


# ============================================================
# FECHA MÍNIMA PARA PARTIDOS RECIENTES
# ============================================================

def obtener_fecha_minima_reciente(
    fecha_limite
):

    fecha = convertir_fecha(
        fecha_limite
    )

    if not fecha:

        return None

    # Aproximadamente 12 meses
    return fecha - timedelta(
        days=365
    )


# ============================================================
# FILTRAR HISTORIAL RECIENTE
# ============================================================

def es_reciente(
    evento,
    fecha_limite
):

    fecha_evento = obtener_fecha(
        evento
    )

    fecha_limite_dt = convertir_fecha(
        fecha_limite
    )

    fecha_minima = obtener_fecha_minima_reciente(
        fecha_limite
    )

    if not fecha_evento:
        return False

    if not fecha_limite_dt:
        return False

    if not fecha_minima:
        return False

    if fecha_evento >= fecha_limite_dt:
        return False

    if fecha_evento < fecha_minima:
        return False

    return True


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

        if not es_reciente(
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

    candidatos = ordenar_por_fecha_descendente(
        candidatos
    )

    if candidatos:

        print(
            "ÚLTIMO LOCAL:",
            obtener_fecha_date(
                candidatos[0]
            )
        )

        return candidatos[0]

    print(
        "NO SE ENCONTRÓ LOCAL RECIENTE"
    )

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

        if not es_reciente(
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

    candidatos = ordenar_por_fecha_descendente(
        candidatos
    )

    if candidatos:

        print(
            "ÚLTIMO VISITANTE:",
            obtener_fecha_date(
                candidatos[0]
            )
        )

        return candidatos[0]

    print(
        "NO SE ENCONTRÓ VISITANTE RECIENTE"
    )

    return None


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

    if not id_a or not id_b:

        return {
            "error":
            "No se pudieron obtener los IDs de los equipos."
        }

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
        "FECHA PARTIDO:",
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
    # SIN límite artificial de 12 meses.
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
    # ÚLTIMO LOCAL A
    # ========================================================

    local_a = ultimo_local(
        historial_a,
        id_a,
        fecha_partido,
        liga
    )

    # ========================================================
    # ÚLTIMO VISITANTE A
    # ========================================================

    visitante_a = ultimo_visitante(
        historial_a,
        id_a,
        fecha_partido,
        liga
    )

    # ========================================================
    # ÚLTIMO LOCAL B
    # ========================================================

    local_b = ultimo_local(
        historial_b,
        id_b,
        fecha_partido,
        liga
    )

    # ========================================================
    # ÚLTIMO VISITANTE B
    # ========================================================

    visitante_b = ultimo_visitante(
        historial_b,
        id_b,
        fecha_partido,
        liga
    )

    # ========================================================
    # RESULTADO DEBUG
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
        if local_a
        else None
    )

    print(
        "VISITANTE A:",
        obtener_fecha_date(visitante_a)
        if visitante_a
        else None
    )

    print(
        "LOCAL B:",
        obtener_fecha_date(local_b)
        if local_b
        else None
    )

    print(
        "VISITANTE B:",
        obtener_fecha_date(visitante_b)
        if visitante_b
        else None
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