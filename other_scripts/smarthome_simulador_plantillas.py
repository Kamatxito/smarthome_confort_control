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
import requests
import json

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

# Función que realiza una petición a la API y obtiene los datos del sensor actual
def GET_datos(alias):
    parametros_GET['alias'] = alias
    resultadoPeticion = requests.get(url=api_Dir, params=parametros_GET)
    datos = resultadoPeticion.json()
    if alias not in ['3/2/10', '2/3/7', '2/3/5']:
        datos += 0.0
    return datos

# ----------- MÉTODOS Y VARIABLES DE LA PARTE DE GESTOR -----------

# Variables y estructuras necesarias
api_Dir = "http://remote:LabSmarthome21@192.168.7.210/scada-remote" # Direccion de la API
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
current_time = datetime.now(pytz.timezone('UTC'))
current_timestamp = int(current_time.timestamp() * 1000)

# Rangos específicos por variable
CO2_MED = 1000  # ppm
CO2_MAX = 2000  # ppm
TEMP_MIN = 20  # °C
TEMP_MAX = 25  # °C
HUMEDAD_MIN = 30  # %
HUMEDAD_MAX = 50  # %
VEL_VIENTO_MAX = 10  # m/s

# Variables y estructuras para las anotaciones de Grafana
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

# Función que realiza el control en función de los datos recogidos y los rangos establecidos
def valorar_control(tempInterior, tempExterior, CO2, humedadInterior, velocidadViento, lluvia):
    prioridadActiva = 0

    # PRIORIDAD MÁXIMA
    #print("Nivel de CO2: " + str(CO2) + ", altura ventana: " + str(estadoVentanas()))
    if CO2 > CO2_MAX and estadoVentanas() == 100:
        mensaje = "Niveles de CO2 muy altos en el interior. Abriendo ventanas por seguridad."
        lanzarAviso(mensaje)
        abrirVentanas()
        apagarCalefaccion()
        prioridadActiva = 1
        añadirAnotacionGrafana(14, "Prioridad Máxima", "CO2", mensaje)
        print("-----------")

    # PRIORIDAD ALTA
    if velocidadViento > VEL_VIENTO_MAX and prioridadActiva != 1 and estadoVentanas() != 100:
        mensaje = "Alta velocidad del viento en el exterior. Cerrando ventanas por seguridad."
        lanzarAviso(mensaje)
        cerrarVentanas()
        prioridadActiva = 2
        añadirAnotacionGrafana(10, "Prioridad Alta", "Vel. Viento", mensaje)
        print("-----------")
    if int(lluvia) == 1  and prioridadActiva != 1 and estadoVentanas() != 100:
        mensaje = "Está lloviendo en el exterior. Cerrando ventanas por seguridad."
        lanzarAviso(mensaje)
        cerrarVentanas()
        prioridadActiva = 2
        #añadirAnotacionGrafana(0, "Prioridad Alta", "Lluvia", mensaje)
        print("-----------")

    print("dcj228. ¿Calefacción encendida (0 = no, 1 = sí)?: " + str(FLAG_CALEFACCION))
    # PRIORIDAD MEDIA
    if not TEMP_MIN <= tempInterior <= TEMP_MAX and prioridadActiva not in [1, 2]:
        prioridadActiva = 3
        if tempInterior < TEMP_MIN: # Hay que subir la temperatura
            if tempExterior > tempInterior and estadoVentanas() == 100: # Se puede subir de forma natural
                mensaje = "Temperatura interior baja. Abriendo ventanas para regularla."
                lanzarAviso(mensaje)
                abrirVentanas()
                apagarCalefaccion()
                añadirAnotacionGrafana(2, "Prioridad Media", "Temperatura", mensaje)
                print("-----------")
            elif FLAG_CALEFACCION == 0: # Hay que utilizar la calefacción
                mensaje = "Temperatura interior baja. Encendiendo calefacción para regularla."
                lanzarAviso(mensaje)
                cerrarVentanas()
                encenderCalefaccion()
                añadirAnotacionGrafana(2, "Prioridad Media", "Temperatura", mensaje)
                print("-----------")
        elif tempInterior > TEMP_MAX: # Hay que bajar la temperatura
            if tempExterior < tempInterior and estadoVentanas() == 100: # Se puede bajar de forma natural
                print("Temperatura interior: " + str(tempInterior))
                mensaje = "Temperatura interior alta. Abriendo ventanas para regularla."
                lanzarAviso(mensaje)
                abrirVentanas()
                apagarAireAcondicionado()
                añadirAnotacionGrafana(2, "Prioridad Media", "Temperatura", mensaje)
                print("-----------")
            elif FLAG_AIRE_ACONDICIONADO == 0: # Hay que utilizar el aire acondicionado
                mensaje = "Temperatura interior alta. Encendiendo aire acondicionado para regularla."
                lanzarAviso(mensaje)
                cerrarVentanas()
                encenderAireAcondicionado()
                añadirAnotacionGrafana(2, "Prioridad Media", "Temperatura", mensaje)
                print("-----------")
    
    # PRIORIDAD BAJA
    if CO2 > CO2_MED and prioridadActiva not in [1, 2, 3] and estadoVentanas() == 100:
        mensaje = "Niveles de CO2 altos en el interior. Abriendo ventanas para regularlos."
        lanzarAviso(mensaje)
        abrirVentanas()
        añadirAnotacionGrafana(14, "Prioridad Baja", "CO2", mensaje)
        print("-----------")
    if not HUMEDAD_MIN <= humedadInterior <= HUMEDAD_MAX and prioridadActiva not in [1, 2, 3] and estadoVentanas() == 100:
        mensaje = "Humedad no óptima en el interior. Abriendo ventanas para regularla."
        lanzarAviso(mensaje)
        abrirVentanas()
        añadirAnotacionGrafana(4, "Prioridad Baja", "Humedad R.", mensaje)
        print("-----------")

