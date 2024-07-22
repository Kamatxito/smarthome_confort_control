# ----------- Simulador de plantillas -----------
# Este script lee las mismas plantillas que el lector, pero en lugar de registrar todos los valores de una vez en un día determinado, 
# simula ese día a tiempo real o en función de los minutos de repetición establecidos. El objetivo es ver representada la toma de decisiones
# y registrarlas en Grafana a fecha de hoy ejecutando a la vez y con la misma frecuencia el gestor de confort v1.1. Ya que solo nos sirve 
# para simular, no se registrarán datos en MongoDB, sino solo en InfluxDB.

from time import sleep
from simulador_libreria import *
from influxdb import InfluxDBClient
import re

# Se realiza la lectura de datos desde una plantilla
plantilla = open('C:\\Users\\TFG3\\Desktop\\David TFG\\smarthome_confort_control\\src\\plantillas\\diaComplejo2.txt', 'r')
contenido = plantilla.readlines()

# Se configura la conexión a InfluxDB
conexInfluxDB = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USER, INFLUXDB_PASS, INFLUXDB_DB)

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
    
    imprimirValores(tempInterior, tempExterior, CO2, humedadInterior, velocidadViento, luxExterior, lluvia)

    # Se prepara un payload y se cargan los datos a la BD
    json_payload = []
    insertarDatosDB("tempInterior", float(tempInterior), json_payload, conexInfluxDB)
    insertarDatosDB("tempExterior", float(tempExterior), json_payload, conexInfluxDB)
    insertarDatosDB("CO2", float(CO2), json_payload, conexInfluxDB)
    insertarDatosDB("humedadInterior", float(humedadInterior), json_payload, conexInfluxDB)
    insertarDatosDB("velocidadViento", float(velocidadViento), json_payload, conexInfluxDB)
    insertarDatosDB("luxExterior", float(luxExterior), json_payload, conexInfluxDB)
    insertarDatosDB("lluvia", bool(lluvia), json_payload, conexInfluxDB)

    # Se llama al gestor del confort con los datos actuales
    valorar_control(float(tempInterior), float(tempExterior), float(CO2), float(humedadInterior), float(velocidadViento), float(lluvia))

    # Se establece la frecuencia (Minutos * segundos)
    sleep(3 * 60)

plantilla.close()
print("Simulación finalizada.")