import streamlit as st
import requests
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Parlay Analytics PRO", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .card-live { background-color: #1F1B24; padding: 14px; border-radius: 12px; border-left: 5px solid #FF5252; margin-bottom: 12px; }
    .card-today { background-color: #161B22; padding: 14px; border-radius: 12px; border-left: 5px solid #00E676; margin-bottom: 12px; }
    .card-tomorrow { background-color: #161B22; padding: 14px; border-radius: 12px; border-left: 5px solid #FFD600; margin-bottom: 12px; }
    .card-upcoming { background-color: #161B22; padding: 14px; border-radius: 12px; border-left: 5px solid #29B6F6; margin-bottom: 12px; }
    
    .badge-live { background-color: #FF5252; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
    .badge-today { background-color: #00E676; color: #000; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
    .badge-tomorrow { background-color: #FFD600; color: #000; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
    .badge-upcoming { background-color: #29B6F6; color: #000; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
    
    .hit-box { background-color: #1B382B; color: #00E676; padding: 5px 8px; border-radius: 6px; font-size: 12px; font-weight: bold; border: 1px solid #00E676; display: inline-block; margin-top: 4px; }
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

@st.cache_data(ttl=30)
def obtener_eventos(codigo_liga):
    hoy_dt = datetime.now()
    fecha_inicio = hoy_dt.strftime("%Y%m%d")
    fecha_fin = (hoy_dt + timedelta(days=10)).strftime("%Y%m%d")
    
    fechas_str = f"{fecha_inicio}-{fecha_fin}"
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{codigo_liga}/scoreboard?dates={fechas_str}"
    
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            events = res.json().get('events', [])
            partidos = []
            str_hoy = hoy_dt.strftime("%Y-%m-%d")
            str_manana = (hoy_dt + timedelta(days=1)).strftime("%Y-%m-%d")

            for ev in events:
                comp = ev['competitions'][0]
                home = comp['competitors'][0]
                away = comp['competitors'][1]
                
                fecha_partido = ev.get('date', '')[:10]
                
                if fecha_partido == str_hoy:
                    dia_tag = "🟢 HOY"
                    categoria_dia = "today"
                elif fecha_partido == str_manana:
                    dia_tag = "🟡 MAÑANA"
                    categoria_dia = "tomorrow"
                else:
                    dia_tag = f"📅 PRÓXIMO ({fecha_partido})"
                    categoria_dia = "upcoming"
                
                partidos.append({
                    "id": ev['id'],
                    "local": home['team']['displayName'],
                    "local_score": int(home.get('score', 0)),
                    "visita": away['team']['displayName'],
                    "visita_score": int(away.get('score', 0)),
                    "fecha": fecha_partido,
                    "hora": ev.get('date', '')[11:16],
                    "dia_tag": dia_tag,
                    "categoria_dia": categoria_dia,
                    "estado_state": ev['status']['type']['state'],
                    "estado_desc": ev['status']['type']['shortDetail']
                })
            return partidos
    except Exception:
        pass
    return []

# Menú desplegable con total de partidos próximos
ligas_con_indicador = {}
for nombre, codigo in LIGAS.items():
    partidos_temp = obtener_eventos(codigo)
    num_juegos = len(partidos_temp)
    if num_juegos > 0:
        label = f"{nombre} 🟢 ({num_juegos} partidos próximos)"
    else:
        label = f"{nombre} ⚪ (Sin partidos próximos)"
    ligas_con_indicador[label] = codigo

liga_seleccionada = st.selectbox("🏆 Selecciona una liga:", list(ligas_con_indicador.keys()))
codigo_seleccionado = ligas_con_indicador[liga_seleccionada]

# Casilla opcional para activar las estadísticas cuando quieras analizar
mostrar_pronosticos = st.checkbox("📊 Mostrar pronósticos y estadísticas de parlay", value=False)

matches = obtener_eventos(codigo_seleccionado)

if not matches:
    st.info("📌 No hay partidos programados próximamente para esta liga.")
else:
    for match in matches:
        local = match['local']
        visita = match['visita']
        g_loc = match['local_score']
        g_vis = match['visita_score']
        tot_goles = g_loc + g_vis
        estado_state = match['estado_state']
        estado_desc = match['estado_desc']
        cat_dia = match['categoria_dia']
        
        is_live = (estado_state == 'in')
        is_post = (estado_state == 'post')

        # Tarjetas de Cartelera Limpia
        if is_live:
            st.markdown(f"""
                <div class="card-live">
                    <span class="badge-live">🔴 EN VIVO — {estado_desc}</span>
                    <h2 style="margin:6px 0 0 0; color:#FFF;">⚽ {local} {g_loc} - {g_vis} {visita}</h2>
                </div>
            """, unsafe_allow_html=True)
        elif cat_dia == "today":
            st.markdown(f"""
                <div class="card-today">
                    <span class="badge-today">🟢 HOY | ⏰ {match['hora']} hrs</span>
                    <h3 style="margin:4px 0 0 0; color:#FFF;">🏟️ {local} vs {visita}</h3>
                </div>
            """, unsafe_allow_html=True)
        elif cat_dia == "tomorrow":
            st.markdown(f"""
                <div class="card-tomorrow">
                    <span class="badge-tomorrow">🟡 MAÑANA | ⏰ {match['hora']} hrs</span>
                    <h3 style="margin:4px 0 0 0; color:#FFF;">🏟️ {local} vs {visita}</h3>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="card-upcoming">
                    <span class="badge-upcoming">{match['dia_tag']} | ⏰ {match['hora']} hrs</span>
                    <h3 style="margin:4px 0 0 0; color:#FFF;">🏟️ {local} vs {visita}</h3>
                </div>
            """, unsafe_allow_html=True)

        # Palomitas de seguimiento en tiempo real
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

        # Si activas la casilla arriba, despliega los porcentajes
        if mostrar_pronosticos:
            p_loc = np.random.uniform(36.0, 50.0)
            p_vis = np.random.uniform(26.0, 40.0)
            p_emp = max(18.0, 100.0 - (p_loc + p_vis))

            over25_prob = np.random.uniform(45.0, 62.0)
            aa_prob = np.random.uniform(48.0, 65.0)
            corners_est = np.random.uniform(8.5, 10.5)
            tarjetas_est = np.random.uniform(3.8, 5.2)

            col1, col2, col3 = st.columns(3)
            col1.metric(f"🟢 Gana {local[:10]}", f"{p_loc:.1f}%")
            col2.metric("⚪ Empate", f"{p_emp:.1f}%")
            col3.metric(f"🔴 Gana {visita[:10]}", f"{p_vis:.1f}%")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("⚽ Over 2.5", f"{over25_prob:.1f}%")
            m2.metric("🤝 Ambos Anotan", f"{aa_prob:.1f}%")
            m3.metric("🚩 Córners", f"~{corners_est:.1f}")
            m4.metric("🟨 Tarjetas", f"~{tarjetas_est:.1f}")

        st.markdown("<hr style='border:0; border-top: 1px solid #2B2B2B; margin: 16px 0;'>", unsafe_allow_html=True)
