import pytz
from datetime import datetime

# API
api_Dir = "http://remote:LabSmarthome21@192.168.7.210/scada-remote"
parametros_GET = {'m': 'json', 'r': 'grp', 'fn': 'getvalue', 'alias': '0/0/0'}
parametros_POST = {'m': 'json', 'r': 'grp', 'fn': 'write', 'alias': '0/0/0', 'value': ''}

# InfluxDB
INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USER = 'admin'
INFLUXDB_PASS = 'admin'
INFLUXDB_DB = 'smarthome'

# Grafana
grafana_url = 'http://localhost:3003'
dashboard_uid = 'WOfYtDjnz'
dashboard_id = 1
panel_id = 1
api_key = ''
anotacion = {
    "dashboardId": dashboard_id,
    "panelId": panel_id,
    "time": int(datetime.now(pytz.timezone('UTC')).timestamp() * 1000),
    "isRegion": False, # Indica si es un momento exacto de tiempo o un rango
    "tags": ["Prioridad X"],
    "text": "Hola mundo."
}
cabecerasGrafana = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {api_key}'
}

# Confort
CO2_MED = 1000  # ppm
CO2_MAX = 2000  # ppm
TEMP_MIN = 20  # °C
TEMP_MAX = 25  # °C
HUMEDAD_MIN = 30  # %
HUMEDAD_MAX = 50  # %
VEL_VIENTO_MAX = 10  # m/s
flag_calefaccion = 0
flag_aire_acondicionado = 0