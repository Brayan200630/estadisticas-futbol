import streamlit as st
from main import analizar_partido, obtener_estadisticas, obtener_fecha

# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Analizador de Partidos - SofaScore",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Analizador Estadístico de Partidos")
st.markdown("Herramienta para comparar enfrentamientos previos (H2H) y últimos partidos como local/visitante filtrados por liga.")

# ============================================================
# FORMULARIO DE ENTRADA
# ============================================================
with st.form("form_analisis"):
    col1, col2 = st.columns(2)
    
    with col1:
        equipo_a = st.text_input("Equipo Local (Equipo A)", placeholder="Ej. Alianza Lima")
        liga = st.text_input("Liga / Torneo", placeholder="Ej. Liga 1")
        
    with col2:
        equipo_b = st.text_input("Equipo Visitante (Equipo B)", placeholder="Ej. Universitario")
        fecha_partido = st.date_input("Fecha Límite del Partido")
        
    submitted = st.form_submit_button("🔍 Analizar Partido", use_container_width=True)

# ============================================================
# PROCESAMIENTO Y VISUALIZACIÓN
# ============================================================
if submitted:
    if not equipo_a or not equipo_b or not liga:
        st.warning("⚠️ Por favor completa los campos de equipos y la liga.")
    else:
        fecha_str = fecha_partido.strftime("%Y-%m-%d")
        
        with st.spinner("Consultando datos en SofaScore... Esto puede tomar unos segundos."):
            resultado = analizar_partido(equipo_a, equipo_b, fecha_str, liga)
            
        if "error" in resultado:
            st.error(f"❌ {resultado['error']}")
        else:
            st.success(f"Encuentros procesados para: **{resultado['equipo_a']}** vs **{resultado['equipo_b']}**")
            
            # ----------------------------------------------------
            # SECCIÓN 1: HISTORIAL H2H
            # ----------------------------------------------------
            st.markdown("---")
            st.subheader("🤝 Historial de Enfrentamientos Directos (H2H)")
            
            h2h_partidos = resultado.get("h2h", [])
            if not h2h_partidos:
                st.info("No se encontraron enfrentamientos previos directos en esta liga antes de la fecha indicada.")
            else:
                for idx, evento in enumerate(h2h_partidos, 1):
                    fecha_evt = obtener_fecha(evento)
                    home_name = evento.get("homeTeam", {}).get("name", "")
                    away_name = evento.get("awayTeam", {}).get("name", "")
                    
                    home_score = evento.get("homeScore", {}).get("current", 0)
                    away_score = evento.get("awayScore", {}).get("current", 0)
                    
                    with st.expander(f"Partido {idx}: {home_name} {home_score} - {away_score} {away_name} ({fecha_evt.strftime('%d/%m/%Y') if fecha_evt else 'Fecha desc.'})"):
                        stats = obtener_estadisticas(evento)
                        
                        # Mostrar marcador general
                        cols = st.columns(3)
                        cols[1].metric(label=f"{home_name} vs {away_name}", value=f"{home_score} - {away_score}")
                        
                        st.markdown("#### Estadísticas del Enfrentamiento")
                        if not stats or all(v is None for v in stats.values()):
                            st.text("No hay estadísticas detalladas disponibles para este encuentro.")
                        else:
                            for nombre_stat, valores in stats.items():
                                if valores:
                                    val_local, val_visitante = valores
                                    st.markdown(f"**{nombre_stat}:** {home_name} ({val_local}) — ({val_visitante}) {away_name}")

            # ----------------------------------------------------
            # SECCIÓN 2: RENDIMIENTO RECIENTE (LOCAL / VISITANTE)
            # ----------------------------------------------------
            st.markdown("---")
            st.subheader("📊 Últimos Partidos Contextuales")
            
            col_a, col_b = st.columns(2)
            
            # --- EQUIPO A ---
            with col_a:
                st.markdown(f"### 🏠 {resultado['equipo_a']} (Como Local)")
                local_evt = resultado.get("local_a")
                
                if not local_evt:
                    st.info("No hay registros recientes como local en esta liga.")
                else:
                    f_loc = obtener_fecha(local_evt)
                    h_n = local_evt.get("homeTeam", {}).get("name")
                    a_n = local_evt.get("awayTeam", {}).get("name")
                    h_s = local_evt.get("homeScore", {}).get("current", 0)
                    a_s = local_evt.get("awayScore", {}).get("current", 0)
                    
                    st.write(f"**Fecha:** {f_loc.strftime('%d/%m/%Y') if f_loc else 'N/D'}")
                    st.write(f"**Resultado:** {h_n} {h_s} - {a_s} {a_n}")
                    
                    stats_loc = obtener_estadisticas(local_evt)
                    with st.expander("Ver estadísticas de local"):
                        for ns, vs in stats_loc.items():
                            if vs:
                                st.text(f"{ns}: Local ({vs[0]}) | Visitante ({vs[1]})")

                st.markdown(f"### ✈️ {resultado['equipo_a']} (Como Visitante)")
                vis_evt_a = resultado.get("visitante_a")
                
                if not vis_evt_a:
                    st.info("No hay registros recientes como visitante en esta liga.")
                else:
                    f_vis = obtener_fecha(vis_evt_a)
                    h_n = vis_evt_a.get("homeTeam", {}).get("name")
                    a_n = vis_evt_a.get("awayTeam", {}).get("name")
                    h_s = vis_evt_a.get("homeScore", {}).get("current", 0)
                    a_s = vis_evt_a.get("awayScore", {}).get("current", 0)
                    
                    st.write(f"**Fecha:** {f_vis.strftime('%d/%m/%Y') if f_vis else 'N/D'}")
                    st.write(f"**Resultado:** {h_n} {h_s} - {a_s} {a_n}")
                    
                    stats_vis_a = obtener_estadisticas(vis_evt_a)
                    with st.expander("Ver estadísticas de visitante"):
                        for ns, vs in stats_vis_a.items():
                            if vs:
                                st.text(f"{ns}: Local ({vs[0]}) | Visitante ({vs[1]})")

            # --- EQUIPO B ---
            with col_b:
                st.markdown(f"### 🏠 {resultado['equipo_b']} (Como Local)")
                local_evt_b = resultado.get("local_b")
                
                if not local_evt_b:
                    st.info("No hay registros recientes como local en esta liga.")
                else:
                    f_loc = obtener_fecha(local_evt_b)
                    h_n = local_evt_b.get("homeTeam", {}).get("name")
                    a_n = local_evt_b.get("awayTeam", {}).get("name")
                    h_s = local_evt_b.get("homeScore", {}).get("current", 0)
                    a_s = local_evt_b.get("awayScore", {}).get("current", 0)
                    
                    st.write(f"**Fecha:** {f_loc.strftime('%d/%m/%Y') if f_loc else 'N/D'}")
                    st.write(f"**Resultado:** {h_n} {h_s} - {a_s} {a_n}")
                    
                    stats_loc_b = obtener_estadisticas(local_evt_b)
                    with st.expander("Ver estadísticas de local"):
                        for ns, vs in stats_loc_b.items():
                            if vs:
                                st.text(f"{ns}: Local ({vs[0]}) | Visitante ({vs[1]})")

                st.markdown(f"### ✈️ {resultado['equipo_b']} (Como Visitante)")
                vis_evt_b = resultado.get("visitante_b")
                
                if not vis_evt_b:
                    st.info("No hay registros recientes como visitante en esta liga.")
                else:
                    f_vis = obtener_fecha(vis_evt_b)
                    h_n = vis_evt_b.get("homeTeam", {}).get("name")
                    a_n = vis_evt_b.get("awayTeam", {}).get("name")
                    h_s = vis_evt_b.get("homeScore", {}).get("current", 0)
                    a_s = vis_evt_b.get("awayScore", {}).get("current", 0)
                    
                    st.write(f"**Fecha:** {f_vis.strftime('%d/%m/%Y') if f_vis else 'N/D'}")
                    st.write(f"**Resultado:** {h_n} {h_s} - {a_s} {a_n}")
                    
                    stats_vis_b = obtener_estadisticas(vis_evt_b)
                    with st.expander("Ver estadísticas de visitante"):
                        for ns, vs in stats_vis_b.items():
                            if vs:
                                st.text(f"{ns}: Local ({vs[0]}) | Visitante ({vs[1]})")