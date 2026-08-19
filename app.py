import streamlit as st
import requests
import numpy as np

st.set_page_config(page_title="Parlay Analytics PRO", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #121212; }
    .card { background-color: #1E1E1E; padding: 18px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #2A2A2A; }
    </style>
""", unsafe_allow_html=True)

st.title("⚽ PARLAY ANALYTICS PRO")
st.subheader("🌐 Cartelera Internacional Automática & Tendencias")

# Configuración de ligas compatibles con la API de ESPN
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

liga_seleccionada = st.selectbox("🏆 Selecciona una competición para ver la cartelera:", list(LIGAS.keys()))

@st.cache_data(ttl=1800)
def obtener_partidos(codigo_liga):
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{codigo_liga}/scoreboard"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            events = response.json().get('events', [])
            partidos = []
            for ev in events:
                comp = ev['competitions'][0]
                partidos.append({
                    "local": comp['competitors'][0]['team']['displayName'],
                    "visita": comp['competitors'][1]['team']['displayName'],
                    "fecha": ev.get('date', '')[:10],
                    "estado": ev['status']['type']['shortDetail']
                })
            return partidos
    except Exception:
        pass
    return []

codigo = LIGAS[liga_seleccionada]
matches = obtener_partidos(codigo)

if not matches:
    st.info(f"📌 No hay partidos programados actualmente para {liga_seleccionada}. Revisa más tarde o selecciona otra liga.")
else:
    for match in matches:
        local = match['local']
        visita = match['visita']
        fecha = match['fecha']
        estado = match['estado']

        st.markdown(f"""
            <div class="card">
                <span style="color:#00E676; font-size:12px; font-weight:bold;">🏆 {liga_seleccionada} | 📅 {fecha} ({estado})</span>
                <h3 style="margin:5px 0 10px 0; color:#FFFFFF;">🏟️ {local} vs {visita}</h3>
            </div>
        """, unsafe_allow_html=True)

        # Simulación automatizada de probabilidades y métricas
        exp_loc = np.random.uniform(1.2, 1.8)
        exp_vis = np.random.uniform(0.9, 1.5)

        total_exp = exp_loc + exp_vis
        gl = (exp_loc / total_exp) * 68
        gv = (exp_vis / total_exp) * 65
        emp = max(15.0, 100 - (gl + gv))
        corners = (exp_loc + exp_vis) * 3.6
        tarjetas = 3.8 + np.random.uniform(0, 1.5)

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric(f"🟢 Gana {local[:10]}", f"{gl:.1f}%")
        col2.metric("⚪ Empate", f"{emp:.1f}%")
        col3.metric(f"🔴 Gana {visita[:10]}", f"{gv:.1f}%")
        col4.metric("🚩 Córners Est.", f"~{corners:.1f}")
        col5.metric("🟨 Tarjetas Est.", f"~{tarjetas:.1f}")

        st.markdown("<hr style='border-color: #222;'>", unsafe_allow_html=True)
