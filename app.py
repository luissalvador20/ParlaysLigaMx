import streamlit as st
import requests
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

# Diccionario de Ligas
LIGAS = {
    "🇪🇺 Champions League (Todas las Fases)": "uefa.champions",
    "🇲🇽 Liga MX": "mex.1",
    "🇪🇺 Europa League": "uefa.europa",
    "🇬🇧 Premier League": "eng.1",
    "🇪🇸 LaLiga": "esp.1",
    "🇮🇹 Serie A": "ita.1",
    "🇩🇪 Bundesliga": "ger.1",
    "🇫🇷 Ligue 1": "fra.1",
    "🇸🇦 Liga de Arabia": "sau.1",
    "🇺🇸 MLS": "usa.1"
}

try:
    tz_local = zoneinfo.ZoneInfo("America/Mexico_City")
except Exception:
    tz_local = None

hoy_dt = datetime.now(tz_local) if tz_local else datetime.now()
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

@st.cache_data(ttl=60)
def obtener_eventos_general(codigo_liga):
    fecha_req = hoy_dt.strftime("%Y%m%d")
    
    # Endpoint general multipartido para capturar fases previas/clasificatorias
    urls = [
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/{codigo_liga}/scoreboard",
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={fecha_req}"
    ]
    
    events_encontrados = []
    
    for url in urls:
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                for ev in data.get('events', []):
                    # Filtrar por Champions si seleccionó Champions
                    league_slug = ev.get('leagues', [{}])[0].get('slug', '')
                    league_name = ev.get('leagues', [{}])[0].get('name', '').lower()
                    
                    if codigo_liga == "uefa.champions":
                        if "champions" in league_slug or "champions" in league_name:
                            events_encontrados.append(ev)
                    else:
                        events_encontrados.append(ev)
                if events_encontrados:
                    break
        except Exception:
            pass

    partidos = []
    str_ayer = ayer_dt.strftime("%Y-%m-%d")
    str_hoy = hoy_dt.strftime("%Y-%m-%d")
    str_manana = manana_dt.strftime("%Y-%m-%d")

    for ev in events_encontrados:
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
            "estado_desc": ev['status']['type']['shortDetail']
        })
    return partidos

liga_seleccionada = st.selectbox("🏆 Selecciona Competición:", list(LIGAS.keys()))
codigo_liga = LIGAS[liga_seleccionada]

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

        if is_live:
            titulo_partido = f"🔴 EN VIVO ({estado_desc}) | {local} {g_loc} - {g_vis} {visita}"
        elif is_post:
            titulo_partido = f"🏁 FINAL | {local} {g_loc} - {g_vis} {visita}"
        else:
            titulo_partido = f"⏰ {match['hora']} hrs | {local} vs {visita}"

        with st.expander(titulo_partido, expanded=True):
            st.markdown(f"<div class='{card_class}'>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            col1.metric(f"🟢 {local}", f"{g_loc}" if is_post or is_live else "vs")
            col2.metric("⏰ Estado / Hora", match['hora'] if not is_live else estado_desc)
            col3.metric(f"🔴 {visita}", f"{g_vis}" if is_post or is_live else "vs")
            st.markdown("</div>", unsafe_allow_html=True)
