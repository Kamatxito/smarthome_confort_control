# ----- CONSTANTES, ESTRUCTURAS Y FUNCIONES -----

import requests
from time import sleep

# Rangos específicos por variable
CO2_MED = 1000  # ppm
CO2_MAX = 2000  # ppm
TEMP_MIN = 20  # °C
TEMP_MAX = 25  # °C
HUMEDAD_MIN = 30  # %
HUMEDAD_MAX = 50  # %
VEL_VIENTO_MAX = 10  # m/s

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

# Función que realiza una petición a la API y obtiene los datos del sensor actual
def GET_datos(alias):
    parametros_GET['alias'] = alias
    resultadoPeticion = requests.get(url=api_Dir, params=parametros_GET)
    datos = resultadoPeticion.json()
    if alias not in ['3/2/10', '2/3/7']:
        datos += 0.0
    return datos

# Función que realiza una petición POST a la API y cambia el estado de los actuadores
def POST_datos(parametros):
    r = requests.post(url=api_Dir, params=parametros_POST)
    print(r.status_code)
    print(r.json())

# Función que se encarga de comprobar la altura de las ventanas
def estadoVentanas():
    valor = GET_datos('2/3/7')
    print("Altura de la ventana: " + str(valor))
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
    #TO-DO
    print("actuar")

# Función que apaga la calefacción
def apagarCalefaccion():
    #TO-DO
    print("actuar")

# Función que apaga el aire acondicionado
def apagarAireAcondicionado():
    #TO-DO
    print("actuar")

# Función que enciende el aire acondicionado
def encenderAireAcondicionado():
    #TO-DO
    print("actuar")

# Función que genera y reproduce a través del altavoz la acción a realizar
def lanzarAviso(mensaje):
    print(mensaje)


# Función que realiza el control en función de los datos recogidos y los rangos establecidos
def valorar_control(tempInterior, tempExterior, CO2, humedadInterior, velocidadViento, lluvia):
    prioridadActiva = 0

    # PRIORIDAD MÁXIMA
    if CO2 > CO2_MAX:
        lanzarAviso("Niveles de CO2 muy altos en el interior. Abriendo ventanas por seguridad.")
        abrirVentanas()
        apagarCalefaccion()
        prioridadActiva = 1

    # PRIORIDAD ALTA
    if velocidadViento > VEL_VIENTO_MAX and prioridadActiva != 1 and estadoVentanas() != 100:
        lanzarAviso("Alta velocidad del viento en el exterior. Cerrando ventanas por seguridad.")
        cerrarVentanas()
        prioridadActiva = 2
    if lluvia == 1  and prioridadActiva != 1 and estadoVentanas() != 100:
        lanzarAviso("Está lloviendo en el exterior. Cerrando ventanas por seguridad.")
        cerrarVentanas()
        prioridadActiva = 2

    # PRIORIDAD MEDIA
    if not TEMP_MIN <= tempInterior <= TEMP_MAX and prioridadActiva not in [1, 2]:
        prioridadActiva = 3
        if tempInterior < TEMP_MIN: # Hay que subir la temperatura
            if tempExterior > tempInterior and estadoVentanas() == 100: # Se puede subir de forma natural
                lanzarAviso("Temperatura interior baja. Abriendo ventanas para regularla.")
                abrirVentanas()
                apagarCalefaccion()
            else: # Hay que utilizar la calefacción
                lanzarAviso("Temperatura interior baja. Encendiendo calefacción para regularla.")
                cerrarVentanas()
                encenderCalefaccion()
        elif tempInterior > TEMP_MAX: # Hay que bajar la temperatura
            if tempExterior < tempInterior and estadoVentanas() == 100: # Se puede bajar de forma natural
                lanzarAviso("Temperatura interior alta. Abriendo ventanas para regularla.")
                abrirVentanas()
                apagarAireAcondicionado()
            else: # Hay que utilizar el aire acondicionado
                lanzarAviso("Temperatura interior alta. Encendiendo aire acondicionado para regularla.")
                cerrarVentanas()
                encenderAireAcondicionado()
    
    # PRIORIDAD BAJA
    if CO2 > CO2_MED and prioridadActiva not in [1, 2, 3] and estadoVentanas() == 100:
        lanzarAviso("Niveles de CO2 altos en el interior. Abriendo ventanas para regularlos.")
        abrirVentanas()
    if not HUMEDAD_MIN <= humedadInterior <= HUMEDAD_MAX and prioridadActiva not in [1, 2, 3] and estadoVentanas() == 100:
        lanzarAviso("Humedad no óptima en el interior. Abriendo ventanas para regularla.")
        abrirVentanas()

# ----- PROGRAMA PRINCIPAL -----

while (True):
    # Datos que se recogen de la SmartHome
    tempInterior = GET_datos('3/1/1')
    tempExterior = GET_datos('3/2/5')
    CO2 = GET_datos('3/2/1')
    humedadInterior = GET_datos('3/2/2')
    velocidadViento = GET_datos('3/2/4')
    luxExterior = GET_datos('3/2/9') # TO-DO: Plantear qué control hacer sobre la luminosidad
    lluvia = not GET_datos('3/2/10')

    # Se realiza el control en función de los datos recogidos
    valorar_control(tempInterior, tempExterior, CO2, humedadInterior, velocidadViento, lluvia)

    sleep(5 * 60)