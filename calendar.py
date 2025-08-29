from datetime import datetime, timedelta, timezone
import requests
from bs4 import BeautifulSoup
from dateutil import tz
from ics import Calendar, Event

# Config básica
TZ_MADRID = tz.gettz("Europe/Madrid")
TZ_UTC = tz.UTC
OUTFILE = "spain-eurobasket.ics"

# Partidos de España (fase de grupos, horas península)
games = [
    # (fecha ISO, hora, rival, sede, etiqueta_local_visitante, id "clave")
    ("2025-08-28", "14:00", "Georgia", "Spyros Kyprianou Arena, Limassol (Chipre)", "Fuera", "geo-esp"),
    ("2025-08-30", "20:30", "Bosnia y Herzegovina", "Spyros Kyprianou Arena, Limassol (Chipre)", "Casa", "esp-bih"),
    ("2025-08-31", "17:15", "Chipre", "Spyros Kyprianou Arena, Limassol (Chipre)", "Casa", "esp-cyp"),
    ("2025-09-02", "20:30", "Italia", "Spyros Kyprianou Arena, Limassol (Chipre)", "Fuera", "ita-esp"),
    ("2025-09-04", "20:30", "Grecia", "Spyros Kyprianou Arena, Limassol (Chipre)", "Casa", "esp-grc"),
]

def fetch_result(team_a, team_b):
    """
    Intenta encontrar un resultado final fiable para {España vs Rival}.
    Fuente de apoyo: página de FIBA 'Games' y resumen en Olympics.com.
    Si no hay resultado aún o la estructura cambia, devuelve None.
    """
    # 1) Olympics.com resumen (suele listar resultados una vez finalizados)
    try:
        url = "https://www.olympics.com/en/news/basketball-fiba-eurobasket-2025-full-schedule-all-results-standings-complete-list"
        html = requests.get(url, timeout=15).text
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True).lower()
        # Búsqueda muy básica de marcador "spain X–Y rival" o parecido
        # Nota: robustez mínima; si cambian el formato, no se rompe nada crítico.
        for sep in [" ", "–", "-", "—"]:
            patterns = [
                f"spain {sep}", f"españa {sep}"
            ]
        # Heurística: no fiable para todos los idiomas; preferimos FIBA si hay.
    except Exception:
        pass

    # 2) FIBA Games page (puede requerir JS; si no carga, salimos)
    try:
        url = "https://www.fiba.basketball/en/events/fiba-eurobasket-2025/games"
        html = requests.get(url, timeout=15).text
        soup = BeautifulSoup(html, "html.parser")
        # Buscamos líneas con Spain y el rival, seguido de dígitos
        txt = soup.get_text(" ", strip=True)
        import re
        # Captura patrones tipo "Spain 82-76 Italy" o "Georgia 70-77 Spain"
        m = re.findall(r"(Spain|España)\s+(\d{2,3})\s*[-–]\s*(\d{2,3})\s+([A-Za-zÀ-ÿ]+)", txt)
        # y también al revés
        m += re.findall(r"([A-Za-zÀ-ÿ]+)\s+(\d{2,3})\s*[-–]\s*(\d{2,3})\s+(Spain|España)", txt)
        # Normalizamos a "España X–Y Rival"
        results = []
        for g in m:
            if g[0].lower() in ("spain", "españa"):
                left_name, a, b, right_name = g[0], g[1], g[2], g[3]
                team_left = "España"
                team_right = right_name
                score = f"{a}-{b}"
            else:
                left_name, a, b, right_name = g[0], g[1], g[2], g[3]
                team_left = left_name
                team_right = "España"
                score = f"{a}-{b}"
            results.append((team_left, score, team_right))
        # Intentamos casar con el rival concreto
        for tl, score, tr in results:
            if "espa" in tl.lower() or "espa" in tr.lower():
                if team_b.lower() in (tl.lower(), tr.lower()):
                    return score
    except Exception:
        pass

    return None

def main():
    cal = Calendar()
    now = datetime.now(TZ_MADRID)

    for date_iso, hour_str, rival, venue, hv, key in games:
        start_local = datetime.fromisoformat(f"{date_iso}T{hour_str}:00").replace(tzinfo=TZ_MADRID)
        end_local = start_local + timedelta(hours=2)

        # Intentar resultado si ya terminó
        score = None
        if now > end_local:
            # Nombrado rival en inglés/latín básico para casarlo arriba
            rival_simple = rival.split(" ")[0].lower()
            # FIBA/olympics suelen usar "Spain" + "Italy/Georgia/Greece/Cyprus/Bosnia"
            map_alias = {
                "Bosnia": "Bosnia", "Bosnia": "Bosnia", "Grecia": "Greece",
                "Georgia": "Georgia", "Chipre": "Cyprus", "Italia": "Italy"
            }
            look_for = map_alias.get(rival.split()[0], rival.split()[0])
            score = fetch_result("Spain", look_for)

        # Título y descripción
        title = f"EuroBasket 2025: España vs {rival}" if hv == "Casa" else f"EuroBasket 2025: {rival} vs España"
        if score:
            title += f" ({score})"

        desc = f"{title}\nSede: {venue}\nGrupo C (Limassol).\nEmisión en España: RTVE."
        # Fuente de horarios/sedes (confirmadas por FIBA/organización chipriota)
        desc += "\nFuentes: FIBA 'Games' y calendario de Chipre (saltos 15:00/18:15/21:30 hora local)."

        e = Event()
        e.name = title
        e.location = venue
        e.begin = start_local.astimezone(TZ_UTC)
        e.end = end_local.astimezone(TZ_UTC)
        e.description = desc
        e.transparent = True  # no bloquear

        cal.events.add(e)

    with open(OUTFILE, "w", encoding="utf-8") as f:
        f.writelines(cal.serialize_iter())

if __name__ == "__main__":
    main()
