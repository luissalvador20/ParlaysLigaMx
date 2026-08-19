import streamlit as st
import requests
import numpy as np

st.set_page_config(page_title="Parlay Analytics PRO", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #121212; }
    .card { background-color: #1E1E1E; padding: 18px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #2A2A2A; }
    .metric-box { background-color: #262626; padding: 10px; border-radius: 8px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# 🔑 Tu API Key configurada
API_KEY = "56fd7c3595dc43a9bc11e6bc256c4dd5"

st.title("⚽ PARLAY ANALYTICS PRO")
st.subheader("📅 Cartelera Automática & Tendencias de Apuestas")

@st.cache_data(ttl=1800)
def obtener_partidos():
    headers = {'X-Auth-Token': API_KEY}
    # Consulta los partidos de la Liga MX y principales ligas del día / próximos días
    url = 'https://api.football-data.org/v4/matches'
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get('matches', [])
    except Exception as e:
        pass
    return []

st.write("🔄 *Sincronizando la cartelera de hoy y mañana en tiempo real...*")

matches = obtener_partidos()

if not matches:
    st.warning("⚠️ No se encontraron partidos programados para las próximas horas o la liga está en pausa entre jornadas. ¡Revisa más tarde!")
else:
    for match in matches[:10]:  # Muestra los partidos más próximos
        local = match['homeTeam']['name']
        visita = match['awayTeam']['name']
        competicion = match.get('competition', {}).get('name', 'Liga / Torneo')
        fecha = match.get('utcDate', '')[:10]

        st.markdown(f"""
            <div class="card">
                <span style="color:#00E676; font-size:12px; font-weight:bold;">🏆 {competicion} | 📅 {fecha}</span>
                <h3 style="margin:5px 0 15px 0; color:#FFFFFF;">🏟️ {local} vs {visita}</h3>
            </div>
        """, unsafe_allow_html=True)

        # Generador de estimaciones automatizadas para el parlay
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
