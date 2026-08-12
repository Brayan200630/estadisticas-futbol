import streamlit as st
from datetime import date, datetime
from curl_cffi import requests
from urllib.parse import quote
import streamlit.components.v1 as components

from main import analizar_partido, obtener_estadisticas


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Estadísticas de Fútbol",
    page_icon="⚽",
    layout="centered"
)

BASE_URL = "https://www.sofascore.com/api/v1"


# ============================================================
# SESIÓN SOFASCORE
# ============================================================

session = requests.Session()


# ============================================================
# PETICIÓN A SOFASCORE
# ============================================================

@st.cache_data(ttl=3600)
def obtener_json_app(url):

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
# BUSCAR EQUIPOS
# ============================================================

@st.cache_data(ttl=3600)
def buscar_equipos_app(nombre):

    if not nombre:
        return []

    url = (
        f"{BASE_URL}/search/all"
        f"?q={quote(nombre)}"
    )

    datos = obtener_json_app(url)

    if not datos:
        return []

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

    # ========================================================
    # ELIMINAR DUPLICADOS
    # ========================================================

    unicos = {}

    for equipo in equipos:

        if equipo["id"]:

            unicos[
                equipo["id"]
            ] = equipo

    return list(
        unicos.values()
    )


# ============================================================
# BUSCAR TORNEOS / LIGAS
# ============================================================

