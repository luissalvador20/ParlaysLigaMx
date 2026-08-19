import streamlit as st
import requests
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Parlay Analytics PRO", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    
    .card-live { background-color: #261517; padding: 16px; border-radius: 12px; border: 2px solid #FF5252; margin-bottom: 12px; }
    .card-today { background-color: #12241A; padding: 16px; border-radius: 12px; border: 2px solid #00E676; margin-bottom: 12px; }
    .card-tomorrow { background-color: #262312; padding: 16px; border-radius: 12px; border: 2px solid #FFD600; margin-bottom: 12px; }
    .card-upcoming { background-color: #121F2B; padding: 16px; border-radius: 12px; border: 2px solid #29B6F6; margin-bottom: 12px; }
    
    .badge-live { background-color: #FF5252; color: #FFF; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; }
    .badge-today { background-color: #00E676; color: #000; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; }
    .badge-tomorrow { background-color: #FFD600; color: #000; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; }
    .badge-upcoming { background-color: #29B6F6; color: #000; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; }
    
    .hit-box { background-color: #1B382B; color: #00E676; padding: 5px 8px; border-radius: 6px; font-size: 12px; font-weight: bold; border: 1px solid #00E676; display: inline-block; margin-top: 6px; }
    
    /* Estilos para la barra de fechas */
    .stSelectbox label { font-size: 14px; color: #00E676; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("⚽ PARLAY ANALYTICS PRO")

LIGAS = {
    "🇲🇽 Liga MX": "mex.1",
    "🇪🇺 Champions League": "uefa.champions",
    "🇬🇧 Premier League": "eng.1",
    "🇪🇸 LaLiga": "esp.1",
    "🇮🇹 Serie A": "ita.1",
    "🇩🇪 Bundesliga": "ger.1",
    "🇫🇷 Ligue 1": "fra.1",
    "🇸🇦 Liga de Arabia": "sau.1",
    "🇺🇸 MLS": "usa.1"
}

# 1. Obtener la Tabla General/Posiciones para pronósticos reales
@st.cache_data(ttl=300)
def obtener_tabla_posiciones(codigo_liga):
    url = f"https://site.api.espn.com/apis/v2/sports/soccer/{codigo_liga}/standings"
    tabla = {}
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            children = data.get('children', [])
            entries = []
            if children:
                entries = children[0].get('standings', {}).get('entries', [])
            else:
                entries = data.get('standings', {}).get('entries', [])
                
            for idx, entry in enumerate(entries):
                team_name = entry['team']['displayName']
                stats = {s['name']: s.get('value', 0) for s in entry.get('stats', [])}
                puntos = stats.get('points', 0)
                dif_goles = stats.get('pointDifferential', 0)
                
                tabla[team_name] = {
                    "posicion": idx + 1,
                    "puntos": puntos,
                    "dif_goles": dif_goles
                }
    except Exception:
        pass
    return tabla

# 2. Obtener partidos por fecha específica
@st.cache_data(ttl=30)
def obtener_eventos_por_fecha(codigo_liga, fecha_str):
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{codigo_liga}/scoreboard?dates={fecha_str}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            events = res.json().get('events', [])
            partidos = []
            for ev in events:
                comp = ev['competitions'][0]
                home = comp['competitors'][0]
                away = comp['competitors'][1]
                
                partidos.append({
                    "id": ev['id'],
                    "local": home['team']['displayName'],
                    "local_score": int(home.get('score', 0)),
                    "visita": away['team']['displayName'],
                    "visita_score": int(away.get('score', 0)),
                    "fecha": ev.get('date', '')[:10],
                    "hora": ev.get('date', '')[11:16],
                    "estado_state": ev['status']['type']['state'],
                    "estado_desc": ev['status']['type']['shortDetail']
                })
            return partidos
    except Exception:
        pass
    return []

# Menú de Seleccion de Liga
col_liga, col_fecha = st.columns([1, 1])

with col_liga:
    liga_nombre = st.selectbox("🏆 Selecciona Competición:", list(LIGAS.keys()))
    codigo_liga = LIGAS[liga_nombre]

# FILTRO DE FECHAS ESTILO FOTMOB / PLAYDOIT
hoy_dt = datetime.now()
manana_dt = hoy_dt + timedelta(days=1)

opciones_fechas = {
    "🟢 HOY": hoy_dt.strftime("%Y%m%d"),
    "🟡 MAÑANA": manana_dt.strftime("%Y%m%d"),
    "🔵 PRÓXIMOS 7 DÍAS": f"{hoy_dt.strftime('%Y%m%d')}-{(hoy_dt + timedelta(days=7)).strftime('%Y%m%d')}"
}

with col_fecha:
    filtro_fecha = st.radio("📅 Filtrar Fechas (Estilo Playdoit):", list(opciones_fechas.keys()), horizontal=True)
    fecha_codigo = opciones_fechas[filtro_fecha]

mostrar_pronosticos = st.checkbox("📊 Mostrar pronósticos basados en la Tabla General", value=True)

# Obtener tabla y partidos
tabla = obtener_tabla_posiciones(codigo_liga)
matches = obtener_eventos_por_fecha(codigo_liga, fecha_codigo)

str_hoy = hoy_dt.strftime("%Y-%m-%d")
str_manana = manana_dt.strftime("%Y-%m-%d")

if not matches:
    st.info("📌 No hay partidos programados para esta fecha en la liga seleccionada.")
else:
    for match in matches:
        local = match['local']
        visita = match['visita']
        g_loc = match['local_score']
        g_vis = match['visita_score']
        tot_goles = g_loc + g_vis
        fecha_p = match['fecha']
        estado_state = match['estado_state']
        estado_desc = match['estado_desc']
        
        is_live = (estado_state == 'in')
        is_post = (estado_state == 'post')

        # Clasificación por fecha
        if is_live:
            st.markdown(f"""
                <div class="card-live">
                    <span class="badge-live">🔴 EN VIVO — {estado_desc}</span>
                    <h2 style="margin:8px 0 0 0; color:#FFF;">⚽ {local} {g_loc} - {g_vis} {visita}</h2>
                </div>
            """, unsafe_allow_html=True)
        elif fecha_p == str_hoy:
            st.markdown(f"""
                <div class="card-today">
                    <span class="badge-today">🟢 SE JUEGA HOY | ⏰ {match['hora']} hrs</span>
                    <h3 style="margin:6px 0 0 0; color:#FFF;">🏟️ {local} vs {visita}</h3>
                </div>
            """, unsafe_allow_html=True)
        elif fecha_p == str_manana:
            st.markdown(f"""
                <div class="card-tomorrow">
                    <span class="badge-tomorrow">🟡 SE JUEGA MAÑANA | ⏰ {match['hora']} hrs</span>
                    <h3 style="margin:6px 0 0 0; color:#FFF;">🏟️ {local} vs {visita}</h3>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="card-upcoming">
                    <span class="badge-upcoming">🔵 FECHA: {fecha_p} | ⏰ {match['hora']} hrs</span>
                    <h3 style="margin:6px 0 0 0; color:#FFF;">🏟️ {local} vs {visita}</h3>
                </div>
            """, unsafe_allow_html=True)

        if is_live or is_post:
            hits = []
            if tot_goles > 2.5:
                hits.append("✅ Over 2.5 Goles")
            if g_loc >= 1 and g_vis >= 1:
                hits.append("✅ Ambos Anotan (AA)")
            if g_loc > g_vis:
                hits.append(f"✅ Gana {local}")
            elif g_vis > g_loc:
                hits.append(f"✅ Gana {visita}")
                
            if hits:
                hit_html = " ".join([f"<div class='hit-box'>{h}</div>" for h in hits])
                st.markdown(f"<div>{hit_html}</div><br>", unsafe_allow_html=True)

        # CÁLCULO DE PROBABILIDAD REAL SEGÚN POSICIÓN EN LA TABLA GENERAL
        if mostrar_pronosticos:
            info_loc = tabla.get(local, {"posicion": 10, "puntos": 15, "dif_goles": 0})
            info_vis = tabla.get(visita, {"posicion": 10, "puntos": 15, "dif_goles": 0})
            
            puntos_loc = info_loc['puntos'] + 3 # Ventaja de localía (+3 pts virtuales)
            puntos_vis = info_vis['puntos']
            
            total_pts = max(1, puntos_loc + puntos_vis)
            
            # Cálculo porcentual
            p_loc = min(78.0, max(20.0, (puntos_loc / total_pts) * 100))
            p_vis = min(70.0, max(15.0, (puntos_vis / total_pts) * 100))
            p_emp = max(15.0, 100.0 - (p_loc + p_vis))
            
            # Normalizar
            s = p_loc + p_vis + p_emp
            p_loc, p_vis, p_emp = (p_loc/s)*100, (p_vis/s)*100, (p_emp/s)*100

            # Estimación Over / Ambos Anotan basado en diferencia de goles
            dg_total = abs(info_loc['dif_goles']) + abs(info_vis['dif_goles'])
            over25_prob = min(82.0, max(42.0, 50.0 + (dg_total * 0.8)))
            aa_prob = min(75.0, max(40.0, 48.0 + (dg_total * 0.5)))
            
            pos_text_loc = f"#{info_loc['posicion']}" if local in tabla else ""
            pos_text_vis = f"#{info_vis['posicion']}" if visita in tabla else ""

            col1, col2, col3 = st.columns(3)
            col1.metric(f"🟢 Gana {local[:10]} {pos_text_loc}", f"{p_loc:.1f}%")
            col2.metric("⚪ Empate", f"{p_emp:.1f}%")
            col3.metric(f"🔴 Gana {visita[:10]} {pos_text_vis}", f"{p_vis:.1f}%")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("⚽ Over 2.5", f"{over25_prob:.1f}%")
            m2.metric("🤝 Ambos Anotan", f"{aa_prob:.1f}%")
            m3.metric("🚩 Córners", "~9.5")
            m4.metric("🟨 Tarjetas", "~4.2")

        st.markdown("<hr style='border:0; border-top: 1px solid #2B2B2B; margin: 16px 0;'>", unsafe_allow_html=True)
