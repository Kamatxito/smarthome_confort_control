import requests
import json
from datetime import datetime
import pytz

grafana_url = 'http://localhost:3003'
dashboard_uid = 'WOfYtDjnz'
dashboard_id = 1
panel_id = 1
api_key = ''

# Convertir la hora actual a milisegundos
current_time = datetime.now(pytz.timezone('UTC'))
current_timestamp = int(current_time.timestamp() * 1000)

anotacion = {
    "dashboardId": dashboard_id,
    "panelId": panel_id,
    "time": current_timestamp,
    "isRegion": False, # Indica si es un momento exacto de tiempo o un rango
    "tags": ["Prioridad X"],
    "text": "Hola mundo."
}

cabecerasGrafana = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {api_key}'
}

def añadirAnotacionGrafana(panelId, prioridad, parametro, mensaje):
    # Nombre Panel  Id
    # Temperatura	2
    # Vel. Viento	10
    # Humedad R.	4
    # Luminosidad   12
    # CO2           14
    anotacion['panelId'] = panelId
    anotacion['tags'] = [prioridad, parametro]
    anotacion['text'] = mensaje

    response = requests.post(f'{grafana_url}/api/annotations', headers=cabecerasGrafana, data=json.dumps(anotacion))

    if response.status_code == 200:
        print('Anotación agregada con éxito')
    else:
        print(f'Error al agregar anotación: {response.content}')

añadirAnotacionGrafana(2, "Prioridad alta", "Temperatura", "Abriendo ventanas")