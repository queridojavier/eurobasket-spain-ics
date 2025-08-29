import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
import pytz
from datetime import datetime

# URL de la web de la FIBA con los partidos
URL = "https://www.fiba.basketball/eurobasket/2025/team/Spain"

# Cabeceras para simular un navegador
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Crear una instancia de un calendario
c = Calendar()

def obtener_datos_partidos():
    """Obtiene los datos de los partidos de la web."""
    try:
        response = requests.get(URL, headers=HEADERS)
        response.raise_for_status()  # Lanza una excepción para errores de HTTP

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Encuentra la sección de los partidos (ajusta el selector según la estructura de la web)
        matches_section = soup.find('div', class_='matches-section') # Reemplaza con la clase correcta

        if not matches_section:
            print("No se encontraron partidos.")
            return []

        partidos = []
        for match in matches_section.find_all('div', class_='match-item'): # Reemplaza con la clase correcta
            try:
                # Extrae la fecha, hora, rival y resultado (ajusta los selectores)
                fecha_str = match.find('span', class_='match-date').text.strip()
                hora_str = match.find('span', class_='match-time').text.strip()
                rival = match.find('span', class_='opponent-name').text.strip()
                
                # Ejemplo de cómo obtener el resultado si existe
                resultado_element = match.find('span', class_='match-score')
                resultado = resultado_element.text.strip() if resultado_element else "Resultado pendiente"

                # Convierte la fecha y hora a un objeto datetime
                # Asegúrate de que el formato de fecha sea el correcto
                fecha_hora_str = f"{fecha_str} {hora_str}"
                fecha_hora_obj = datetime.strptime(fecha_hora_str, "%d %b %Y %H:%M") 
                
                # Asigna una zona horaria, por ejemplo 'Europe/Madrid'
                zona_horaria = pytz.timezone('Europe/Madrid')
                fecha_hora_local = zona_horaria.localize(fecha_hora_obj)

                partidos.append({
                    'rival': rival,
                    'fecha_hora': fecha_hora_local,
                    'resultado': resultado
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
        evento.name = f"España vs {partido['rival']}"
        evento.begin = partido['fecha_hora']
        
        if "Resultado" not in partido['resultado']: # El partido ha terminado
            evento.name += f" - Resultado: {partido['resultado']}"
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
