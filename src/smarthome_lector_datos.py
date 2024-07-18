#
# --- SCRIPT DE RECOGIDA DE DATOS EN LA SMARTHOME --- 
#
# En este script se realiza todo el proceso de recogida de datos de los sensores a traves de la API de la SmartHome.
# Esos datos se almacenan en dos bases de datos: una tipo temporal, influxDB; y otra tipo no SQL, mongoDB. 
# Por último, también guarda en un fichero de texto una copia de todos los datos que recoge.

from time import sleep
import requests
from datetime import datetime
from pathlib import Path
from influxdb import InfluxDBClient
import pytz
import pymongo

# Variables y estructuras necesarias
api_Dir = "http://remote:LabSmarthome21@192.168.7.210/scada-remote" # Direccion de la API
parametros = { # Parametros para la conexion a la API
    'm': 'json', # Formato de salida
    'r': 'grp', # Request
    'fn': 'getvalue', # Función a ejecutar
    'alias': '3/1/1' # Dirección del objeto
}

# Método que realiza una petición a la API y obtiene los datos del sensor actual
def obtener_datos_sensor(alias):
    parametros['alias'] = alias
    resultadoPeticion = requests.get(url=api_Dir, params=parametros)
    datos = resultadoPeticion.json()
    if alias not in ['3/2/10', '2/3/7']:
        datos += 0.0
    return datos

# PROGRAMA PRINCIPAL

while (True):

    # PARTE 1: RECOGIDA DE DATOS

    # Datos que se recogen de la SmartHome
    tempInterior = obtener_datos_sensor('3/1/1')
    tempExterior = obtener_datos_sensor('3/2/5')
    CO2 = obtener_datos_sensor('3/2/1')
    humedadInterior = obtener_datos_sensor('3/2/2')
    velocidadViento = obtener_datos_sensor('3/2/4')
    luxExterior = obtener_datos_sensor('3/2/9')
    lluvia = obtener_datos_sensor('3/2/10')
    alturaEstorDormitorio = obtener_datos_sensor('2/3/7')

    # PARTE 2: ENVIO DE DATOS A BD INFLUX Y A BD MONGO

    # Configurar conexiones a influx y mongoDB
    conexInfluxDB = InfluxDBClient('localhost', 8086, 'admin', 'admin', 'smarthome') # ... a InfluxDB
    conexMongoDB = pymongo.MongoClient("mongodb://localhost:27017/") # ... a mongoDB
    mongoDBActual = conexMongoDB["smarthome"]
    mongoColecActual = mongoDBActual["tempInterior"]

    # La zona horaria sera UTC para evitar problemas de incompatibilidad con Grafana
    zonaHoraria = pytz.timezone('UTC') 
    now = datetime.now(zonaHoraria)

    # Se configura un payload, carga util, para cada una de las medidas que se realizan y se actualiza la base de datos
    json_payload = []

    # Temperatura interior
    data = {
        "measurement": "tempInterior",
        "time": now,
        "fields": {
            'value': tempInterior
        }
    }
    json_payload.append(data)
    # Se debe insertar ya en la mongoDB y cambiar la coleccion
    mongoColecActual.insert_one(data)
    mongoColecActual = mongoDBActual["tempExterior"]

    # Temperatura exterior
    data = {
        "measurement": "tempExterior",
        "time": now,
        "fields": {
            'value': tempExterior
        }
    }
    json_payload.append(data)
    mongoColecActual.insert_one(data)
    mongoColecActual = mongoDBActual["CO2"]

    # CO2
    data = {
        "measurement": "CO2",
        "time": now,
        "fields": {
            'value': CO2
        }
    }
    json_payload.append(data)
    mongoColecActual.insert_one(data)
    mongoColecActual = mongoDBActual["humedadInterior"]

    # Humedad relativa interior
    data = {
        "measurement": "humedadInterior",
        "time": now,
        "fields": {
            'value': humedadInterior
        }
    }
    json_payload.append(data)
    mongoColecActual.insert_one(data)
    mongoColecActual = mongoDBActual["velocidadViento"]

    # Velocidad del viento
    data = {
        "measurement": "velocidadViento",
        "time": now,
        "fields": {
            'value': velocidadViento
        }
    }
    json_payload.append(data)
    mongoColecActual.insert_one(data)
    mongoColecActual = mongoDBActual["luxExterior"]

    # Luminosidad exterior
    data = {
        "measurement": "luxExterior",
        "time": now,
        "fields": {
            'value': luxExterior
        }
    }
    json_payload.append(data)
    mongoColecActual.insert_one(data)
    mongoColecActual = mongoDBActual["lluvia"]

    # Lluvia
    if str(lluvia) == "True" :
        lluviaTexto = "Sin lluvia"
    else :
        lluviaTexto = "Con lluvia"
    data = {
        "measurement": "lluvia",
        "time": now,
        "fields": {
            'value': lluvia,
            'texto': lluviaTexto
        }
    }
    json_payload.append(data)
    mongoColecActual.insert_one(data)
    mongoColecActual = mongoDBActual["alturaEstorDormitorio"]

    # Altura del estor del dormitorio
    data = {
        "measurement": "alturaEstorDormitorio",
        "time": now,
        "fields": {
            'value': alturaEstorDormitorio
        }
    }
    json_payload.append(data)
    conexInfluxDB.write_points(json_payload)
    mongoColecActual.insert_one(data)

    # PARTE 3: EXPORTACION DE DATOS EN TXT

    now = datetime.now()
    fecha = now.strftime('%d-%m-%Y')
    hora = now.strftime('%H:%M')
    # Debemos comprobar si existe el archivo para añadir la cabecera o no
    fileObj = Path('C:\\Users\\TFG3\\Desktop\\David TFG\\txtLogs\\' + fecha + '.txt')
    if(fileObj.is_file()):
        f = open('C:\\Users\\TFG3\\Desktop\\David TFG\\txtLogs\\' + fecha+'.txt', 'a')
        f.write(hora + '\t%2.1f\t%2.1f\t%3.2f\t%d\t%d\t%4.2f\t%d\n' % (tempInterior, tempExterior, CO2, humedadInterior, velocidadViento, luxExterior, not lluvia))
        f.close()
    else:
        print('No existe el fichero')
        f = open('C:\\Users\\TFG3\\Desktop\\David TFG\\txtLogs\\' + fecha+'.txt', 'w')
        f.write('HORA\tTEMPERATURA INT.\tTEMPERATURA EXT.\tCO2\tHUMEDAD INT.\tVEL. VIENTO\tLUMINOSIDAD EXT.\tLLUVIA\n')
        f.write(hora + '\t%2.1f\t%2.1f\t%3.2f\t%d\t%d\t%4.2f\t%d\n' % (tempInterior, tempExterior, CO2, humedadInterior, velocidadViento, luxExterior, not lluvia))
        f.close()
    
    print("Datos registrados correctamente: " + str(fecha) + " " + str(hora))

    sleep(5 * 60)