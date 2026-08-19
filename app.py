import streamlit as st
import numpy as np

# Configuración de página con diseño oscuro
st.set_page_config(page_title="Parlay Analytics PRO", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #121212; }
    .card { background-color: #1E1E1E; padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #2A2A2A; }
    .player-card { display: flex; align-items: center; gap: 15px; background: #262626; padding: 12px; border-radius: 8px; margin-top: 10px; }
    .player-img { width: 65px; height: 65px; border-radius: 50%; object-fit: cover; border: 2px solid #00E676; }
    </style>
""", unsafe_allow_html=True)

st.title("⚽ PARLAY ANALYTICS PRO")
st.subheader("Análisis Visual de Partidos & Tendencias de Apuestas")

# MATRIZ COMPLETA - LIGA MX (18 EQUIPOS)
FUERZA_EQUIPOS = {
    "América": {"atq": 1.65, "def": 0.85, "star": "Henry Martín", "foto": "https://a.espncdn.com/combiner/i?img=/i/headshots/soccer/players/full/210344.png"},
    "Tigres UANL": {"atq": 1.55, "def": 0.90, "star": "André-Pierre Gignac", "foto": "https://a.espncdn.com/combiner/i?img=/i/headshots/soccer/players/full/88302.png"},
    "Monterrey": {"atq": 1.50, "def": 0.90, "star": "Germán Berterame", "foto": "https://a.espncdn.com/combiner/i?img=/i/headshots/soccer/players/full/248559.png"},
    "Toluca": {"atq": 1.60, "def": 1.10, "star": "Paulinho", "foto": "https://a.espncdn.com/combiner/i?img=/i/headshots/soccer/players/full/188440.png"},
    "Cruz Azul": {"atq": 1.45, "def": 0.80, "star": "Giorgos Giakoumakis", "foto": "https://a.espncdn.com/combiner/i?img=/i/headshots/soccer/players/full/210609.png"},
    "Pachuca": {"atq": 1.35, "def": 1.05, "star": "Salomón Rondón", "foto": "https://a.espncdn.com/combiner/i?img=/i/headshots/soccer/players/full/116239.png"},
    "Guadalajara": {"atq": 1.25, "def": 1.00, "star": "Javier Hernández", "foto": "https://a.espncdn.com/combiner/i?img=/i/headshots/soccer/players/full/148818.png"},
    "Pumas UNAM": {"atq": 1.20, "def": 1.10, "star": "Guillermo Martínez", "foto": "https://a.espncdn.com/combiner/i?img=/i/headshots/soccer/players/full/215357.png"},
    "León": {"atq": 1.15, "def": 1.15, "star": "Jhonder Cádiz", "foto": "https://a.espncdn.com/combiner/i?img=/i/headshots/soccer/players/full/208537.png"},
    "Santos Laguna": {"atq": 1.05, "def": 1.25, "star": "Anthony Lozano", "foto": "https://a.espncdn.com/combiner/i?img=/i/headshots/soccer/players/full/163013.png"},
    "Atlas": {"atq": 0.95, "def": 1.15, "star": "Uroš Đurđević", "foto": "https://a.espncdn.com/combiner/i?img=/i/headshots/soccer/players/full/183204.png"},
    "Atletico San Luis": {"atq": 1.10, "def": 1.30, "star": "Fran Boli", "foto": "https://a.espncdn.com/combiner/i?img=/i/headshots/soccer/players/full/208226.png"},
    "Necaxa": {"atq": 1.00, "def": 1.20, "star": "Diber Cambindo", "foto": "https://a.espncdn.com/combiner/i?img=/i/headshots/soccer/players/full/257371.png"},
    "Tijuana": {"atq": 1.10, "def": 1.35, "star": "Carlos González", "foto": "https://a.espncdn.com/combiner/i?img=/i/headshots/soccer/players/full/200676.png"},
    "Mazatlan FC": {"atq": 0.90, "def": 1.30, "star": "Brian Rubio", "foto": "https://a.espncdn.com/combiner/i?img=/i/headshots/soccer/players/full/252980.png"},
    "FC Juarez": {"atq": 0.85, "def": 1.35, "star": "Óscar Estupiñán", "foto": "https://a.espncdn.com/combiner/i?img=/i/headshots/soccer/players/full/215707.png"},
    "Querétaro": {"atq": 0.80, "def": 1.40, "star": "Rubén Rubio", "foto": "https://a.espncdn.com/combiner/i?img=/i/headshots/png/2200/default.png"},
    "Puebla": {"atq": 0.80, "def": 1.45, "star": "Lucas Cavallini", "foto": "https://a.espncdn.com/combiner/i?img=/i/headshots/soccer/players/full/175855.png"}
}

col1, col2 = st.columns(2)

equipos_ordenados = sorted(list(FUERZA_EQUIPOS.keys()))

with col1:
    local = st.selectbox("🏠 Equipo Local", equipos_ordenados, index=0)
with col2:
    visita = st.selectbox("✈️ Equipo Visitante", equipos_ordenados, index=1)

if st.button("🔥 GENERAR ANÁLISIS COMPLETO", use_container_width=True):
    if local == visita:
        st.error("Por favor selecciona dos equipos diferentes.")
    else:
        st_local = FUERZA_EQUIPOS[local]
        st_visita = FUERZA_EQUIPOS[visita]
        
        # Simulación de Poisson
        exp_local = (st_local["atq"] * 1.15) / st_visita["def"]
        exp_visita = st_visita["atq"] / st_local["def"]
        
        prob_local = np.random.poisson(exp_local, 10000)
        prob_visita = np.random.poisson(exp_visita, 10000)
        
        gl = np.mean(prob_local > prob_visita) * 100
        emp = np.mean(prob_local == prob_visita) * 100
        gv = np.mean(prob_local < prob_visita) * 100
        o25 = np.mean((prob_local + prob_visita) > 2.5) * 100
        
        # Estimaciones adicionales
        corners_totales = (exp_local + exp_visita) * 3.8
        tarjetas_totales = 3.5 + (0.5 if (gl > 35 and gv > 35) else 0)
        
        st.markdown("---")
        st.markdown(f"### 🏟️ {local} vs {visita}")
        
        # Métricas de Probabilidades
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(f"🟢 Gana {local}", f"{gl:.1f}%")
        m2.metric("⚪ Empate", f"{emp:.1f}%")
        m3.metric(f"🔴 Gana {visita}", f"{gv:.1f}%")
        m4.metric("⚽ Over 2.5 Goles", f"{o25:.1f}%")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Tarjetas de Jugadores con Foto
        c_play1, c_play2 = st.columns(2)
        
        tiros_loc = (max(2.5, exp_local * 3.1)) * 0.42
        tiros_vis = (max(2.0, exp_visita * 2.9)) * 0.40
        
        with c_play1:
            st.markdown(f"""
                <div class="player-card">
                    <img src="{st_local['foto']}" class="player-img">
                    <div>
                        <h4 style="margin:0; color:#FFFFFF;">{st_local['star']}</h4>
                        <span style="color:#00E676; font-size:13px; font-weight:bold;">{local}</span>
                        <p style="margin:5px 0 0 0; color:#B0B0B0;">🎯 Tiros a puerta esperados: <b>{tiros_loc:.1f}</b></p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        with c_play2:
            st.markdown(f"""
                <div class="player-card">
                    <img src="{st_visita['foto']}" class="player-img">
                    <div>
                        <h4 style="margin:0; color:#FFFFFF;">{st_visita['star']}</h4>
                        <span style="color:#FF5252; font-size:13px; font-weight:bold;">{visita}</span>
                        <p style="margin:5px 0 0 0; color:#B0B0B0;">🎯 Tiros a puerta esperados: <b>{tiros_vis:.1f}</b></p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Métricas Secundarias con Dibujos
        s1, s2, s3 = st.columns(3)
        s1.metric("🚩 Córners Totales Esperados", f"~{corners_totales:.1f}", delta="+8.5 Córners sugerido")
        s2.metric("🟨 Tarjetas Estimadas", f"~{tarjetas_totales:.1f}", delta="Línea +3.5 o +4.5")
        s3.metric("🚨 Doble Oportunidad (1X)", f"{gl+emp:.1f}%", delta="Valor Local / Sorpresa")
