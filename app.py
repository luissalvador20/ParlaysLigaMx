import streamlit as st
import requests
import numpy as np
from datetime import datetime, timedelta
import zoneinfo

st.set_page_config(page_title="Parlay Analytics PRO", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    
    .card-live { background-color: #1A1D24; padding: 12px; border-radius: 8px; border-left: 5px solid #FF5252; margin-bottom: 8px; }
    .card-today { background-color: #1A1D24; padding: 12px; border-radius: 8px; border-left: 5px solid #00E676; margin-bottom: 8px; }
    .card-tomorrow { background-color: #1A1D24; padding: 12px; border-radius: 8px; border-left: 5px solid #FFD600; margin-bottom: 8px; }
    .card-upcoming { background-color: #1A1D24; padding: 12px; border-radius: 8px; border-left: 5px solid #29B6F6; margin-bottom: 8px; }
    
    .box-hit { background-color: #12241A; color: #00E676; padding: 5px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; border: 1px solid #00E676; display: inline-block; margin: 2px; }
    .box-miss { background-color: #261517; color: #FF5252; padding: 5px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; border: 1px solid #FF5252; display: inline-block; margin: 2px; }
    
    .stSelectbox label { font-size: 14px; color: #00E676; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("⚽ PARLAY ANALYTICS PRO")

# Diccionario de 10 Ligas
LIGAS = {
    "🇲🇽 Liga MX": "mex.1",
    "🇪🇺 Champions League": "uefa.champions",
    "🇪🇺 Europa League": "uefa.europa",
    "🇬🇧 Premier League": "eng.1",
    "🇪🇸 LaLiga": "esp.1",
    "🇮🇹 Serie A": "ita.1",
    "🇩🇪 Bundesliga": "ger.1",
    "🇫🇷 Ligue 1": "fra.1",
    "🇸🇦 Liga de Arabia": "sau.1",
    "🇺🇸 MLS": "usa.1"
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

@st.cache_data(ttl=60)
def obtener_eventos_general(codigo_liga):
    try:
        tz_local = zoneinfo.ZoneInfo("America/Mexico_City")
    except Exception:
        tz_local = None

    hoy_dt = datetime.now(tz_local) if tz_local else datetime.now()
    fecha_inicio = (hoy_dt - timedelta(days=2)).strftime("%Y%m%d")
    fecha_fin = (hoy_dt + timedelta(days=7)).strftime("%Y%m%d")
    
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{codigo_liga}/scoreboard?dates={fecha_inicio}-{fecha_fin}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            events = res.json().get('events', [])
            partidos = []
            
            str_ayer = (hoy_dt - timedelta(days=1)).strftime("%Y-%m-%d")
            str_hoy = hoy_dt.strftime("%Y-%m-%d")
            str_manana = (hoy_dt + timedelta(days=1)).strftime("%Y-%m-%d")

            for ev in events:
                comp = ev['competitions'][0]
                home = comp['competitors'][0]
                away = comp['competitors'][1]
                
                date_utc_str = ev.get('date', '')
                if date_utc_str:
                    dt_utc = datetime.fromisoformat(date_utc_str.replace('Z', '+00:00'))
                    dt_local = dt_utc.astimezone(tz_local) if tz_local else dt_utc
                    fecha_p = dt_local.strftime("%Y-%m-%d")
                    hora_p = dt_local.strftime("%H:%M")
                else:
                    fecha_p = ""
                    hora_p = ""

                if fecha_p == str_hoy:
                    cat_dia = "today"
                elif fecha_p == str_manana:
                    cat_dia = "tomorrow"
                elif fecha_p == str_ayer:
                    cat_dia = "yesterday"
                else:
                    cat_dia = "upcoming"

                leaders = comp.get('leaders', [])
                jugadores = []
                for leader in leaders:
                    for l_entry in leader.get('leaders', []):
                        athlete = l_entry.get('athlete', {})
                        if athlete:
                            jugadores.append({
                                "nombre": athlete.get('displayName', 'Jugador'),
                                "foto": athlete.get('headshot', {}).get('href', 'https://a.espncdn.com/i/headshots/default-player.png'),
                                "stat": l_entry.get('displayValue', '')
                            })

                partidos.append({
                    "id": ev['id'],
                    "local": home['team']['displayName'],
                    "local_score": int(home.get('score', 0)),
                    "visita": away['team']['displayName'],
                    "visita_score": int(away.get('score', 0)),
                    "fecha": fecha_p,
                    "hora": hora_p,
                    "cat_dia": cat_dia,
                    "estado_state": ev['status']['type']['state'],
                    "estado_desc": ev['status']['type']['shortDetail'],
                    "jugadores": jugadores
                })
            return partidos
    except Exception:
        pass
    return []

# Filtro Días estilo FotMob
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
filtro_dia = st.radio("Selecciona el día:", list(dias_fotmob.keys()), index=1, horizontal=True)
fecha_seleccionada = dias_fotmob[filtro_dia]

# Conteo por Ligas con Badges
ligas_con_indicador = {}
for nombre, codigo in LIGAS.items():
    partidos_temp = obtener_eventos_general(codigo)
    num_live = sum(1 for p in partidos_temp if p['estado_state'] == 'in')
    num_today = sum(1 for p in partidos_temp if p['cat_dia'] == 'today' and p['estado_state'] != 'in')
    num_tomorrow = sum(1 for p in partidos_temp if p['cat_dia'] == 'tomorrow')
    
    detalles = []
    if num_live > 0:
        detalles.append(f"🔴 {num_live} en vivo")
    if num_today > 0:
        detalles.append(f"🟢 {num_today} hoy")
    if num_tomorrow > 0:
        detalles.append(f"🟡 {num_tomorrow} mañana")
        
    label = f"{nombre} | " + " • ".join(detalles) if detalles else f"{nombre} ⚪ (Sin partidos)"
    ligas_con_indicador[label] = codigo

liga_seleccionada = st.selectbox("🏆 Selecciona Competición:", list(ligas_con_indicador.keys()))
codigo_liga = ligas_con_indicador[liga_seleccionada]

tabla = obtener_tabla_posiciones(codigo_liga)
matches = obtener_eventos_general(codigo_liga)

if fecha_seleccionada != "all":
    matches = [p for p in matches if p['fecha'] == fecha_seleccionada]

if not matches:
    st.info("📌 No hay partidos programados para el filtro seleccionado.")
else:
    for match in matches:
        local = match['local']
        visita = match['visita']
        g_loc = match['local_score']
        g_vis = match['visita_score']
        tot_goles = g_loc + g_vis
        estado_state = match['estado_state']
        estado_desc = match['estado_desc']
        cat_dia = match['cat_dia']
        
        is_live = (estado_state == 'in')
        is_post = (estado_state == 'post')

        card_class = "card-live" if is_live else (
            "card-today" if cat_dia == "today" else (
                "card-tomorrow" if cat_dia == "tomorrow" else "card-upcoming"
            )
        )

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

        prediccion_ganador = local if p_loc > p_vis else visita

        if is_live:
            titulo_partido = f"🔴 EN VIVO ({estado_desc}) | {local} {g_loc} - {g_vis} {visita}"
        elif is_post:
            titulo_partido = f"🏁 FINAL | {local} {g_loc} - {g_vis} {visita}"
        else:
            titulo_partido = f"⏰ {match['hora']} hrs | {local} vs {visita}"

        with st.expander(titulo_partido, expanded=False):
            st.markdown(f"<div class='{card_class}'>", unsafe_allow_html=True)
            
            if is_post or is_live:
                st.markdown("#### 🎯 Auditoría: Pronóstico vs Resultado")
                auditoria_html = []

                ganador_real = local if g_loc > g_vis else (visita if g_vis > g_loc else "Empate")
                if ganador_real == "Empate":
                    auditoria_html.append("<div class='box-miss'>❌ Ganador: Empate</div>")
                elif prediccion_ganador == ganador_real:
                    auditoria_html.append(f"<div class='box-hit'>✅ Ganador: Atinado ({ganador_real})</div>")
                else:
                    auditoria_html.append(f"<div class='box-miss'>❌ Ganador: Falló (Predijo {prediccion_ganador})</div>")

                if (over25_prob >= 50.0) == (tot_goles > 2.5):
                    auditoria_html.append(f"<div class='box-hit'>✅ Over 2.5: Atinado ({tot_goles} goles)</div>")
                else:
                    auditoria_html.append(f"<div class='box-miss'>❌ Over 2.5: Falló ({tot_goles} goles)</div>")

                st.markdown(" ".join(auditoria_html), unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

            pos_text_loc = f"#{info_loc['posicion']}" if local in tabla else ""
            pos_text_vis = f"#{info_vis['posicion']}" if visita in tabla else ""

            col1, col2, col3 = st.columns(3)
            col1.metric(f"🟢 Gana {local[:10]} {pos_text_loc}", f"{p_loc:.1f}%")
            col2.metric("⚪ Empate", f"{p_emp:.1f}%")
            col3.metric(f"🔴 Gana {visita[:10]} {pos_text_vis}", f"{p_vis:.1f}%")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("⚽ Over 2.5", f"{over25_prob:.1f}%")
            m2.metric("🤝 Ambos Anotan", f"{aa_prob:.1f}%")
            m3.metric("🚩 Córners Est.", "~9.5")
            m4.metric("🟨 Tarjetas Est.", "~4.2")

            if match['jugadores']:
                st.markdown("---")
                st.markdown("🎯 **Jugadores Clave / Tiradores a destacar:**")
                cols_j = st.columns(min(4, len(match['jugadores'])))
                for idx, jug in enumerate(match['jugadores'][:4]):
                    with cols_j[idx]:
                        st.image(jug['foto'], width=60)
                        st.caption(f"**{jug['nombre']}**\n{jug['stat']}")

            st.markdown("</div>", unsafe_allow_html=True)
