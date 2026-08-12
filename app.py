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
# TÍTULO
# ============================================================

st.title(
    "⚽ Estadísticas de Fútbol"
)

st.write(
    "Consulta estadísticas de los últimos partidos "
    "relevantes de dos equipos."
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
# LIGA / COPA ESPECÍFICA
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

    # ========================================================
    # TODAS LAS COMPETICIONES
    #
    # IMPORTANTE:
    # Enviamos "TODAS" al main.py.
    # No dejamos liga vacía.
    # ========================================================

    liga = "TODAS"

    st.info(
        "🌎 Se buscarán los últimos partidos "
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
# FUNCIÓN PARA FORMATEAR FECHA
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


# ============================================================
# FUNCIÓN PARA OBTENER RESULTADO
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
    #
    # Ejemplo:
    #
    # 1 (5) - 1 (4)
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
        # Respaldo: overtime
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
        # Respaldo: period1
        # ----------------------------------------------------

        if (
            home_regular is None
            or
            away_regular is None
        ):

            home_regular = home_score.get(
                "period1"
            )

            away_regular = home_score.get(
                "period1"
            )

        # ----------------------------------------------------
        # Último respaldo
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
# FUNCIÓN PARA MOSTRAR PARTIDO
# ============================================================

def mostrar_partido(evento):

    if not evento:

        st.info(
            "No se encontró un partido válido."
        )

        return

    # ========================================================
    # EQUIPOS
    # ========================================================

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

    # ========================================================
    # FECHA
    # ========================================================

    fecha_formateada = formatear_fecha(
        evento
    )

    # ========================================================
    # TORNEO / LIGA
    # ========================================================

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

    if torneo:

        st.write(
            f"**Liga:** {torneo}"
        )

    # ========================================================
    # FECHA
    # ========================================================

    st.write(
        f"**Fecha:** {fecha_formateada}"
    )

    # ========================================================
    # PARTIDO
    # ========================================================

    st.write(
        f"**Partido:** "
        f"{local} vs {visitante}"
    )

    # ========================================================
    # RESULTADO
    # ========================================================

    resultado = obtener_resultado(
        evento
    )

    if resultado:

        st.write(
            f"**Resultado:** {resultado}"
        )

    # ========================================================
    # ESTADÍSTICAS
    # ========================================================

    estadisticas = obtener_estadisticas(
        evento
    )

    posesion = estadisticas.get(
        "Posesión"
    )

    corners = estadisticas.get(
        "Córners"
    )

    faltas = estadisticas.get(
        "Faltas"
    )

    tarjetas = estadisticas.get(
        "Tarjetas amarillas"
    )

    tiros = estadisticas.get(
        "Tiros a puerta"
    )

    fueras = estadisticas.get(
        "Fueras de juego"
    )

    # ========================================================
    # POSESIÓN
    # ========================================================

    if posesion:

        st.write(
            f"**Posesión:** "
            f"{local} {posesion[0]} - "
            f"{posesion[1]} {visitante}"
        )

    else:

        st.write(
            "**Posesión:** "
            "Datos no disponibles"
        )

    # ========================================================
    # CÓRNERS
    # ========================================================

    if corners:

        st.write(
            f"**Saques de esquina:** "
            f"{local} {corners[0]} - "
            f"{corners[1]} {visitante}"
        )

    else:

        st.write(
            "**Saques de esquina:** "
            "Datos no disponibles"
        )

    # ========================================================
    # FALTAS
    # ========================================================

    if faltas:

        st.write(
            f"**Faltas:** "
            f"{local} {faltas[0]} - "
            f"{faltas[1]} {visitante}"
        )

    else:

        st.write(
            "**Faltas:** "
            "Datos no disponibles"
        )

    # ========================================================
    # TARJETAS
    # ========================================================

    if tarjetas:

        st.write(
            f"**Tarjetas amarillas:** "
            f"{local} {tarjetas[0]} - "
            f"{tarjetas[1]} {visitante}"
        )

    else:

        st.write(
            "**Tarjetas amarillas:** "
            "Datos no disponibles"
        )

    # ========================================================
    # TIROS A PUERTA
    # ========================================================

    if tiros:

        st.write(
            f"**Tiros a puerta:** "
            f"{local} {tiros[0]} - "
            f"{tiros[1]} {visitante}"
        )

    else:

        st.write(
            "**Tiros a puerta:** "
            "Datos no disponibles"
        )

    # ========================================================
    # FUERAS DE JUEGO
    # ========================================================

    if fueras:

        st.write(
            f"**Fueras de juego:** "
            f"{local} {fueras[0]} - "
            f"{fueras[1]} {visitante}"
        )

    else:

        st.write(
            "**Fueras de juego:** "
            "Datos no disponibles"
        )


# ============================================================
# GENERAR TEXTO COMPLETO PARA COPIAR
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
    # FUNCIÓN INTERNA PARA CONSTRUIR PARTIDO
    # ========================================================

    def texto_partido(
        titulo,
        evento
    ):

        resultado = []

        resultado.append(
            titulo
        )

        if not evento:

            resultado.append(
                "No se encontró un partido válido."
            )

            resultado.append("")

            return resultado

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

        fecha = formatear_fecha(
            evento
        )

        marcador = obtener_resultado(
            evento
        )

        estadisticas = obtener_estadisticas(
            evento
        )

        resultado.append(
            f"Fecha: {fecha}"
        )

        resultado.append(
            f"Partido: "
            f"{local} vs {visitante}"
        )

        if torneo:

            resultado.append(
                f"Liga: {torneo}"
            )

        if marcador:

            resultado.append(
                f"Resultado: {marcador}"
            )

        posesion = estadisticas.get(
            "Posesión"
        )

        corners = estadisticas.get(
            "Córners"
        )

        faltas = estadisticas.get(
            "Faltas"
        )

        tarjetas = estadisticas.get(
            "Tarjetas amarillas"
        )

        tiros = estadisticas.get(
            "Tiros a puerta"
        )

        fueras = estadisticas.get(
            "Fueras de juego"
        )

        if posesion:

            resultado.append(
                f"Posesión: "
                f"{local} {posesion[0]} - "
                f"{posesion[1]} {visitante}"
            )

        else:

            resultado.append(
                "Posesión: "
                "Datos no disponibles"
            )

        if corners:

            resultado.append(
                f"Saques de esquina: "
                f"{local} {corners[0]} - "
                f"{corners[1]} {visitante}"
            )

        else:

            resultado.append(
                "Saques de esquina: "
                "Datos no disponibles"
            )

        if faltas:

            resultado.append(
                f"Faltas: "
                f"{local} {faltas[0]} - "
                f"{faltas[1]} {visitante}"
            )

        else:

            resultado.append(
                "Faltas: "
                "Datos no disponibles"
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

        if tiros:

            resultado.append(
                f"Tiros a puerta: "
                f"{local} {tiros[0]} - "
                f"{tiros[1]} {visitante}"
            )

        else:

            resultado.append(
                "Tiros a puerta: "
                "Datos no disponibles"
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

        resultado.append("")

        return resultado

    # ========================================================
    # H2H
    # ========================================================

    lineas.append(
        "🔁 ENFRENTAMIENTOS DIRECTOS"
    )

    lineas.append("")

    lineas.extend(
        texto_partido(
            f"🏠 Último enfrentamiento "
            f"con {nombre_a} como LOCAL",
            datos.get("h2h_a_local")
        )
    )

    lineas.extend(
        texto_partido(
            f"✈️ Último enfrentamiento "
            f"con {nombre_a} como VISITANTE",
            datos.get("h2h_a_visitante")
        )
    )

    # ========================================================
    # EQUIPO A
    # ========================================================

    lineas.append(
        f"⚽ {nombre_a}"
    )

    lineas.append("")

    lineas.extend(
        texto_partido(
            "🏠 Último partido como LOCAL",
            datos.get("local_a")
        )
    )

    lineas.extend(
        texto_partido(
            "✈️ Último partido como VISITANTE",
            datos.get("visitante_a")
        )
    )

    # ========================================================
    # EQUIPO B
    # ========================================================

    lineas.append(
        f"⚽ {nombre_b}"
    )

    lineas.append("")

    lineas.extend(
        texto_partido(
            "🏠 Último partido como LOCAL",
            datos.get("local_b")
        )
    )

    lineas.extend(
        texto_partido(
            "✈️ Último partido como VISITANTE",
            datos.get("visitante_b")
        )
    )

    return "\n".join(
        lineas
    )


# ============================================================
# BOTÓN COPIAR TEXTO
# ============================================================

def mostrar_boton_copiar(texto):

    texto_js = (
        texto
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
    )

    html = f"""
    <button
        onclick="copiarTexto()"
        style="
            width: 100%;
            padding: 10px 16px;
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
                    "✅ Texto copiado";

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
                    "✅ Texto copiado";

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

    # ========================================================
    # IMPORTANTE:
    #
    # SOLAMENTE se exige liga cuando se selecciona
    # "Competición específica".
    #
    # Si es "Todas las competiciones", liga = "TODAS"
    # y no se ejecuta esta validación.
    # ========================================================

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
    # RANGO DE BÚSQUEDA
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
    # INFORMACIÓN DEL RANGO
    # ========================================================

    st.info(
        f"📅 Buscando partidos desde "
        f"**{fecha_inicio.strftime('%d/%m/%Y')}** "
        f"hasta antes del "
        f"**{fecha_fin.strftime('%d/%m/%Y')}**."
    )

    # ========================================================
    # INFORMACIÓN DE COMPETICIÓN
    # ========================================================

    if modo_competicion == "Todas las competiciones":

        st.info(
            "🌎 Modo: **todas las competiciones**. "
            "No se filtrarán los partidos por liga o copa."
        )

    else:

        st.info(
            f"🏆 Competición seleccionada: "
            f"**{liga}**"
        )

    # ========================================================
    # BÚSQUEDA
    # ========================================================

    with st.spinner(
        "Buscando información en Sofascore..."
    ):

        print(
            "===== INICIO DE BUSQUEDA ====="
        )

        print(
            "Equipo A:",
            equipo_a.strip()
        )

        print(
            "Equipo B:",
            equipo_b.strip()
        )

        print(
            "Liga:",
            liga.strip()
        )

        print(
            "Fecha:",
            fecha_partido
        )

        print(
            "Modo:",
            modo_competicion
        )

        print(
            "RANGO:",
            fecha_inicio,
            "->",
            fecha_fin
        )

        datos = analizar_partido(
            equipo_a.strip(),
            equipo_b.strip(),
            fecha_partido.strftime(
                "%Y-%m-%d"
            ),
            liga.strip()
        )

    # ========================================================
    # ERROR
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
    # NOMBRES ENCONTRADOS
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
    # INFORMACIÓN ENCONTRADA
    # ========================================================

    st.success(
        f"Equipos encontrados: "
        f"{nombre_a} vs {nombre_b}"
    )

    if (
        modo_competicion
        == "Todas las competiciones"
    ):

        st.info(
            "Liga: **Todas las competiciones**"
        )

    else:

        st.info(
            f"Liga seleccionada: **{liga}**"
        )

    # ========================================================
    # BOTÓN PARA COPIAR TODO EL TEXTO
    # ========================================================

    texto_completo = generar_texto_copiable(
        datos,
        nombre_a,
        nombre_b,
        liga
    )

    mostrar_boton_copiar(
        texto_completo
    )

    # ========================================================
    # H2H
    # ========================================================

    st.divider()

    st.header(
        "🔁 Enfrentamientos directos"
    )

    # ========================================================
    # H2H EQUIPO A LOCAL
    # ========================================================

    st.subheader(
        f"🏠 Último enfrentamiento "
        f"con {nombre_a} como LOCAL"
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
            "No se encontró un enfrentamiento "
            f"de {nombre_a} como local "
            "dentro del período seleccionado."
        )

    # ========================================================
    # H2H EQUIPO A VISITANTE
    # ========================================================

    st.subheader(
        f"✈️ Último enfrentamiento "
        f"con {nombre_a} como VISITANTE"
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
            "No se encontró un enfrentamiento "
            f"de {nombre_a} como visitante "
            "dentro del período seleccionado."
        )

    # ========================================================
    # EQUIPO A
    # ========================================================

    st.divider()

    st.header(
        f"⚽ {nombre_a}"
    )

    # ========================================================
    # EQUIPO A LOCAL
    # ========================================================

    st.subheader(
        "🏠 Último partido como LOCAL"
    )

    st.write(
        "Las estadísticas fueron las siguientes:"
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
            "No se encontró un partido válido "
            "desde el 01/01/2020 hasta la fecha "
            "seleccionada."
        )

    # ========================================================
    # EQUIPO A VISITANTE
    # ========================================================

    st.subheader(
        "✈️ Último partido como VISITANTE"
    )

    st.write(
        "Las estadísticas fueron las siguientes:"
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
            "No se encontró un partido válido "
            "desde el 01/01/2020 hasta la fecha "
            "seleccionada."
        )

    # ========================================================
    # EQUIPO B
    # ========================================================

    st.divider()

    st.header(
        f"⚽ {nombre_b}"
    )

    # ========================================================
    # EQUIPO B LOCAL
    # ========================================================

    st.subheader(
        "🏠 Último partido como LOCAL"
    )

    st.write(
        "Las estadísticas fueron las siguientes:"
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
            "No se encontró un partido válido "
            "desde el 01/01/2020 hasta la fecha "
            "seleccionada."
        )

    # ========================================================
    # EQUIPO B VISITANTE
    # ========================================================

    st.subheader(
        "✈️ Último partido como VISITANTE"
    )

    st.write(
        "Las estadísticas fueron las siguientes:"
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
            "No se encontró un partido válido "
            "desde el 01/01/2020 hasta la fecha "
            "seleccionada."
        )