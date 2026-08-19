import streamlit as st
import requests
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Parlay Analytics PRO", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    
    .badge-live { background-color: #FF5252; color: #FFF; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
    .badge-today { background-color: #00E676; color: #000; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
    
    /* Cajas de acierto y error */
    .box-hit { background-color: #12241A; color: #00E676; padding: 6px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; border: 1px solid #00E676; display: inline-block; margin: 3px 2px; }
    .box-miss { background-color: #261517; color: #FF5252; padding: 6px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; border: 1px solid #FF5252; display: inline-block; margin: 3px 2px; }
    
    .stSelectbox label { font-size: 14px; color: #00E676; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("⚽ PARLAY ANALYTICS PRO")

LIGAS = {
    "🇺🇸 MLS": "usa.1",
    "🇲🇽 Liga MX": "mex.1",
    "🇪🇺 Champions League": "uefa.champions",
    "🇬🇧 Premier League": "eng.1",
    "🇪🇸 LaLiga": "esp.1",
    "🇮🇹 Serie A": "ita.1"
}

@st.cache_data(ttl=300)
def obtener_tabla_posiciones(codigo_liga):
    url = f"https://site.api.espn.com/apis/v2/sports/soccer/{codigo_liga}/standings"
    tabla = {}
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            children = data.get('children', [])
            entries = children[0].get('standings', {}).get('entries', []) if children else data.get('standings', {}).get('entries', [])
                
            for idx, entry in enumerate(entries):
                team_name = entry['team']['displayName']
                stats = {s['name']: s.get('value', 0) for s in entry.get('stats', [])}
                tabla[team_name] = {
                    "posicion": idx + 1,
                    "puntos": stats.get('points', 0),
                    "dif_goles": stats.get('pointDifferential', 0)
                }
    except Exception:
        pass
    return tabla

@st.cache_data(ttl=30)
def obtener_eventos_general(codigo_liga):
    hoy_dt = datetime.now()
    fecha_inicio = (hoy_dt - timedelta(days=2)).strftime("%Y%m%d")
    fecha_fin = (hoy_dt + timedelta(days=7)).strftime("%Y%m%d")
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{codigo_liga}/scoreboard?dates={fecha_inicio}-{fecha_fin}"
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
                fecha_p = ev.get('date', '')[:10]
                
                if fecha_p == str_hoy:
                    cat_dia = "today"
                elif fecha_p == str_manana:
                    cat_dia = "tomorrow"
                else:
                    cat_dia = "upcoming"

                partidos.append({
                    "id": ev['id'],
                    "local": home['team']['displayName'],
                    "local_score": int(home.get('score', 0)),
                    "visita": away['team']['displayName'],
                    "visita_score": int(away.get('score', 0)),
                    "fecha": fecha_p,
                    "hora": ev.get('date', '')[11:16],
                    "cat_dia": cat_dia,
                    "estado_state": ev['status']['type']['state'],
                    "estado_desc": ev['status']['type']['shortDetail']
                })
            return partidos
    except Exception:
        pass
    return []

# Filtro de Días Estilo FotMob
hoy_dt = datetime.now()
ayer_dt = hoy_dt - timedelta(days=1)
manana_dt = hoy_dt + timedelta(days=1)

dias_fotmob = {
    f"Ayer ({ayer_dt.strftime('%d/%m')})": ayer_dt.strftime("%Y-%m-%d"),
    "🟢 Hoy": hoy_dt.strftime("%Y-%m-%d"),
    "🟡 Mañana": manana_dt.strftime("%Y-%m-%d"),
    "🔵 Todos": "all"
}

st.subheader("📅 Fecha")
filtro_dia = st.radio("Selecciona el día:", list(dias_fotmob.keys()), index=0, horizontal=True)
fecha_seleccionada = dias_fotmob[filtro_dia]

# Selección de Liga
liga_nom = st.selectbox("🏆 Selecciona Competición:", list(LIGAS.keys()))
codigo_liga = LIGAS[liga_nom]

tabla = obtener_tabla_posiciones(codigo_liga)
matches = obtener_eventos_general(codigo_liga)

if fecha_seleccionada != "all":
    matches = [p for p in matches if p['fecha'] == fecha_seleccionada]

if not matches:
    st.info("📌 No hay partidos programados para este día.")
else:
    for match in matches:
        local = match['local']
        visita = match['visita']
        g_loc = match['local_score']
        g_vis = match['visita_score']
        tot_goles = g_loc + g_vis
        estado_state = match['estado_state']
        estado_desc = match['estado_desc']
        
        is_live = (estado_state == 'in')
        is_post = (estado_state == 'post')

        # --- CÁLCULO DE PROBABILIDADES DEL ALGORITMO ---
        info_loc = tabla.get(local, {"posicion": 10, "puntos": 15, "dif_goles": 0})
        info_vis = tabla.get(visita, {"posicion": 10, "puntos": 15, "dif_goles": 0})
        
        puntos_loc = info_loc['puntos'] + 3
        puntos_vis = info_vis['puntos']
        total_pts = max(1, puntos_loc + puntos_vis)
        
        p_loc = min(78.0, max(20.0, (puntos_loc / total_pts) * 100))
        p_vis = min(70.0, max(15.0, (puntos_vis / total_pts) * 100))
        p_emp = max(15.0, 100.0 - (p_loc + p_vis))
        
        s = p_loc + p_vis + p_emp
        p_loc, p_vis, p_emp = (p_loc/s)*100, (p_vis/s)*100, (p_emp/s)*100

        dg_total = abs(info_loc['dif_goles']) + abs(info_vis['dif_goles'])
        over25_prob = min(82.0, max(42.0, 50.0 + (dg_total * 0.8)))
        aa_prob = min(75.0, max(40.0, 48.0 + (dg_total * 0.5)))

        # ¿A quién daba como favorito la App?
        prediccion_ganador = local if p_loc > p_vis else visita
        prediccion_over = over25_prob >= 50.0
        prediccion_aa = aa_prob >= 50.0

        # --- TITULO SEGÚN ESTADO ---
        if is_live:
            titulo_partido = f"🔴 EN VIVO ({estado_desc}) | {local} {g_loc} - {g_vis} {visita}"
        elif is_post:
            titulo_partido = f"🏁 FINAL | {local} {g_loc} - {g_vis} {visita}"
        else:
            titulo_partido = f"⏰ {match['hora']} hrs | {local} vs {visita}"

        with st.expander(titulo_partido, expanded=False):
            # EVALUACIÓN DE FALLOS / ACIERTOS SI EL PARTIDO YA TERMINÓ O ESTÁ EN VIVO
            if is_post or is_live:
                st.markdown("#### 🎯 Auditoría del Pronóstico vs Realidad")
                auditoria_html = []

                # 1. Ganador
                ganador_real = local if g_loc > g_vis else (visita if g_vis > g_loc else "Empate")
                if ganador_real == "Empate":
                    auditoria_html.append("<div class='box-miss'>❌ Ganador: Hubo Empate</div>")
                elif prediccion_ganador == ganador_real:
                    auditoria_html.append(f"<div class='box-hit'>✅ Ganador: Atinado ({ganador_real})</div>")
                else:
                    auditoria_html.append(f"<div class='box-miss'>❌ Ganador: Falló (Predijo {prediccion_ganador}, ganó {ganador_real})</div>")

                # 2. Over 2.5
                real_over = (tot_goles > 2.5)
                if prediccion_over == real_over:
                    auditoria_html.append(f"<div class='box-hit'>✅ Over 2.5: Atinado ({tot_goles} goles)</div>")
                else:
                    auditoria_html.append(f"<div class='box-miss'>❌ Over 2.5: Falló ({tot_goles} goles)</div>")

                # 3. Ambos Anotan
                real_aa = (g_loc >= 1 and g_vis >= 1)
                if prediccion_aa == real_aa:
                    auditoria_html.append(f"<div class='box-hit'>✅ Ambos Anotan: Atinado</div>")
                else:
                    auditoria_html.append(f"<div class='box-miss'>❌ Ambos Anotan: Falló</div>")

                st.markdown(" ".join(auditoria_html), unsafe_allow_html=True)
                st.markdown("---")

            # --- MOSTRAR LOS PORCENTAJES Y PROMPTS DE LA APP ---
            pos_text_loc = f"#{info_loc['posicion']}" if local in tabla else ""
            pos_text_vis = f"#{info_vis['posicion']}" if visita in tabla else ""

            st.markdown("### 📊 Pronóstico Inicial del Algoritmo")
            col1, col2, col3 = st.columns(3)
            col1.metric(f"🟢 Gana {local[:10]} {pos_text_loc}", f"{p_loc:.1f}%")
            col2.metric("⚪ Empate", f"{p_emp:.1f}%")
            col3.metric(f"🔴 Gana {visita[:10]} {pos_text_vis}", f"{p_vis:.1f}%")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("⚽ Over 2.5", f"{over25_prob:.1f}%")
            m2.metric("🤝 Ambos Anotan", f"{aa_prob:.1f}%")
            m3.metric("🚩 Córners Est.", "~9.5")
            m4.metric("🟨 Tarjetas Est.", "~4.2")
