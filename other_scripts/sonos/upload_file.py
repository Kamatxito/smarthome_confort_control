import logging
import boto3
from botocore.exceptions import ClientError
import os

def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

# Especifica el nombre del bucket, el nombre del archivo y la ruta de destino local
nombre_bucket = 'tfg-ual-david'
nombre_archivo = 'pruebaDavid.mp3'
ruta_destino = 'pruebaDavid.mp3'

# Llama a la función para descargar el archivo
upload_file(nombre_archivo, nombre_bucket, ruta_destino)

# La URL de descarga del fichero será: prueba_desde_python_public.mp3