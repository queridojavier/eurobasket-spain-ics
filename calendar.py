from datetime import datetime, timedelta
from dateutil import tz
import re
import requests

# Config
TZ_MADRID = tz.gettz("Europe/Madrid")
TZ_UTC = tz.gettz("UTC")
OUTFILE = "spain-eurobasket.ics"

# Partidos (hora peninsular)
GAMES = [
    ("2025-08-28", "14:00", "Georgia", "Spyros Kyprianou Arena, Limassol (Chipre)", "away"),
    ("2025-08-30", "20:30", "Bosnia y Herzegovina", "Spyros Kyprianou Arena, Limassol (Chipre)", "home"),
    ("2025-08-31", "17:15", "Chipre", "Spyros Kyprianou Arena, Limassol (Chipre)", "home"),
    ("2025-09-02", "20:30", "Italia", "Spyros Kyprianou Arena, Limassol (Chipre)", "away"),
    ("2025-09-04", "20:30", "Grecia", "Spyros Kyprianou Arena, Limassol (Chipre)", "home"),
]

# Alias sencillos para casar nombres con fuentes en inglés
ALIAS = {
    "Bosnia y Herzegovina": "Bosnia",
    "Grecia": "Greece",
    "Georgia": "Georgia",
    "Chipre": "Cyprus",
    "Italia": "Italy",
}

def fetch_result(rival_en: str):
    """
    Intenta sacar marcadores finales desde la página 'Games' de FIBA.
    Si no encuentra o la página cambia, devuelve None y seguimos felices.
    """
    try:
        url = "https://www.fiba.basketball/en/events/fiba-eurobasket-2025/games"
        html = requests.get(url, timeout=20).text
        txt = re.sub(r"\s+", " ", html)
        # Busca patrones tipo "Spain 82-76 Italy" o "Italy 76-82 Spain"
        patt1 = re.findall(r"(Spain|España)\s*(\d{2,3})\s*[-–]\s*(\d{2,3})\s*(" + re.escape(rival_en) + r")", txt, flags=re.I)
        patt2 = re.findall(r"(" + re.escape(rival_en) + r")\s*(\d{2,3})\s*[-–]\s*(\d{2,3})\s*(Spain|España)", txt, flags=re.I)
        # Priorizamos que haya números y devolvemos "X-Y" con España a la izquierda si procede
        if patt1:
            _, a, b, _ = patt1[0]
            return f"{a}-{b}"
        if patt2:
            _, a, b, _ = patt2[0]
            return f"{b}-{a}"
    except Exception:
        pass
    return None

def dt_local_to_utc(dt_local):
    return dt_local.replace(tzinfo=TZ_MADRID).astimezone(TZ_UTC)

def fold_ics(text):
    # Plegado simple a 75 octetos aprox. para DESCRIPTION largas
    out = []
    line = ""
    for ch in text:
        if len(line.encode("utf-8")) >= 73:
            out.append(line)
            line = " " + ch  # continuation line empieza con espacio
        else:
            line += ch
    if line:
        out.append(line)
    return "\n".join(out)

def main():
    now = datetime.now(TZ_MADRID)

    lines = [
        "BEGIN:VCALENDAR",
        "PRODID:-//queridojavier//EuroBasket Spain 2025//ES",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:EuroBasket 2025 - España",
        "X-WR-TIMEZONE:Europe/Madrid",
    ]

    for date_iso, hour_str, rival, venue, hv in GAMES:
        start_local = datetime.fromisoformat(f"{date_iso}T{hour_str}:00")
        end_local = start_local + timedelta(hours=2)

        # Intento de resultado si ya terminó
        result = None
        if now > end_local:
            rival_en = ALIAS.get(rival, rival).split()[0]
            result = fetch_result(rival_en)

        # Título
        if hv == "home":
            title = f"EuroBasket 2025: España vs {rival}"
        else:
            title = f"EuroBasket 2025: {rival} vs España"
        if result:
            title += f" ({result})"

        # Campos ICS
        dtstart_utc = dt_local_to_utc(start_local).strftime("%Y%m%dT%H%M%SZ")
        dtend_utc = dt_local_to_utc(end_local).strftime("%Y%m%dT%H%M%SZ")
        dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

        desc = (
            f"{title}\\nSede: {venue}\\nGrupo C (Limassol).\\n"
            "TV en España: RTVE.\\n"
            "Fuente horarios/sede: FIBA 'Games'."
        )
        desc = fold_ics(desc)

        uid = f"{date_iso}-{rival.replace(' ', '').lower()}@eurobasket-spain"

        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dtstamp}",
            f"DTSTART:{dtstart_utc}",
            f"DTEND:{dtend_utc}",
            f"SUMMARY:{title}",
            f"LOCATION:{venue}",
            f"DESCRIPTION:{desc}",
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")

    with open(OUTFILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    main()
