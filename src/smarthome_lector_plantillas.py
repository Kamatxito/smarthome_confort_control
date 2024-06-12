# En esta versión del smarthome_datos.py, en lugar de leer directamente desde los sensore, se hace una lectura 
# desde las plantillas previamente diseñadas. En las bases de datos también se guardan estos valores. El 
# objetivo es de cara a mostarlo junto al TFG, ejemplificar con tiempos y días totalmente diferentes cómo 
# funcionaría el control de los sensores y actuadores.

from time import sleep
from datetime import datetime
from influxdb import InfluxDBClient
import pytz
import pymongo
import re

# PARTE 0: MÉTODOS Y VARIABLES

# Este método se utiliza para agregar datos a las BD, tanto para mongoDB como para influxDB
def agregarDatosDB(nombreColeccion, hora, dato, json_payload):
        mongoColecActual = mongoDBActual[nombreColeccion]
        data = {
            "measurement": nombreColeccion,
            "time": "2023-05-30 "+str(hora)+":00+00:00",
            "fields": {
                'value': dato
            }
        }
        json_payload.append(data)
        mongoColecActual.insert_one(data)
        conexInfluxDB.write_points(json_payload)

def imprimirValores():
    print("Hora: " + str(hora))
    print("Temperatura interior: " + str(tempInterior))
    print("Temperatura exterior: " + str(tempExterior))
    print("CO2: " + str(CO2))
    print("Humedad interior: " + str(humedadInterior))
    print("Velocidad del viento: " + str(velocidadViento))
    print("Luz exterior: " + str(luxExterior))
    if lluvia == "0":
        print("Lluvia: no está lloviendo")
    else:
        print("Lluvia: sí está lloviendo")

# PROGRAMA PRINCIPAL

# Se realiza la lectura de datos desde una plantilla
plantilla = open('./Plantillas/diaInvernalTemps.txt', 'r')
contenido = plantilla.readlines()

# Se parará la ejecución una vez haya terminado de recorrer todas las líneas
for contadorLineas, linea in enumerate(contenido):

    # Se dividen los datos de la línea
    if contadorLineas == 0:
        continue
    datos = re.split(r'\t|\n', linea)

    # PARTE 1: RECOGIDA DE DATOS
    for dato in datos:
        hora = datos[0]
        tempInterior = datos[1]
        tempExterior = datos[2]
        CO2 = datos[3]
        humedadInterior = datos[4]
        velocidadViento = datos[5]
        luxExterior = datos[6]
        lluvia = datos[7]
    #imprimirValores()
    
    # PARTE 2: ENVIO DE DATOS A BD INFLUX Y A BD MONGO

    # Configurar conexiones...
    conexInfluxDB = InfluxDBClient('localhost', 8086, 'admin', 'admin', 'smarthome') # ... a InfluxDB
    conexMongoDB = pymongo.MongoClient("mongodb://localhost:27017/") # ... a mongoDB
    mongoDBActual = conexMongoDB["smarthome"]

    # Se prepara un payload y se cargan los datos a las BD
    json_payload = []
    agregarDatosDB("tempInterior", hora, float(tempInterior), json_payload)
    agregarDatosDB("tempExterior", hora, float(tempExterior), json_payload)
    agregarDatosDB("CO2", hora, float(CO2), json_payload)
    agregarDatosDB("humedadInterior", hora, float(humedadInterior), json_payload)
    agregarDatosDB("velocidadViento", hora, float(velocidadViento), json_payload)
    agregarDatosDB("luxExterior", hora, float(luxExterior), json_payload)
    agregarDatosDB("lluvia", hora, bool(lluvia), json_payload)

plantilla.close()
print("Datos registrados correctamente")