# Función que registra en Grafana la acción tomada mediante una anotación.
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

# Función que genera y reproduce a través del altavoz la acción a realizar
def lanzarAviso(mensaje):
    print(mensaje)

# Función que realiza una petición POST a la API y cambia el estado de los actuadores
def POST_datos(parametros):
    r = requests.post(url=api_Dir, params=parametros_POST)
    print(r.status_code)
    print(r.json())

# Función que se encarga de comprobar la altura de las ventanas
def estadoVentanas():
    valor = GET_datos('2/3/7')
    #accionEnCurso = GET_datos('2/3/5')
    #print("Altura de la ventana: " + str(valor))
    return valor

# Función que abre las ventanas de la Smarthome
def abrirVentanas():
    parametros_POST['alias'] = '2/3/5'
    parametros_POST['value'] = 0
    POST_datos(parametros_POST)

# Función que cierra todas las ventanas de la Smarthome
def cerrarVentanas():
    parametros_POST['alias'] = '2/3/5'
    parametros_POST['value'] = 1
    POST_datos(parametros_POST)

# Función que activa la calefacción
def encenderCalefaccion():
    global FLAG_CALEFACCION
    FLAG_CALEFACCION = 1
    print("Encendiendo calefacción")

# Función que apaga la calefacción
def apagarCalefaccion():
    global FLAG_CALEFACCION
    FLAG_CALEFACCION = 0
    print("Apagando calefacción")

# Función que apaga el aire acondicionado
def apagarAireAcondicionado():
    global FLAG_AIRE_ACONDICIONADO
    FLAG_AIRE_ACONDICIONADO = 0
    print("Apagando aire acondicionado")

# Función que enciende el aire acondicionado
def encenderAireAcondicionado():
    global FLAG_AIRE_ACONDICIONADO
    FLAG_AIRE_ACONDICIONADO = 1
    print("Encendiendo aire acondicionado")

# ----------- PROGRAMA PRINCIPAL -----------

# Se realiza la lectura de datos desde una plantilla
plantilla = open('C:\\Users\\TFG3\\Desktop\\David TFG\\smarthome_confort_control\\src\\plantillas\\diaComplejo2.txt', 'r')
contenido = plantilla.readlines()

# Se configura la conexión a InfluxDB
conexInfluxDB = InfluxDBClient('localhost', 8086, 'admin', 'admin', 'smarthome')

# Se parará la ejecución una vez haya terminado de recorrer todas las líneas
for contadorLineas, linea in enumerate(contenido):

    # Flags
    # 0 - apagado
    # 1 - encendido
    global FLAG_AIRE_ACONDICIONADO 
    FLAG_AIRE_ACONDICIONADO = 0
    global FLAG_CALEFACCION
    FLAG_CALEFACCION = 0

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
    #print("Nivel de CO2: " + str(CO2) + ", Nivel de CO2 en float: " + str(estadoVentanas()))
    insertarDatosDB("CO2", float(CO2), json_payload)
    insertarDatosDB("humedadInterior", float(humedadInterior), json_payload)
    insertarDatosDB("velocidadViento", float(velocidadViento), json_payload)
    insertarDatosDB("luxExterior", float(luxExterior), json_payload)
    insertarDatosDB("lluvia", bool(lluvia), json_payload)

    # Se llama al gestor del confort con los datos actuales
    valorar_control(float(tempInterior), float(tempExterior), float(CO2), float(humedadInterior), float(velocidadViento), float(lluvia))

    # Se establece la frecuencia (Minutos * segundos)
    sleep(3 * 60)

plantilla.close()
print("Simulación finalizada.")