from datetime import datetime, timedelta
import zoneinfo # Para manejar la zona horaria real (México/América)

@st.cache_data(ttl=60)
def obtener_eventos_general(codigo_liga):
    # Definimos la zona horaria local para que no choque con la UTC de ESPN
    try:
        tz_local = zoneinfo.ZoneInfo("America/Mexico_City")
    except Exception:
        tz_local = None

    hoy_dt = datetime.now(tz_local) if tz_local else datetime.now()
    
    # Rango de 10 días alrededor de hoy
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
                
                # Convertimos el string ISO de ESPN (UTC) a objeto datetime real
                date_utc_str = ev.get('date', '')
                if date_utc_str:
                    dt_utc = datetime.fromisoformat(date_utc_str.replace('Z', '+00:00'))
                    # Convertimos a la hora local
                    dt_local = dt_utc.astimezone(tz_local) if tz_local else dt_utc
                    fecha_p = dt_local.strftime("%Y-%m-%d")
                    hora_p = dt_local.strftime("%H:%M")
                else:
                    fecha_p = ""
                    hora_p = ""

                # Categoría de día corregida
                if fecha_p == str_hoy:
                    cat_dia = "today"
                elif fecha_p == str_manana:
                    cat_dia = "tomorrow"
                elif fecha_p == str_ayer:
                    cat_dia = "yesterday"
                else:
                    cat_dia = "upcoming"

                # Jugadores / Tiradores destacados
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
    except Exception as e:
        pass
    return []
