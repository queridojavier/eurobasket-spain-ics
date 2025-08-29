# Genera spain-eurobasket.ics sin dependencias externas.
# Intenta añadir el marcador final desde la página de FIBA con urllib + regex.
from datetime import datetime, timedelta, timezone
from urllib.request import urlopen, Request
import re

OUTFILE = "spain-eurobasket.ics"

# Partidos (hora peninsular, CEST UTC+2 en esas fechas)
GAMES = [
    ("2025-08-28", "14:00", "Georgia", "away", "Spyros Kyprianou Arena, Limassol (Chipre)"),
    ("2025-08-30", "20:30", "Bosnia y Herzegovina", "home", "Spyros Kyprianou Arena, Limassol (Chipre)"),
    ("2025-08-31", "17:15", "Chipre", "home", "Spyros Kyprianou Arena, Limassol (Chipre)"),
    ("2025-09-02", "20:30", "Italia", "away", "Spyros Kyprianou Arena, Limassol (Chipre)"),
    ("2025-09-04", "20:30", "Grecia", "home", "Spyros Kyprianou Arena, Limassol (Chipre)"),
]

# Mapas simples para casar nombres con FIBA en inglés
ALIAS = {
    "Bosnia y Herzegovina": "Bosnia",
    "Grecia": "Greece",
    "Georgia": "Georgia",
    "Chipre": "Cyprus",
    "Italia": "Italy",
}

def fetch_fiba_text():
    """Descarga la página de 'Games' de FIBA en texto plano. Si falla, devuelve ''. """
    try:
        url = "https://www.fiba.basketball/en/events/fiba-eurobasket-2025/games"
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        # Compactamos espacios para facilitar regex
        return re.sub(r"\s+", " ", html)
    except Exception:
        return ""

def find_score(fiba_text: str, rival_en: str):
    """
    Busca patrones tipo:
      'Spain 82-76 Italy'  o  'Italy 76-82 Spain'
    Devuelve '82-76' con España a la izquierda. Si no encuentra, None.
    """
    if not fiba_text:
        return None
    pattern1 = re.compile(r"(Spain|España)\s*(\d{2,3})\s*[-–]\s*(\d{2,3})\s*(" + re.escape(rival_en) + r")", re.I)
    pattern2 = re.compile(r"(" + re.escape(rival_en) + r")\s*(\d{2,3})\s*[-–]\s*(\d{2,3})\s*(Spain|España)", re.I)

    m1 = pattern1.search(fiba_text)
    if m1:
        a, b = m1.group(2), m1.group(3)
        return f"{a}-{b}"

    m2 = pattern2.search(fiba_text)
    if m2:
        a, b = m2.group(2), m2.group(3)
        # Aquí el rival está a la izquierda; ponemos a España a la izquierda del marcador
        return f"{b}-{a}"

    return None

def fold_ics_line(s: str) -> str:
    """
    Plegado ingenuo de líneas >75 octetos para cumplir con iCal.
    Continúa líneas con un espacio inicial.
    """
    out = []
    line = ""
    for ch in s:
        if len(line.encode("utf-8")) >= 73:
            out.append(line)
            line = " " + ch
        else:
            line += ch
    if line:
        out.append(line)
    return "\n".join(out)

def main():
    now_cest = datetime.now(timezone(timedelta(hours=2)))  # CEST
    fiba_text = fetch_fiba_text()

    lines = [
        "BEGIN:VCALENDAR",
        "PRODID:-//queridojavier//EuroBasket Spain 2025//ES",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:EuroBasket 2025 - España",
        "X-WR-TIMEZONE:Europe/Madrid",
    ]

    for date_iso, hour_str, rival, hv, venue in GAMES:
        # Construimos datetimes locales CEST y pasamos a UTC restando 2h
        y, m, d = map(int, date_iso.split("-"))
        hh, mm = map(int, hour_str.split(":"))
        start_local = datetime(y, m, d, hh, mm, tzinfo=timezone(timedelta(hours=2)))  # CEST
        end_local = start_local + timedelta(hours=2)
        start_utc = (start_local - timedelta(hours=2)).strftime("%Y%m%dT%H%M%SZ")
        end_utc = (end_local - timedelta(hours=2)).strftime("%Y%m%dT%H%M%SZ")

        # Resultado si ya terminó
        score = None
        if now_cest > end_local:
            rival_en = ALIAS.get(rival, rival).split()[0]
            score = find_score(fiba_text, rival_en)

        title = f"EuroBasket 2025: España vs {rival}" if hv == "home" else f"EuroBasket 2025: {rival} vs España"
        if score:
            title += f" ({score})"

        desc = f"{title}\\nSede: {venue}\\nGrupo C (Limassol).\\nTV en España: RTVE.\\nFuente horarios/sede: FIBA 'Games'."
        desc = fold_ics_line(f"DESCRIPTION:{desc}")

        uid = f"{date_iso}-{rival.replace(' ', '').lower()}@eurobasket-spain"
        dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dtstamp}",
            f"DTSTART:{start_utc}",
            f"DTEND:{end_utc}",
            f"SUMMARY:{title}",
            f"LOCATION:{venue}",
            desc,
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")

    with open(OUTFILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    main()