@st.cache_data(ttl=3600)
def buscar_ligas_app(nombre):

    if not nombre:
        return []

    url = (
        f"{BASE_URL}/search/all"
        f"?q={quote(nombre)}"
    )

    datos = obtener_json_app(url)

    if not datos:
        return []

    resultados = datos.get(
        "results",
        []
    )

    ligas = []

    for resultado in resultados:

        tipo = resultado.get(
            "type"
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

        nombre_liga = entidad.get(
            "name"
        )

        # ----------------------------------------------------
        # Algunos resultados pueden tener uniqueTournament
        # dentro de entity.
        # ----------------------------------------------------

        if not tournament_id:

            unique = entidad.get(
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

                if not nombre_liga:

                    nombre_liga = unique.get(
                        "name"
                    )

        if not tournament_id or not nombre_liga:
            continue

        pais = ""

        category = entidad.get(
            "category",
            {}
        )

        if isinstance(
            category,
            dict
        ):

            pais = category.get(
                "name",
                ""
            )

        item = {
            "id": tournament_id,
            "name": nombre_liga,
            "country": pais
        }

        existe = False

        for liga in ligas:

            if liga["id"] == tournament_id:

                existe = True
                break

        if not existe:

            ligas.append(
                item
            )

    return ligas


# ============================================================
# FUNCIONES DE FORMATO
# ============================================================

def formatear_fecha(evento):

    if not evento:
        return "Fecha no disponible"

    timestamp = evento.get(
        "startTimestamp"
    )

    if timestamp is None:
        return "Fecha no disponible"

    try:

        return datetime.fromtimestamp(
            int(timestamp)
        ).strftime(
            "%d/%m/%Y"
        )

    except Exception:

        return "Fecha no disponible"


def formatear_fecha_hora(evento):

    if not evento:
        return "Fecha no disponible"

    timestamp = evento.get(
        "startTimestamp"
    )

    if timestamp is None:
        return "Fecha no disponible"

    try:

        return datetime.fromtimestamp(
            int(timestamp)
        ).strftime(
            "%d/%m/%Y %H:%M"
        )

    except Exception:

        return "Fecha no disponible"


# ============================================================
# OBTENER RESULTADO
# ============================================================

def obtener_resultado(evento):

    if not evento:
        return None

    home_score = evento.get(
        "homeScore",
        {}
    )

    away_score = evento.get(
        "awayScore",
        {}
    )

    if not isinstance(
        home_score,
        dict
    ):

        home_score = {}

    if not isinstance(
        away_score,
        dict
    ):

        away_score = {}

    # ========================================================
    # RESULTADO ACTUAL
    # ========================================================

    home_current = home_score.get(
        "current"
    )

    away_current = away_score.get(
        "current"
    )

    # ========================================================
    # PENALES
    # ========================================================

    home_penalty = home_score.get(
        "penalties"
    )

    away_penalty = away_score.get(
        "penalties"
    )

    # ========================================================
    # PARTIDO DECIDIDO POR PENALES
    # ========================================================

    if (
        home_penalty is not None
        and
        away_penalty is not None
    ):

        home_regular = home_score.get(
            "normaltime"
        )

        away_regular = away_score.get(
            "normaltime"
        )

        # ----------------------------------------------------
        # RESPALDO: OVERTIME
        # ----------------------------------------------------

        if (
            home_regular is None
            or
            away_regular is None
        ):

            home_regular = home_score.get(
                "overtime"
            )

            away_regular = away_score.get(
                "overtime"
            )

        # ----------------------------------------------------
        # RESPALDO: PERIOD1
        # ----------------------------------------------------

        if (
            home_regular is None
            or
            away_regular is None
        ):

            home_regular = home_score.get(
                "period1"
            )

            away_regular = away_score.get(
                "period1"
            )

        # ----------------------------------------------------
        # ÚLTIMO RESPALDO
        # ----------------------------------------------------

        if (
            home_regular is None
            or
            away_regular is None
        ):

            home_regular = home_current
            away_regular = away_current

        if (
            home_regular is not None
            and
            away_regular is not None
        ):

            return (
                f"{home_regular} "
                f"({home_penalty}) - "
                f"{away_regular} "
                f"({away_penalty})"
            )

    # ========================================================
    # RESULTADO NORMAL
    # ========================================================

    if (
        home_current is not None
        and
        away_current is not None
    ):

        return (
            f"{home_current} - "
            f"{away_current}"
        )

    return None


# ============================================================
# OBTENER NOMBRE DEL TORNEO
# ============================================================

def obtener_torneo(evento):

    if not evento:
        return None

    torneo = (
        evento
        .get("uniqueTournament", {})
        .get("name")
    )

    if not torneo:

        torneo = (
            evento
            .get("tournament", {})
            .get("name")
        )

    return torneo


# ============================================================
# OBTENER EQUIPOS
# ============================================================

def obtener_nombres_equipos(evento):

    if not evento:
        return (
            "Desconocido",
            "Desconocido"
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

    return local, visitante


# ============================================================
# MOSTRAR ESTADÍSTICAS
# ============================================================

def mostrar_estadisticas(evento):

    if not evento:

        return

    local, visitante = (
        obtener_nombres_equipos(evento)
    )

    estadisticas = obtener_estadisticas(
        evento
    )

    st.markdown(
        "### ESTADÍSTICAS"
    )

    # ========================================================
    # POSESIÓN
    # ========================================================

    posesion = estadisticas.get(
        "Posesión"
    )

    if posesion:

        st.write(
            f"Posesión: "
            f"{local} {posesion[0]} - "
            f"{posesion[1]} {visitante}"
        )

    else:

        st.write(
            "Posesión: Datos no disponibles"
        )

    # ========================================================
    # CÓRNERS
    # ========================================================

    corners = estadisticas.get(
        "Córners"
    )

    if corners:

        st.write(
            f"Córners: "
            f"{local} {corners[0]} - "
            f"{corners[1]} {visitante}"
        )

    else:

        st.write(
            "Córners: Datos no disponibles"
        )

    # ========================================================
    # FALTAS
    # ========================================================

    faltas = estadisticas.get(
        "Faltas"
    )

    if faltas:

        st.write(
            f"Faltas: "
            f"{local} {faltas[0]} - "
            f"{faltas[1]} {visitante}"
        )

    else:

        st.write(
            "Faltas: Datos no disponibles"
        )

    # ========================================================
    # TARJETAS
    # ========================================================

    tarjetas = estadisticas.get(
        "Tarjetas amarillas"
    )

    if tarjetas:

        st.write(
            f"Tarjetas amarillas: "
            f"{local} {tarjetas[0]} - "
            f"{tarjetas[1]} {visitante}"
        )

    else:

        st.write(
            "Tarjetas amarillas: "
            "Datos no disponibles"
        )

    # ========================================================
    # TIROS A PUERTA
    # ========================================================

    tiros = estadisticas.get(
        "Tiros a puerta"
    )

    if tiros:

        st.write(
            f"Tiros a puerta: "
            f"{local} {tiros[0]} - "
            f"{tiros[1]} {visitante}"
        )

    else:

        st.write(
            "Tiros a puerta: Datos no disponibles"
        )

    # ========================================================
    # FUERAS DE JUEGO
    # ========================================================

    fueras = estadisticas.get(
        "Fueras de juego"
    )

    if fueras:

        st.write(
            f"Fueras de juego: "
            f"{local} {fueras[0]} - "
            f"{fueras[1]} {visitante}"
        )

    else:

        st.write(
            "Fueras de juego: Datos no disponibles"
        )


# ============================================================
# MOSTRAR GOLES
# ============================================================

def mostrar_goles(evento):

    goles = evento.get(
        "goals",
        []
    )

    if not goles:
        return

    st.markdown(
        "### GOLES"
    )

    for gol in goles:

        minuto = gol.get(
            "time"
        )

        jugador = gol.get(
            "player",
            {}
        )

        if isinstance(
            jugador,
            dict
        ):

            nombre = jugador.get(
                "name",
                "Jugador desconocido"
            )

        else:

            nombre = str(jugador)

        equipo = gol.get(
            "isHome"
        )

        if equipo is True:

            equipo_nombre = (
                evento
                .get("homeTeam", {})
                .get("name", "")
            )

        else:

            equipo_nombre = (
                evento
                .get("awayTeam", {})
                .get("name", "")
            )

        tipo = gol.get(
            "incidentType",
            "regular"
        )

        if tipo == "penalty":

            tipo_texto = "penal"

        elif tipo == "ownGoal":

            tipo_texto = "autogol"

        else:

            tipo_texto = "regular"

        st.write(
            f"{minuto}' {nombre} "
            f"({equipo_nombre}) — "
            f"{tipo_texto}"
        )


# ============================================================
# MOSTRAR ALINEACIONES
# ============================================================

def mostrar_alineaciones(evento):

    lineups = evento.get(
        "lineups"
    )

    if not lineups:
        return

    st.markdown(
        "### ALINEACIONES"
    )

    # ========================================================
    # EQUIPO LOCAL
    # ========================================================

    home_team = evento.get(
        "homeTeam",
        {}
    )

    away_team = evento.get(
        "awayTeam",
        {}
    )

    home_name = home_team.get(
        "name",
        "Local"
    )

    away_name = away_team.get(
        "name",
        "Visitante"
    )

    # --------------------------------------------------------
    # Función interna
    # --------------------------------------------------------

    def mostrar_equipo_alineacion(
        nombre_equipo,
        datos_equipo
    ):

        if not datos_equipo:
            return

        st.write(
            nombre_equipo
        )

        formacion = datos_equipo.get(
            "formation"
        )

        if formacion:

            st.write(
                f"Formación: {formacion}"
            )

        titulares = datos_equipo.get(
            "players",
            []
        )

        titulares_lista = []

        suplentes_lista = []

        for jugador in titulares:

            if not isinstance(
                jugador,
                dict
            ):
                continue

            jugador_data = jugador.get(
                "player",
                {}
            )

            if not isinstance(
                jugador_data,
                dict
            ):

                jugador_data = {}

            nombre = jugador_data.get(
                "name",
                "Jugador desconocido"
            )

            shirt = jugador_data.get(
                "shirtNumber"
            )

            position = jugador.get(
                "position"
            )

            texto = ""

            if shirt is not None:

                texto += f"#{shirt} "

            texto += nombre

            if position:

                texto += f" ({position})"

            titular = jugador.get(
                "substitute",
                False
            )

            if titular:

                suplentes_lista.append(
                    texto
                )

            else:

                titulares_lista.append(
                    texto
                )

        if titulares_lista:

            st.write(
                "Titulares: "
                +
                ", ".join(
                    titulares_lista
                )
            )

        if suplentes_lista:

            st.write(
                "Suplentes: "
                +
                ", ".join(
                    suplentes_lista
                )
            )

    # ========================================================
    # DATOS DEL LOCAL
    # ========================================================

    home_lineup = lineups.get(
        "home"
    )

    away_lineup = lineups.get(
        "away"
    )

    if home_lineup:

        mostrar_equipo_alineacion(
            home_name,
            home_lineup
        )

    if away_lineup:

        mostrar_equipo_alineacion(
            away_name,
            away_lineup
        )


# ============================================================
# MOSTRAR CAMBIOS
# ============================================================

def mostrar_cambios(evento):

    cambios = evento.get(
        "substitutions"
    )

    if not cambios:
        return

    st.markdown(
        "### CAMBIOS"
    )

    if isinstance(
        cambios,
        dict
    ):

        for lado, lista in cambios.items():

            if not isinstance(
                lista,
                list
            ):
                continue

            if lado == "home":

                nombre_equipo = (
                    evento
                    .get("homeTeam", {})
                    .get("name", "Local")
                )

            elif lado == "away":

                nombre_equipo = (
                    evento
                    .get("awayTeam", {})
                    .get("name", "Visitante")
                )

            else:

                nombre_equipo = lado

            for cambio in lista:

                if not isinstance(
                    cambio,
                    dict
                ):
                    continue

                minuto = cambio.get(
                    "time",
                    "?"
                )

                jugador_entrante = cambio.get(
                    "playerIn",
                    {}
                )

                jugador_saliente = cambio.get(
                    "playerOut",
                    {}
                )

                if isinstance(
                    jugador_entrante,
                    dict
                ):

                    nombre_entrante = (
                        jugador_entrante.get(
                            "name",
                            "Desconocido"
                        )
                    )

                else:

                    nombre_entrante = str(
                        jugador_entrante
                    )

                if isinstance(
                    jugador_saliente,
                    dict
                ):

                    nombre_saliente = (
                        jugador_saliente.get(
                            "name",
                            "Desconocido"
                        )
                    )

                else:

                    nombre_saliente = str(
                        jugador_saliente
                    )

                st.write(
                    f"{minuto}' "
                    f"{nombre_equipo}: "
                    f"entró {nombre_entrante} "
                    f"por {nombre_saliente}"
                )


# ============================================================
# MOSTRAR PARTIDO
# ============================================================

def mostrar_partido(evento):

    if not evento:

        st.info(
            "No se encontró un partido válido."
        )

        return

    local, visitante = (
        obtener_nombres_equipos(evento)
    )

    fecha_formateada = formatear_fecha(
        evento
    )

    torneo = obtener_torneo(
        evento
    )

    resultado = obtener_resultado(
        evento
    )

    st.write(
        f"Fecha: {fecha_formateada}"
    )

    st.write(
        f"Partido: {local} vs {visitante}"
    )

    if torneo:

        st.write(
            f"Competición: {torneo}"
        )

    if resultado:

        st.write(
            f"Resultado: {resultado}"
        )

    mostrar_goles(
        evento
    )

    mostrar_alineaciones(
        evento
    )

    mostrar_cambios(
        evento
    )

    mostrar_estadisticas(
        evento
    )


# ============================================================
# TEXTO COPIABLE
# ============================================================

def generar_texto_copiable(
    datos,
    nombre_a,
    nombre_b,
    liga
):

    lineas = []

    # ========================================================
    # INFORMACIÓN GENERAL
    # ========================================================

    lineas.append(
        f"Equipos: {nombre_a} vs {nombre_b}"
    )

    lineas.append(
        f"Liga: {liga}"
    )

    lineas.append("")

    # ========================================================
    # FUNCIÓN PARA CONSTRUIR PARTIDO
    # ========================================================

    def texto_partido(
        titulo,
        evento
    ):

        resultado = []

        resultado.append(
            titulo
        )

        resultado.append(
            ""
        )

        if not evento:

            resultado.append(
                "No se encontró un partido válido."
            )

            resultado.append(
                ""
            )

            return resultado

        local, visitante = (
            obtener_nombres_equipos(
                evento
            )
        )

        fecha = formatear_fecha(
            evento
        )

        torneo = obtener_torneo(
            evento
        )

        marcador = obtener_resultado(
            evento
        )

        resultado.append(
            f"Fecha: {fecha}"
        )

        resultado.append(
            f"Partido: {local} vs {visitante}"
        )

        if torneo:

            resultado.append(
                f"Competición: {torneo}"
            )

        if marcador:

            resultado.append(
                f"Resultado: {marcador}"
            )

        # ====================================================
        # GOLES
        # ====================================================

        goles = evento.get(
            "goals",
            []
        )

        if goles:

            resultado.append(
                ""
            )

            resultado.append(
                "GOLES"
            )

            for gol in goles:

                minuto = gol.get(
                    "time"
                )

                jugador = gol.get(
                    "player",
                    {}
                )

                if isinstance(
                    jugador,
                    dict
                ):

                    jugador_nombre = (
                        jugador.get(
                            "name",
                            "Jugador desconocido"
                        )
                    )

                else:

                    jugador_nombre = str(
                        jugador
                    )

                if gol.get("isHome"):

                    equipo_nombre = local

                else:

                    equipo_nombre = visitante

                tipo = gol.get(
                    "incidentType",
                    "regular"
                )

                if tipo == "penalty":

                    tipo_texto = "penal"

                elif tipo == "ownGoal":

                    tipo_texto = "autogol"

                else:

                    tipo_texto = "regular"

                resultado.append(
                    f"{minuto}' "
                    f"{jugador_nombre} "
                    f"({equipo_nombre}) — "
                    f"{tipo_texto}"
                )

        # ====================================================
        # ALINEACIONES
        # ====================================================

        lineups = evento.get(
            "lineups"
        )

        if lineups:

            resultado.append(
                ""
            )

            resultado.append(
                "ALINEACIONES"
            )

            def construir_alineacion(
                nombre_equipo,
                datos_equipo
            ):

                bloque = []

                if not datos_equipo:
                    return bloque

                bloque.append(
                    nombre_equipo
                )

                formacion = datos_equipo.get(
                    "formation"
                )

                if formacion:

                    bloque.append(
                        f"Formación: {formacion}"
                    )

                jugadores = datos_equipo.get(
                    "players",
                    []
                )

                titulares = []
                suplentes = []

                for jugador in jugadores:

                    if not isinstance(
                        jugador,
                        dict
                    ):
                        continue

                    jugador_data = jugador.get(
                        "player",
                        {}
                    )

                    if not isinstance(
                        jugador_data,
                        dict
                    ):

                        jugador_data = {}

                    nombre = jugador_data.get(
                        "name",
                        "Jugador desconocido"
                    )

                    dorsal = jugador_data.get(
                        "shirtNumber"
                    )

                    posicion = jugador.get(
                        "position"
                    )

                    texto = ""

                    if dorsal is not None:

                        texto += (
                            f"#{dorsal} "
                        )

                    texto += nombre

                    if posicion:

                        texto += (
                            f" ({posicion})"
                        )

                    if jugador.get(
                        "substitute",
                        False
                    ):

                        suplentes.append(
                            texto
                        )

                    else:

                        titulares.append(
                            texto
                        )

                if titulares:

                    bloque.append(
                        "Titulares: "
                        +
                        ", ".join(
                            titulares
                        )
                    )

                if suplentes:

                    bloque.append(
                        "Suplentes: "
                        +
                        ", ".join(
                            suplentes
                        )
                    )

                return bloque

            home_lineup = lineups.get(
                "home"
            )

            away_lineup = lineups.get(
                "away"
            )

            if home_lineup:

                resultado.extend(
                    construir_alineacion(
                        local,
                        home_lineup
                    )
                )

            if away_lineup:

                resultado.extend(
                    construir_alineacion(
                        visitante,
                        away_lineup
                    )
                )

        # ====================================================
        # CAMBIOS
        # ====================================================

        cambios = evento.get(
            "substitutions"
        )

        if cambios:

            resultado.append(
                ""
            )

            resultado.append(
                "CAMBIOS"
            )

            if isinstance(
                cambios,
                dict
            ):

                for lado, lista in cambios.items():

                    if not isinstance(
                        lista,
                        list
                    ):
                        continue

                    if lado == "home":

                        nombre_equipo = local

                    elif lado == "away":

                        nombre_equipo = visitante

                    else:

                        nombre_equipo = lado

                    for cambio in lista:

                        if not isinstance(
                            cambio,
                            dict
                        ):
                            continue

                        minuto = cambio.get(
                            "time",
                            "?"
                        )

                        jugador_in = cambio.get(
                            "playerIn",
                            {}
                        )

                        jugador_out = cambio.get(
                            "playerOut",
                            {}
                        )

                        if isinstance(
                            jugador_in,
                            dict
                        ):

                            nombre_in = (
                                jugador_in.get(
                                    "name",
                                    "Desconocido"
                                )
                            )

                        else:

                            nombre_in = str(
                                jugador_in
                            )

                        if isinstance(
                            jugador_out,
                            dict
                        ):

                            nombre_out = (
                                jugador_out.get(
                                    "name",
                                    "Desconocido"
                                )
                            )

                        else:

                            nombre_out = str(
                                jugador_out
                            )

                        resultado.append(
                            f"{minuto}' "
                            f"{nombre_equipo}: "
                            f"entró {nombre_in} "
                            f"por {nombre_out}"
                        )

        # ====================================================
        # ESTADÍSTICAS
        # ====================================================

        estadisticas = obtener_estadisticas(
            evento
        )

        resultado.append(
            ""
        )

        resultado.append(
            "ESTADÍSTICAS"
        )

        posesion = estadisticas.get(
            "Posesión"
        )

        if posesion:

            resultado.append(
                f"Posesión: "
                f"{local} {posesion[0]} - "
                f"{posesion[1]} {visitante}"
            )

        else:

            resultado.append(
                "Posesión: Datos no disponibles"
            )

        corners = estadisticas.get(
            "Córners"
        )

        if corners:

            resultado.append(
                f"Córners: "
                f"{local} {corners[0]} - "
                f"{corners[1]} {visitante}"
            )

        else:

            resultado.append(
                "Córners: Datos no disponibles"
            )

        faltas = estadisticas.get(
            "Faltas"
        )

        if faltas:

            resultado.append(
                f"Faltas: "
                f"{local} {faltas[0]} - "
                f"{faltas[1]} {visitante}"
            )

        else:

            resultado.append(
                "Faltas: Datos no disponibles"
            )

        tarjetas = estadisticas.get(
            "Tarjetas amarillas"
        )

        if tarjetas:

            resultado.append(
                f"Tarjetas amarillas: "
                f"{local} {tarjetas[0]} - "
                f"{tarjetas[1]} {visitante}"
            )

        else:

            resultado.append(
                "Tarjetas amarillas: "
                "Datos no disponibles"
            )

        tiros = estadisticas.get(
            "Tiros a puerta"
        )

        if tiros:

            resultado.append(
                f"Tiros a puerta: "
                f"{local} {tiros[0]} - "
                f"{tiros[1]} {visitante}"
            )

        else:

            resultado.append(
                "Tiros a puerta: Datos no disponibles"
            )

        fueras = estadisticas.get(
            "Fueras de juego"
        )

        if fueras:

            resultado.append(
                f"Fueras de juego: "
                f"{local} {fueras[0]} - "
                f"{fueras[1]} {visitante}"
            )

        else:

            resultado.append(
                "Fueras de juego: "
                "Datos no disponibles"
            )

        resultado.append(
            ""
        )

        return resultado

    # ========================================================
    # PRÓXIMO ENFRENTAMIENTO
    # ========================================================

    proximo_enfrentamiento = datos.get(
        "proximo_enfrentamiento"
    )

    if proximo_enfrentamiento:

        lineas.append(
            "PRÓXIMO ENFRENTAMIENTO"
        )

        lineas.append("")

        lineas.append(
            f"Fecha y hora: "
            f"{formatear_fecha_hora(proximo_enfrentamiento)}"
        )

        local_prox, visitante_prox = (
            obtener_nombres_equipos(
                proximo_enfrentamiento
            )
        )

        lineas.append(
            f"Partido: "
            f"{local_prox} vs {visitante_prox}"
        )

        torneo_prox = obtener_torneo(
            proximo_enfrentamiento
        )

        if torneo_prox:

            lineas.append(
                f"Competición: {torneo_prox}"
            )

        lineas.append("")

    # ========================================================
    # PRÓXIMO PARTIDO EQUIPO A
    # ========================================================

    proximo_a = datos.get(
        "proximo_a"
    )

    if proximo_a:

        lineas.extend(
            texto_partido(
                f"PRÓXIMO PARTIDO DE {nombre_a}",
                proximo_a
            )
        )

    # ========================================================
    # PRÓXIMO PARTIDO EQUIPO B
    # ========================================================

    proximo_b = datos.get(
        "proximo_b"
    )

    if proximo_b:

        lineas.extend(
            texto_partido(
                f"PRÓXIMO PARTIDO DE {nombre_b}",
                proximo_b
            )
        )

    # ========================================================
    # H2H
    # ========================================================

    lineas.append(
        "ENFRENTAMIENTOS DIRECTOS"
    )

    lineas.append("")

    lineas.extend(
        texto_partido(
            f"Último enfrentamiento "
            f"con {nombre_a} como LOCAL",
            datos.get(
                "h2h_a_local"
            )
        )
    )

    lineas.extend(
        texto_partido(
            f"Último enfrentamiento "
            f"con {nombre_a} como VISITANTE",
            datos.get(
                "h2h_a_visitante"
            )
        )
    )

    # ========================================================
    # EQUIPO A
    # ========================================================

    lineas.append(
        nombre_a
    )

    lineas.append("")

    lineas.extend(
        texto_partido(
            "Último partido como LOCAL",
            datos.get(
                "local_a"
            )
        )
    )

    lineas.extend(
        texto_partido(
            "Último partido como VISITANTE",
            datos.get(
                "visitante_a"
            )
        )
    )

    # ========================================================
    # EQUIPO B
    # ========================================================

    lineas.append(
        nombre_b
    )

    lineas.append("")

    lineas.extend(
        texto_partido(
            "Último partido como LOCAL",
            datos.get(
                "local_b"
            )
        )
    )

    lineas.extend(
        texto_partido(
            "Último partido como VISITANTE",
            datos.get(
                "visitante_b"
            )
        )
    )

    return "\n".join(
        lineas
    )


# ============================================================
# BOTÓN COPIAR
# ============================================================

def mostrar_boton_copiar(texto):

    texto_js = (
        texto
        .replace(
            "\\",
            "\\\\"
        )
        .replace(
            "`",
            "\\`"
        )
        .replace(
            "${",
            "\\${"
        )
    )

    html = f"""
    <button
        onclick="copiarTexto()"
        style="
            width: 100%;
            padding: 11px 16px;
            font-size: 16px;
            font-weight: 600;
            border-radius: 8px;
            border: 1px solid #ccc;
            background: white;
            color: black;
            cursor: pointer;
        "
    >
        📋 Copiar texto completo
    </button>

    <script>

    function copiarTexto() {{

        const texto = `{texto_js}`;

        navigator.clipboard.writeText(texto)
            .then(() => {{

                const boton =
                    document.querySelector("button");

                boton.innerText =
                    "Texto copiado";

                setTimeout(() => {{

                    boton.innerText =
                        "📋 Copiar texto completo";

                }}, 2000);

            }})
            .catch(() => {{

                const area =
                    document.createElement("textarea");

                area.value = texto;

                document.body.appendChild(
                    area
                );

                area.select();

                document.execCommand(
                    "copy"
                );

                document.body.removeChild(
                    area
                );

                const boton =
                    document.querySelector("button");

                boton.innerText =
                    "Texto copiado";

                setTimeout(() => {{

                    boton.innerText =
                        "📋 Copiar texto completo";

                }}, 2000);

            }});

    }}

    </script>
    """

    components.html(
        html,
        height=55
    )


# ============================================================
# TÍTULO
# ============================================================

st.title(
    "⚽ Estadísticas de Fútbol"
)

st.write(
    "Consulta estadísticas de los últimos "
    "partidos relevantes de dos equipos."
)


# ============================================================
# EQUIPO A
# ============================================================

st.subheader(
    "Equipo A"
)

busqueda_a = st.text_input(
    "Buscar Equipo A",
    placeholder="Escribe el nombre del equipo...",
    key="busqueda_equipo_a"
)

equipos_a = buscar_equipos_app(
    busqueda_a.strip()
)

opciones_a = [
    f'{equipo["name"]}'
    + (
        f' ({equipo["country"]})'
        if equipo["country"]
        else ""
    )
    for equipo in equipos_a
]

if opciones_a:

    seleccion_a = st.selectbox(
        "Selecciona Equipo A",
        opciones_a,
        key="seleccion_equipo_a"
    )

    indice_a = opciones_a.index(
        seleccion_a
    )

    equipo_a = equipos_a[
        indice_a
    ]["name"]

else:

    equipo_a = ""


# ============================================================
# EQUIPO B
# ============================================================

st.subheader(
    "Equipo B"
)

busqueda_b = st.text_input(
    "Buscar Equipo B",
    placeholder="Escribe el nombre del equipo...",
    key="busqueda_equipo_b"
)

equipos_b = buscar_equipos_app(
    busqueda_b.strip()
)

opciones_b = [
    f'{equipo["name"]}'
    + (
        f' ({equipo["country"]})'
        if equipo["country"]
        else ""
    )
    for equipo in equipos_b
]

if opciones_b:

    seleccion_b = st.selectbox(
        "Selecciona Equipo B",
        opciones_b,
        key="seleccion_equipo_b"
    )

    indice_b = opciones_b.index(
        seleccion_b
    )

    equipo_b = equipos_b[
        indice_b
    ]["name"]

else:

    equipo_b = ""


# ============================================================
# COMPETICIÓN
# ============================================================

st.subheader(
    "Competición"
)

modo_competicion = st.radio(
    "¿Cómo quieres buscar los partidos?",
    [
        "Competición específica",
        "Todas las competiciones"
    ],
    horizontal=True
)


# ============================================================
# LIGA / COPA
# ============================================================

if modo_competicion == "Competición específica":

    busqueda_liga = st.text_input(
        "Buscar Liga / Copa",
        placeholder=(
            "Ejemplo: Liga 1, Libertadores, "
            "Champions League..."
        ),
        key="busqueda_liga"
    )

    ligas = buscar_ligas_app(
        busqueda_liga.strip()
    )

    opciones_ligas = [
        f'{liga_item["name"]}'
        + (
            f' ({liga_item["country"]})'
            if liga_item["country"]
            else ""
        )
        for liga_item in ligas
    ]

    if opciones_ligas:

        seleccion_liga = st.selectbox(
            "Selecciona Liga / Copa",
            opciones_ligas,
            key="seleccion_liga"
        )

        indice_liga = opciones_ligas.index(
            seleccion_liga
        )

        liga = ligas[
            indice_liga
        ]["name"]

    else:

        liga = ""

else:

    liga = "TODAS"

    st.info(
        "Se buscarán los últimos partidos "
        "sin importar si fueron de liga, copa, "
        "competición internacional u otro torneo."
    )


# ============================================================
# FECHA
# ============================================================

fecha_partido = st.date_input(
    "Fecha del partido",
    value=date.today()
)


# ============================================================
# BOTÓN
# ============================================================

if st.button(
    "🔎 Buscar partido",
    use_container_width=True
):

    # ========================================================
    # VALIDACIONES
    # ========================================================

    if not equipo_a.strip():

        st.error(
            "Selecciona o escribe el Equipo A."
        )

        st.stop()

    if not equipo_b.strip():

        st.error(
            "Selecciona o escribe el Equipo B."
        )

        st.stop()

    if (
        modo_competicion
        == "Competición específica"
        and
        not liga.strip()
    ):

        st.error(
            "Selecciona o escribe la liga/copa."
        )

        st.stop()

    # ========================================================
    # RANGO
    # ========================================================

    fecha_inicio = date(
        2020,
        1,
        1
    )

    fecha_fin = fecha_partido

    if fecha_fin <= fecha_inicio:

        st.error(
            "La fecha del partido debe ser "
            "posterior al 01/01/2020."
        )

        st.stop()

    # ========================================================
    # INFORMACIÓN
    # ========================================================

    st.info(
        f"Buscando partidos desde "
        f"**{fecha_inicio.strftime('%d/%m/%Y')}** "
        f"hasta antes del "
        f"**{fecha_fin.strftime('%d/%m/%Y')}**."
    )

    if modo_competicion == "Todas las competiciones":

        st.info(
            "Modo: **todas las competiciones**."
        )

    else:

        st.info(
            f"Competición seleccionada: "
            f"**{liga}**"
        )

    # ========================================================
    # BÚSQUEDA
    # ========================================================

    with st.spinner(
        "Buscando información en Sofascore..."
    ):

        datos = analizar_partido(
            equipo_a.strip(),
            equipo_b.strip(),
            fecha_partido.strftime(
                "%Y-%m-%d"
            ),
            liga.strip()
        )

    # ========================================================
    # ERRORES
    # ========================================================

    if not datos:

        st.error(
            "No se recibieron datos."
        )

        st.stop()

    if "error" in datos:

        st.error(
            datos["error"]
        )

        st.stop()

    # ========================================================
    # NOMBRES
    # ========================================================

    nombre_a = datos.get(
        "equipo_a",
        equipo_a
    )

    nombre_b = datos.get(
        "equipo_b",
        equipo_b
    )

    # ========================================================
    # RESULTADO DE BÚSQUEDA
    # ========================================================

    st.success(
        f"Equipos encontrados: "
        f"{nombre_a} vs {nombre_b}"
    )

    # ========================================================
    # TEXTO COMPLETO
    # ========================================================

    texto_completo = generar_texto_copiable(
        datos,
        nombre_a,
        nombre_b,
        liga
    )

    st.markdown(
        "### 📋 TEXTO COMPLETO"
    )

    mostrar_boton_copiar(
        texto_completo
    )

    # ========================================================
    # PRÓXIMO ENFRENTAMIENTO
    # ========================================================

    proximo_enfrentamiento = datos.get(
        "proximo_enfrentamiento"
    )

    if proximo_enfrentamiento:

        st.divider()

        st.header(
            "🔜 PRÓXIMO ENFRENTAMIENTO"
        )

        st.write(
            f"Fecha y hora: "
            f"{formatear_fecha_hora(proximo_enfrentamiento)}"
        )

        local_prox, visitante_prox = (
            obtener_nombres_equipos(
                proximo_enfrentamiento
            )
        )

        st.write(
            f"Partido: "
            f"{local_prox} vs {visitante_prox}"
        )

        torneo_prox = obtener_torneo(
            proximo_enfrentamiento
        )

        if torneo_prox:

            st.write(
                f"Competición: {torneo_prox}"
            )

    # ========================================================
    # PRÓXIMO PARTIDO EQUIPO A
    # ========================================================

    proximo_a = datos.get(
        "proximo_a"
    )

    if proximo_a:

        st.divider()

        st.header(
            f"🔜 PRÓXIMO PARTIDO DE {nombre_a}"
        )

        mostrar_partido(
            proximo_a
        )

    # ========================================================
    # PRÓXIMO PARTIDO EQUIPO B
    # ========================================================

    proximo_b = datos.get(
        "proximo_b"
    )

    if proximo_b:

        st.divider()

        st.header(
            f"🔜 PRÓXIMO PARTIDO DE {nombre_b}"
        )

        mostrar_partido(
            proximo_b
        )

    # ========================================================
    # H2H
    # ========================================================

    st.divider()

    st.header(
        "🔁 ENFRENTAMIENTOS DIRECTOS"
    )

    # ========================================================
    # H2H LOCAL
    # ========================================================

    st.subheader(
        f"Último enfrentamiento con "
        f"{nombre_a} como LOCAL"
    )

    h2h_a_local = datos.get(
        "h2h_a_local"
    )

    if h2h_a_local:

        mostrar_partido(
            h2h_a_local
        )

    else:

        st.info(
            f"No se encontró un enfrentamiento "
            f"de {nombre_a} como local."
        )

    # ========================================================
    # H2H VISITANTE
    # ========================================================

    st.subheader(
        f"Último enfrentamiento con "
        f"{nombre_a} como VISITANTE"
    )

    h2h_a_visitante = datos.get(
        "h2h_a_visitante"
    )

    if h2h_a_visitante:

        mostrar_partido(
            h2h_a_visitante
        )

    else:

        st.info(
            f"No se encontró un enfrentamiento "
            f"de {nombre_a} como visitante."
        )

    # ========================================================
    # EQUIPO A
    # ========================================================

    st.divider()

    st.header(
        f"⚽ {nombre_a}"
    )

    # ========================================================
    # LOCAL
    # ========================================================

    st.subheader(
        "Último partido como LOCAL"
    )

    local_a = datos.get(
        "local_a"
    )

    if local_a:

        mostrar_partido(
            local_a
        )

    else:

        st.info(
            "No se encontró un partido válido."
        )

    # ========================================================
    # VISITANTE
    # ========================================================

    st.subheader(
        "Último partido como VISITANTE"
    )

    visitante_a = datos.get(
        "visitante_a"
    )

    if visitante_a:

        mostrar_partido(
            visitante_a
        )

    else:

        st.info(
            "No se encontró un partido válido."
        )

    # ========================================================
    # EQUIPO B
    # ========================================================

    st.divider()

    st.header(
        f"⚽ {nombre_b}"
    )

    # ========================================================
    # LOCAL
    # ========================================================

    st.subheader(
        "Último partido como LOCAL"
    )

    local_b = datos.get(
        "local_b"
    )

    if local_b:

        mostrar_partido(
            local_b
        )

    else:

        st.info(
            "No se encontró un partido válido."
        )

    # ========================================================
    # VISITANTE
    # ========================================================

    st.subheader(
        "Último partido como VISITANTE"
    )

    visitante_b = datos.get(
        "visitante_b"
    )

    if visitante_b:

        mostrar_partido(
            visitante_b
        )

    else:

        st.info(
            "No se encontró un partido válido."
        )