# Este script realiza las funciones de registrar datos y gestionar los actuadores simulando cambios en 
# el clima. Por ejemplo: se puede simular un día caloroso de humedad alta o un día frío con mucho viento.

# --- MÓDULOS IMPORTADOS ---
from time import sleep
import requests
from datetime import datetime
from pathlib import Path
from influxdb import InfluxDBClient
import pytz
import pymongo
from soco import SoCo
from gtts import gTTS
import os

# --- VARIABLES Y MÉTODOS A USAR ---
# Tendremos un valor para cada variable y así poder realizar simulaciones más precisas
aux_simulador = 1
valor_simulacion = 0.0
tempExterior_aume_simulacion = 0.0
tempExterior_desc_simulacion = 0.0
tempInterior_aume_simulacion = 0.0
tempInterior_desc_simulacion = 0.0
baliza_simulacion_temp_ext_aume = False
baliza_simulacion_temp_int_aume = False
baliza_simulacion_temp_ext_desc = False
baliza_simulacion_temp_int_desc = False

# API:
dir = "http://remote:LabSmarthome21@192.168.7.210/scada-remote" # Direccion de la API

parametros_POST = { # Parametros para la conexion a la API
    'm': 'json', # Formato de salida
    'r': 'grp', # Request
    'fn': 'write', # Función a ejecutar
    'alias': '0/0/0', # Dirección del objeto
    'value': '' # Nuevo valor del objeto
}
def GET_datos(parametros): # Conexion y peticion a la API
    r = requests.get(url=dir, params=parametros)
    return r.json()
    return 15
def POST_datos(parametros):
    r = requests.post(url=dir, params=parametros)
    print(r.status_code)
    print(r.json())

# Sonos
def reproducir_audio(mensaje):
    '''
    sonos = SoCo('192.168.7.14')
    sonos.status_light = True
    sonos.volume = 10
    '''
    tts = gTTS(mensaje, lang='es')
    tts.save('mensaje_audio.mp3')
    '''
    sonos.play_uri("URL")
    '''
    os.remove("mensaje_audio.mp3")

