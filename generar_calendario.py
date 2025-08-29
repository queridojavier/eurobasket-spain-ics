import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
import pytz
from datetime import datetime
from babel.dates import parse_date

# URL de la web de la FIBA con los partidos de España
URL = "https://www.fiba.basketball/eurobasket/2025/team/Spain"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

c = Calendar()

def obtener_datos_partidos():
    """Obtiene los datos de los partidos de la web de la FIBA."""
    try:
        response = requests.get(URL, headers=HEADERS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Encuentra los partidos en la sección de "Match schedule"
        matches = soup.find_all('div', class_='fiba-match-item-wrapper')

        if not matches:
            print("No se encontraron partidos en la página.")
            return []

        partidos = []
        for match in matches:
            try:
                # Extrae los datos
                
                # Ejemplo de fecha y hora
                date_str = match.find('div', class_='fiba-match-schedule-date').text.strip()
                time_str = match.find('div', class_='fiba-match-schedule-time').text.strip()
                
                # Ejemplo de equipos
                team1_name = match.find('span', class_='fiba-match-team1').text.strip()
                team2_name = match.find('span', class_='fiba-match-team2').text.strip()
                
                # Asumiendo que el resultado es el que aparece en la clase 'fiba-match-score'
                score_element = match.find('div', class_='fiba-match-score')
                score_str = score_element.text.strip().replace('\n', ' ').replace(' ', '') if score_element else 'vs'
                
                # Define el título del evento
                if 'vs' in score_str:
                    titulo = f"España vs {team2_name if team1_name == 'Spain' else team1_name}"
                else:
                    titulo = f"España vs {team2_name if team1_name == 'Spain' else team1_name} - Resultado: {score_str}"
                
                # Formato de fecha
                # '11 Nov 2024' -> '11 Nov 2024 18:00'
                fecha_hora_str = f"{date_str} {time_str}"
                
                # Usar babel para parsear la fecha en español si es necesario, si no, usa datetime
                # En este caso la FIBA usa formato inglés, así que 'datetime' es suficiente.
                fecha_hora_obj = datetime.strptime(fecha_hora_str, "%d %b %Y %H:%M")
                
                zona_horaria = pytz.timezone('Europe/Madrid')
                fecha_hora_local = zona_horaria.localize(fecha_hora_obj)
                
                partidos.append({
                    'titulo': titulo,
                    'fecha_hora': fecha_hora_local,
                    'resultado': score_str
                })
            except Exception as e:
                print(f"Error procesando un partido: {e}")
                continue
        return partidos
    except requests.exceptions.RequestException as e:
        print(f"Error al acceder a la URL: {e}")
        return []

def generar_ical(partidos):
    """Genera y guarda el archivo .ics."""
    for partido in partidos:
        evento = Event()
        evento.name = partido['titulo']
        evento.begin = partido['fecha_hora']
        
        if 'vs' not in partido['resultado']:
            evento.description = f"Partido del Eurobasket. Resultado: {partido['resultado']}"
        else:
            evento.description = "Partido del Eurobasket."
        
        c.events.add(evento)

    with open('spain_baloncesto.ics', 'w', encoding='utf-8') as f:
        f.writelines(c)

if __name__ == '__main__':
    partidos = obtener_datos_partidos()
    if partidos:
        generar_ical(partidos)
        print("Calendario generado con éxito.")
    else:
        print("No se pudo generar el calendario.")
