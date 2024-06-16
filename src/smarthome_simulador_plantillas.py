# ----------- Simulador de plantillas -----------
# Este script lee las mismas plantillas que el lector, pero en lugar de registrar todos los valores de una vez en un día determinado, 
# simula ese día a tiempo real o en función de los minutos de repetición establecidos. El objetivo es ver representada la toma de decisiones
# y registrarlas en Grafana a fecha de hoy ejecutando a la vez y con la misma frecuencia el gestor de confort v1.1. Ya que solo nos sirve 
# para simular, no se registrarán datos en MongoDB, sino solo en InfluxDB.

from time import sleep
from datetime import datetime
from influxdb import InfluxDBClient
import pytz
import re

# ----------- MÉTODOS Y VARIABLES -----------

# Insetar datos en BD.
# Función para insertar los datos de una colección en InfluxDB.
def insertarDatosDB(nombreColeccion, dato, json_payload):
        data = {
            "measurement": nombreColeccion,
            "time": datetime.now(pytz.timezone('UTC')),
            "fields": {
                'value': dato
            }
        }
        json_payload.append(data)
        conexInfluxDB.write_points(json_payload)

# Imprimir valores.
# Función para imprimir los valores en pantalla y revisar los valores a tiempo real.
def imprimirValores():
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
    print("-----------")

# ----------- PROGRAMA PRINCIPAL -----------

# Se realiza la lectura de datos desde una plantilla
plantilla = open('./Plantillas/diaInvernalTemps.txt', 'r')
contenido = plantilla.readlines()

# Se configura la conexión a InfluxDB
conexInfluxDB = InfluxDBClient('localhost', 8086, 'admin', 'admin', 'smarthome')

# Se parará la ejecución una vez haya terminado de recorrer todas las líneas
for contadorLineas, linea in enumerate(contenido):

    # Se dividen los datos de la línea
    if contadorLineas == 0:
        continue
    datos = re.split(r'\t|\n', linea)

    # Se recogen los datos de la plantilla
    for dato in datos:
        # hora = datos[0]
        tempInterior = datos[1]
        tempExterior = datos[2]
        CO2 = datos[3]
        humedadInterior = datos[4]
        velocidadViento = datos[5]
        luxExterior = datos[6]
        lluvia = datos[7]
    
    imprimirValores()

    # Se prepara un payload y se cargan los datos a la BD
    json_payload = []
    insertarDatosDB("tempInterior", float(tempInterior), json_payload)
    insertarDatosDB("tempExterior", float(tempExterior), json_payload)
    insertarDatosDB("CO2", float(CO2), json_payload)
    insertarDatosDB("humedadInterior", float(humedadInterior), json_payload)
    insertarDatosDB("velocidadViento", float(velocidadViento), json_payload)
    insertarDatosDB("luxExterior", float(luxExterior), json_payload)
    insertarDatosDB("lluvia", bool(lluvia), json_payload)

    # Se establece la frecuencia (Minutos * segundos)
    sleep(1 * 60)

plantilla.close()
print("Simulación finalizada.")