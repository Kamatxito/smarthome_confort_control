import boto3

def descargar_archivo(nombre_bucket, nombre_archivo, ruta_destino):
    # Crea una instancia del cliente de S3
    s3 = boto3.client('s3')
    
    try:
        # Descarga el archivo del bucket de S3a
        s3.download_file(nombre_bucket, nombre_archivo, ruta_destino)
        print("El archivo se ha descargado exitosamente.")
    except Exception as e:
        print("Error al descargar el archivo:", str(e))

# Especifica el nombre del bucket, el nombre del archivo y la ruta de destino local
nombre_bucket = 'tfg-ual-david'
nombre_archivo = 'prueba.mp3'
ruta_destino = 'prueba.mp3'

# Llama a la función para descargar el archivo
descargar_archivo(nombre_bucket, nombre_archivo, ruta_destino)