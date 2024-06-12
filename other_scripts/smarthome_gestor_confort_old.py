# VIEJA VERSION
# En este script se gestiona qué parámetros son controlados automáticamente. Primero pregunta al usuario por
# qué campos controlar y entonces actúa sobre la smarthome en función de los valores que se van obteniendo.

import requests
from time import sleep
from soco import SoCo
from gtts import gTTS
import os

# Balizas para activar cada control
baliza_temp = False

# Configuración para el acceso a los sensores
dir = "http://remote:LabSmarthome21@192.168.7.210/scada-remote" # Direccion de la API
parametros_GET = { # Parametros para la conexion a la API
    'm': 'json', # Formato de salida
    'r': 'grp', # Request
    'fn': 'getvalue', # Función a ejecutar
    'alias': '0/0/0' # Dirección del objeto
}
parametros_POST = { # Parametros para la conexion a la API
    'm': 'json', # Formato de salida
    'r': 'grp', # Request
    'fn': 'write', # Función a ejecutar
    'alias': '0/0/0', # Dirección del objeto
    'value': '' # Nuevo valor del objeto
}
def GET_datos(parametros):
    r = requests.get(url=dir, params=parametros)
    return r.json()
def POST_datos(parametros):
    r = requests.post(url=dir, params=parametros)
    print(r.status_code)
    print(r.json())

# Método para generar y reproducir mensaje en el Sonos
def reproducir_audio(mensaje):
    sonos = SoCo('192.168.7.12')
    sonos.status_light = True
    sonos.volume = 30
    tts = gTTS(mensaje, lang='es')
    tts.save('mensaje_audio.mp3')
    sonos.play_uri("mensaje_audio.mp3")
    os.remove("mensaje_audio.mp3")

# Consultas al usuario
opcion = input("Activar control de temperatura (True/False): ")
baliza_temp = bool(opcion)

while (True):
    # Gestor de confort
    if (baliza_temp):
        # Recogida de datos
        parametros_GET['alias'] = '3/2/5'
        temp_exterior = GET_datos(parametros_GET)
        temp_exterior += 0.0 # Para evitar valores enteros
        print(temp_exterior)
        parametros_GET['alias'] = '3/1/1'
        temp_interior = GET_datos(parametros_GET)
        temp_interior += 0.0 # Para evitar valores enteros
        print(temp_interior)
        parametros_GET['alias'] = '2/3/7'
        altura_ventana = GET_datos(parametros_GET)
        print(altura_ventana)

        # Gestión de cada caso
        if ((temp_interior < 20) and (temp_exterior > temp_interior) and (altura_ventana==100)):
            print("Temperatura baja en el interior, abriendo ventanas.")
            reproducir_audio("Temperatura baja en el interior, abriendo ventanas.")
            parametros_POST['alias'] = '2/3/5'
            parametros_POST['value'] = 0
            POST_datos(parametros_POST)
        if ((temp_interior > 25) and (temp_exterior > temp_interior) and (altura_ventana<100)):
            print("Temperatura alta en el interior, cerrando ventanas.")
            reproducir_audio("Temperatura alta en el interior, cerrando ventanas.")
            parametros_POST['alias'] = '2/3/5'
            parametros_POST['value'] = 1
            POST_datos(parametros_POST)
            
    sleep(1*60)