# --- PROGRAMA PRINCIPAL ---
while (True):

    if (aux_simulador == 1):
        # --- CONSULTAS AL USUARIO ---
        print("Te doy la bienvenida al simulador, active las opciones que prefiera lanzar:")
        opcion = input("Activar control de temperatura (True/False): ")
        baliza_control_temp = bool(opcion)
        if (baliza_control_temp):
            opcion = input("Activar aumento de temperatura exterior (True/False): ")
            baliza_simulacion_temp_ext_aume = bool(opcion)
            opcion = input("Activar aumento de temperatura interior (True/False): ")
            baliza_simulacion_temp_int_aume = bool(opcion)
            opcion = input("Activar descenso de temperatura exterior (True/False): ")
            baliza_simulacion_temp_ext_desc = bool(opcion)
            opcion = input("Activar descenso de temperatura interior (True/False): ")
            baliza_simulacion_temp_int_desc = bool(opcion)
        aux_simulador = 0

    # PARTE 1: RECOGIDA DE DATOS
    parametros_GET = { # Parametros para la conexion a la API
        'm': 'json', # Formato de salida
        'r': 'grp', # Request
        'fn': 'getvalue', # Función a ejecutar
        'alias': '3/1/1' # Dirección del objeto
    }

    # Datos que se recogen de la SmartHome
    # Temperatura interior
    tempInterior = GET_datos(parametros_GET)
    tempInterior += 0.0
    # En el caso de que esté activa la simulación, sumará al valor original el parámetro de simulación. 
    # Además, para mantener consistencia en la propia simulación, si en la ejecución se ha simulado en algún 
    # momento la variable, esta seguirá sumándose sin aumentar para mantener la coherencia.
    if (baliza_simulacion_temp_int_aume or tempInterior_aume_simulacion > 0.0):
        tempInterior += tempInterior_aume_simulacion
    if (baliza_simulacion_temp_int_desc or tempInterior_desc_simulacion > 0.0):
        tempInterior -= tempInterior_desc_simulacion
    
    # Temperatura exterior
    parametros_GET['alias'] = '3/2/5' # Alias del siguiente sensor
    tempExterior = GET_datos(parametros_GET)
    tempExterior += 0.0 # Para evitar valores enteros
    if (baliza_simulacion_temp_ext_aume or tempExterior_aume_simulacion > 0.0):
        tempExterior += tempExterior_aume_simulacion
    if (baliza_simulacion_temp_ext_desc or tempExterior_desc_simulacion > 0.0):
        tempExterior -= tempExterior_desc_simulacion
    
    # CO2
    parametros_GET['alias'] = '3/2/1'
    CO2 = GET_datos(parametros_GET)
    CO2 += 0.0 # Para evitar valores enteros

    # Humedad interior
    parametros_GET['alias'] = '3/2/2'
    humedadInterior = GET_datos(parametros_GET)
    humedadInterior += 0.0 # Para evitar valores enteros

    # Velocidad viento
    parametros_GET['alias'] = '3/2/4'
    velocidadViento =  GET_datos(parametros_GET)
    velocidadViento += 0.0 # Para evitar valores enteros

    # Luz exterior
    parametros_GET['alias'] = '3/2/6'
    luxExterior = GET_datos(parametros_GET)
    luxExterior += 0.0 # Para evitar valores enteros

    # Lluvia
    parametros_GET['alias'] = '3/2/10'
    lluvia = GET_datos(parametros_GET)

    # Actualizamos los valores de simulación
    if (baliza_simulacion_temp_int_aume and tempInterior_aume_simulacion <= 20.0):
        tempInterior_aume_simulacion += 1.0
    if (baliza_simulacion_temp_int_desc and tempInterior_desc_simulacion <= 20.0):
        tempInterior_desc_simulacion += 1.0
    if (baliza_simulacion_temp_ext_aume and tempExterior_aume_simulacion <= 20.0):
        tempExterior_aume_simulacion += 1.0
    if (baliza_simulacion_temp_ext_desc and tempExterior_desc_simulacion <= 20.0):
        tempExterior_desc_simulacion += 1.0

    # PARTE 2: ENVIO DE DATOS A BD INFLUX Y A BD MONGO

    # Configurar conexiones...
    conexInfluxDB = InfluxDBClient('localhost', 8086, 'admin', 'admin', 'smarthome') # ... a InfluxDB
    conexMongoDB = pymongo.MongoClient("mongodb://localhost:27017/") # ... a mongoDB
    mongoDBActual = conexMongoDB["smarthome"]
    mongoColecActual = mongoDBActual["tempInterior"]

    # La zona horaria sera UTC para evitar problemas de incompatibilidad con Grafana
    zonaHoraria = pytz.timezone('UTC') 
    now = datetime.now(zonaHoraria)

    # Se configura un payload, carga util, para cada una de las medidas que se realizan y se actualiza la base de datos
    # Temperatura
    json_payload = []
    json_data = {
        "measurement": "tempInterior",
        "time": now,
        "fields": {
            'value': tempInterior
        }
    }
    json_payload.append(json_data)
    # Se debe insertar ya en la mongoDB y cambiar la coleccion
    mongoColecActual.insert_one(json_data)
    mongoColecActual = mongoDBActual["tempExterior"]
    json_data = {
        "measurement": "tempExterior",
        "time": now,
        "fields": {
            'value': tempExterior
        }
    }
    json_payload.append(json_data)
    mongoColecActual.insert_one(json_data)
    mongoColecActual = mongoDBActual["CO2"]

    # Contaminación
    json_data = {
        "measurement": "CO2",
        "time": now,
        "fields": {
            'value': CO2
        }
    }
    json_payload.append(json_data)
    mongoColecActual.insert_one(json_data)
    mongoColecActual = mongoDBActual["humedadInterior"]

    # Humedad
    json_data = {
        "measurement": "humedadInterior",
        "time": now,
        "fields": {
            'value': humedadInterior
        }
    }
    json_payload.append(json_data)
    mongoColecActual.insert_one(json_data)
    mongoColecActual = mongoDBActual["velocidadViento"]

    # Velocidad del viento
    json_data = {
        "measurement": "velocidadViento",
        "time": now,
        "fields": {
            'value': velocidadViento
        }
    }
    json_payload.append(json_data)
    mongoColecActual.insert_one(json_data)
    mongoColecActual = mongoDBActual["luxExterior"]

    # Luminosidad
    json_data = {
        "measurement": "luxExterior",
        "time": now,
        "fields": {
            'value': luxExterior
        }
    }
    json_payload.append(json_data)
    mongoColecActual.insert_one(json_data)
    mongoColecActual = mongoDBActual["lluvia"]

    # Lluvia
    json_data = {
        "measurement": "lluvia",
        "time": now,
        "fields": {
            'value': lluvia
        }
    }
    json_payload.append(json_data)
    conexInfluxDB.write_points(json_payload)
    mongoColecActual.insert_one(json_data)

    # PARTE 3: EXPORTACION DE DATOS EN TXT
    
    now = datetime.now()
    fecha = now.strftime('%d-%m-%Y')
    hora = now.strftime('%H:%M')

    # Debemos comprobar si existe el archivo para añadir la cabecera o no
    fileObj = Path('C:\\Users\\TFG3\\Desktop\\David TFG\\txtLogs\\' + fecha + '.txt')
    if(fileObj.is_file()):
        f = open('C:\\Users\\TFG3\\Desktop\\David TFG\\txtLogs\\' + fecha+'.txt', 'a')
        f.write(hora + '\t%2.1f\t%2.1f\t%3.2f\t%d\t%d\t%4.2f\t%d\n' % (tempInterior, tempExterior, CO2, humedadInterior, velocidadViento, luxExterior, not lluvia))
        f.close
    else:
        print('No existe el fichero')
        f = open('C:\\Users\\TFG3\\Desktop\\David TFG\\txtLogs\\' + fecha+'.txt', 'w')
        f.write('HORA\tTEMPERATURA INT.\tTEMPERATURA EXT.\tCO2\tHUMEDAD INT.\tVEL. VIENTO\tLUMINOSIDAD EXT.\tLLUVIA\n')
        f.write(hora + '\t%2.1f\t%2.1f\t%3.2f\t%d\t%d\t%4.2f\t%d\n' % (tempInterior, tempExterior, CO2, humedadInterior, velocidadViento, luxExterior, not lluvia))
        f.close

    # PARTE 4: GESTOR DEL SIMULADOR

    # Gestor de confort
    if (baliza_control_temp):
        # Recogida de datos
        parametros_GET['alias'] = '2/3/7'
        altura_ventana = GET_datos(parametros_GET)
        if (altura_ventana < 100):
            print("La ventana está abierta: " + str(altura_ventana))
        else:
            print("La ventana está cerrada: " + str(altura_ventana))
        print("Temperatura interior: " + str(tempInterior))
        print("Temperatura exterior: " + str(tempExterior))

        # Gestión de cada caso
        if ((tempInterior < 20.0) and (tempExterior > 20.0 or tempExterior > tempInterior) and (altura_ventana==100)):
            print("Temperatura baja en el interior, abriendo ventanas.")
            reproducir_audio("Temperatura baja en el interior, abriendo ventanas.")
            parametros_POST['alias'] = '2/3/5'
            parametros_POST['value'] = 0
            POST_datos(parametros_POST)
        if ((tempInterior < 20.0) and (tempExterior < 20.0 or tempExterior < tempInterior) and (altura_ventana<100)):
            print("Temperatura baja en el interior y en el exterior, cerrando ventanas.")
            reproducir_audio("Temperatura baja en el interior, abriendo ventanas.")
            parametros_POST['alias'] = '2/3/5'
            parametros_POST['value'] = 1
            POST_datos(parametros_POST)
        if ((tempInterior > 25.0) and (tempExterior > 25.0) and (tempExterior > tempInterior) and (altura_ventana<100)):
            print("Temperatura alta en el interior y exterior, cerrando ventanas.")
            reproducir_audio("Temperatura alta en el interior y exterior, cerrando ventanas.")
            parametros_POST['alias'] = '2/3/5'
            parametros_POST['value'] = 1
            POST_datos(parametros_POST)
        if ((tempInterior > 25.0) and (tempExterior < 25.0 or tempExterior < tempInterior) and (altura_ventana==100)):
            print("Temperatura alta en el interior, abriendo ventanas.")
            reproducir_audio("Temperatura alta en el interior, abriendo ventanas.")
            parametros_POST['alias'] = '2/3/5'
            parametros_POST['value'] = 0
            POST_datos(parametros_POST)

    print("Datos simulados correctamente: " + str(fecha) + " " + str(hora))
    opcion = input("¿Quieres cambiar las opciones del simulador? (True/False): ")
    baliza_opcion = bool(opcion)
    if baliza_opcion:
        aux_simulador = 1