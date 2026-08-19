import streamlit as st
import requests
from datetime import datetime, timedelta
import zoneinfo

st.set_page_config(page_title="Parlay Analytics PRO", page_icon="⚽", layout="wide")

# Estilos CSS Limpios
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    
    /* Tarjeta Contenedora según estado */
    .card-live {
        background-color: #1A1D24;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
        border: 1px solid #2A2E39;
        border-left: 6px solid #FF5252;
        color: white;
    }
    .card-today {
        background-color: #1A1D24;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
        border: 1px solid #2A2E39;
        border-left: 6px solid #00E676;
        color: white;
    }
    .card-tomorrow {
        background-color: #1A1D24;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
        border: 1px solid #2A2E39;
        border-left: 6px solid #FFD600;
        color: white;
    }
    .card-upcoming {
        background-color: #1A1D24;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
        border: 1px solid #2A2E39;
        border-left: 6px solid #29B6F6;
        color: white;
    }
    
    .score-banner {
        background-color: #262A36;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        font-size: 18px;
        font-weight: bold;
        color: #FFFFFF;
        margin-bottom: 16px;
    }

    .draftea-item {
        background-color: #121418;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 10px;
        border: 1px solid #2A2E39;
    }
    .draftea-header-flex {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 13px;
        font-weight: bold;
        margin-bottom: 6px;
    }
    .draftea-title { color: #FFFFFF; }
    .draftea-details { color: #8A8F9D; font-size: 12px; }
    
    .progress-container {
        width: 100%;
        background-color: #262A36;
        border-radius: 6px;
        height: 16px;
        position: relative;
        overflow: hidden;
    }
    .progress-bar-green {
        background: linear-gradient(90deg, #00C853, #00E676);
        height: 100%;
        border-radius: 6px;
    }
    .progress-bar-red {
        background: linear-gradient(90deg, #D50000, #FF5252);
        height: 100%;
        border-radius: 6px;
    }
    .progress-val-text {
        position: absolute;
        right: 8px;
        top: 0px;
        font-size: 11px;
        font-weight: bold;
        color: #FFFFFF;
        line-height: 16px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚽ PARLAY ANALYTICS PRO")

# Zona Horaria
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
    fecha_inicio = (hoy_dt - timedelta(days=3)).strftime("%Y%m%d")
    fecha_fin = (hoy_dt + timedelta(days=7)).strftime("%Y%m%d")
    
    codigos = [codigo_liga]
    if codigo_liga == "uefa.champions":
        codigos.append("uefa.champions_qualifying")

    partidos_totales = []
    
    for cod in codigos:
        urls = [
            f"https://site.api.espn.com/apis/site/v2/sports/soccer/{cod}/scoreboard?dates={fecha_inicio}-{fecha_fin}",
            f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={fecha_inicio}-{fecha_fin}"
        ]
        
        events_encontrados = []
        for url in urls:
            try:
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    events = res.json().get('events', [])
                    for ev in events:
                        league_slug = ev.get('leagues', [{}])[0].get('slug', '')
                        league_name = ev.get('leagues', [{}])[0].get('name', '').lower()
                        
                        if cod == "uefa.champions" or cod == "uefa.champions_qualifying":
                            if "champions" in league_slug or "champions" in league_name:
                                events_encontrados.append(ev)
                        elif cod == "mex.1":
                            if "mex.1" in league_slug or "liga mx" in league_name:
                                events_encontrados.append(ev)
                        else:
                            events_encontrados.append(ev)
                    if events_encontrados:
                        break
            except Exception:
                pass

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

            stats_dict = {"local": {}, "visita": {}}
            for key, team in [("local", home), ("visita", away)]:
                for st_item in team.get('statistics', []):
                    stats_dict[key][st_item.get('name')] = st_item.get('displayValue', '0')

            partidos_totales.append({
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
                "stats": stats_dict
            })
            
    partidos_unicos = {p['id']: p for p in partidos_totales}.values()
    return list(partidos_unicos)

# Selector de Ligas con Badges
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

def armar_barra_draftea_html(titulo, actual_val, linea_val, extra_info="", is_boolean=False):
    if is_boolean:
        is_hit = bool(actual_val)
        porcentaje = 100 if is_hit else 0
        text_val = "SÍ" if is_hit else "NO"
        linea_str = "Ambos anotan"
    else:
        try:
            val_num = float(actual_val)
        except ValueError:
            val_num = 0.0
            
        porcentaje = min(100, int((val_num / linea_val) * 100)) if linea_val > 0 else 0
        is_hit = val_num >= linea_val
        text_val = f"{actual_val} / {linea_val}"
        linea_str = f"Línea: {linea_val}"
    
    status_icon = "✅" if is_hit else "🔴"
    bar_class = "progress-bar-green" if is_hit else "progress-bar-red"
    
    return f"""<div class="draftea-item"><div class="draftea-header-flex"><span class="draftea-title">{status_icon} {titulo} ({linea_str})</span><span class="draftea-details">{extra_info}</span></div><div class="progress-container"><div class="{bar_class}" style="width: {porcentaje}%;"></div><span class="progress-val-text">{text_val}</span></div></div>"""

if not matches:
    st.info("📌 No hay partidos programados para el filtro seleccionado.")
else:
    for match in matches:
        local = match['local']
        visita = match['visita']
        g_loc = match['local_score']
        g_vis = match['visita_score']
        tot_goles = g_loc + g_vis
        ambos_anotaron = (g_loc > 0 and g_vis > 0)
        
        estado_state = match['estado_state']
        estado_desc = match['estado_desc']
        cat_dia = match['cat_dia']
        stats = match['stats']
        
        is_live = (estado_state == 'in')
        is_post = (estado_state == 'post')

        card_class = "card-live" if is_live else (
            "card-today" if cat_dia == "today" else (
                "card-tomorrow" if cat_dia == "tomorrow" else "card-upcoming"
            )
        )

        info_loc = tabla.get(local, {"posicion": 10, "puntos": 15, "dif_goles": 0})
        info_vis = tabla.get(visita, {"posicion": 10, "puntos": 15, "dif_goles": 0})

        dg_total = abs(info_loc['dif_goles']) + abs(info_vis['dif_goles'])
        linea_goles_apuesta = 2.5 if dg_total > 5 else 1.5

        if is_live:
            header_str = f"🔴 EN VIVO ({estado_desc}) | {local} {g_loc} - {g_vis} {visita}"
        elif is_post:
            header_str = f"🏁 FINAL | {local} {g_loc} - {g_vis} {visita}"
        else:
            header_str = f"⏰ {match['hora']} hrs | {local} vs {visita}"

        corners_loc = stats['local'].get('wonCorners', stats['local'].get('corners', '0'))
        corners_vis = stats['visita'].get('wonCorners', stats['visita'].get('corners', '0'))
        try: tot_corners = int(corners_loc) + int(corners_vis)
        except ValueError: tot_corners = 0

        shots_loc = stats['local'].get('totalShots', stats['local'].get('shots', '0'))
        shots_vis = stats['visita'].get('totalShots', stats['visita'].get('shots', '0'))
        try: tot_shots = int(shots_loc) + int(shots_vis)
        except ValueError: tot_shots = 0

        shots_on_loc = stats['local'].get('shotsOnTarget', '0')
        shots_on_vis = stats['visita'].get('shotsOnTarget', '0')
        try: tot_shots_on = int(shots_on_loc) + int(shots_on_vis)
        except ValueError: tot_shots_on = 0

        yellow_loc = stats['local'].get('yellowCards', '0')
        yellow_vis = stats['visita'].get('yellowCards', '0')
        try: tot_yellow = int(yellow_loc) + int(yellow_vis)
        except ValueError: tot_yellow = 0

        # Diseño directo y sin recuadros confusos arriba
        html_cuadro_unico = f"""<div class="{card_class}"><div class="score-banner">{header_str}</div>{armar_barra_draftea_html(f'⚽ Goles Totales (+{linea_goles_apuesta})', tot_goles, linea_goles_apuesta, f"Marcador: {g_loc} - {g_vis}")}{armar_barra_draftea_html('🤝 Ambos Anotan (AA)', ambos_anotaron, 1.0, f"{local}: {g_loc} | {visita}: {g_vis}", is_boolean=True)}{armar_barra_draftea_html('🚩 Córners Totales', tot_corners, 9.5, f"{local}: {corners_loc} | {visita}: {corners_vis}")}{armar_barra_draftea_html('🎯 Tiros Totales', tot_shots, 22.5, f"{local}: {shots_loc} | {visita}: {shots_vis}")}{armar_barra_draftea_html('⚽ Tiros a Puerta', tot_shots_on, 8.5, f"{local}: {shots_on_loc} | {visita}: {shots_on_vis}")}{armar_barra_draftea_html('🟨 Tarjetas Amarillas', tot_yellow, 4.5, f"{local}: {yellow_loc} | {visita}: {yellow_vis}")}</div>"""
        
        st.markdown(html_cuadro_unico, unsafe_allow_html=True)
