from simulador_config import *
import requests
import json
from datetime import datetime
import pytz

# -----------------------------------------------------
# -------- FUNCIONES GRAFANA --------------------------
# -----------------------------------------------------

# Añade una anotación al panel correspondiente en el momento actual
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
    anotacion['time'] = int(datetime.now(pytz.timezone('UTC')).timestamp() * 1000)

    response = requests.post(f'{grafana_url}/api/annotations', headers=cabecerasGrafana, data=json.dumps(anotacion))

    if response.status_code == 200:
        print('Anotación agregada con éxito')
    else:
        print(f'Error al agregar anotación: {response.content}')

# -----------------------------------------------------
# -------- FUNCIONES DE INTERACCIÓN CON LA API --------
# -----------------------------------------------------

# Recupera el valor de un sensor o actuador
def GET_datos(alias):
    parametros_GET['alias'] = alias
    resultadoPeticion = requests.get(url=api_Dir, params=parametros_GET)
    datos = resultadoPeticion.json()
    if alias not in ['3/2/10', '2/3/7']:
        datos += 0.0
    return datos

# Modifica el valor de un actuador
def POST_datos():
    r = requests.post(url=api_Dir, params=parametros_POST)
    print(r.status_code)
    print(r.json())

# -----------------------------------------------------
# -------- FUNCIONES DE BD ----------------------------
# -----------------------------------------------------

# Inserta los datos en DB
def insertarDatosDB(nombreColeccion, dato, json_payload, conexInfluxDB):
    data = {
        "measurement": nombreColeccion,
        "time": datetime.now(pytz.timezone('UTC')),
        "fields": {
            'value': dato
        }
    }
    json_payload.append(data)
    conexInfluxDB.write_points(json_payload)

# -----------------------------------------------------
# -------- FUNCIONES DE SONOS -------------------------
# -----------------------------------------------------

# Genera y reproduce el mensaje a través del altavoz
def lanzarAviso(mensaje):
    print(mensaje)

# -----------------------------------------------------
# -------- FUNCIONES DE CONFORT -----------------------
# -----------------------------------------------------

# Recupera la altura de la ventana de referencia
def estadoVentanas():
    valor = GET_datos('2/3/7')
    #accionEnCurso = GET_datos('2/3/5')
    #print("Altura de la ventana: " + str(valor))
    return valor

# Función que abre la ventana de referencia
def abrirVentanas():
    parametros_POST['alias'] = '2/3/5'
    parametros_POST['value'] = 0
    POST_datos()

# Función que cierra la ventana de referencia
def cerrarVentanas():
    parametros_POST['alias'] = '2/3/5'
    parametros_POST['value'] = 1
    POST_datos()

# Función que enciende la calefacción
def encenderCalefaccion():
    global flag_calefaccion
    flag_calefaccion = 1
    if flag_calefaccion == 1:
        print("Encendiendo calefacción")
    else:
        print("Calefacción apagada")

# Función que apaga la calefacción
def apagarCalefaccion():
    global flag_calefaccion
    flag_calefaccion = 0
    if flag_calefaccion == 1:
        print("Calefacción encendida")
    else:
        print("Apagando calefacción")

# Función que apaga el aire acondicionado
def apagarAireAcondicionado():
    global flag_aire_acondicionado
    flag_aire_acondicionado = 0
    if flag_aire_acondicionado == 1:
        print("Aire acondicionado encendido")
    else:
        print("Apagando aire acondicionado")

# Función que enciende el aire acondicionado
def encenderAireAcondicionado():
    global flag_aire_acondicionado
    flag_aire_acondicionado = 1
    if flag_aire_acondicionado == 1:
        print("Encendiendo aire acondicionado")
    else:
        print("Aire acondicionado apagado")

# Función que realiza el control en función de los datos recogidos y los rangos establecidos
def valorar_control(tempInterior, tempExterior, CO2, humedadInterior, velocidadViento, lluvia):
    prioridadActiva = 0

    # PRIORIDAD MÁXIMA
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
        añadirAnotacionGrafana(0, "Prioridad Alta", "Lluvia", mensaje)
        print("-----------")

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
            elif flag_calefaccion == 0: # Hay que utilizar la calefacción
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
            elif flag_aire_acondicionado == 0: # Hay que utilizar el aire acondicionado
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

# -----------------------------------------------------
# -------- FUNCIONES DE SOPORTE -----------------------
# -----------------------------------------------------

# Imprime los valores por pantalla
def imprimirValores(tempInterior, tempExterior, CO2, humedadInterior, velocidadViento, luxExterior, lluvia):
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