import json
from typing import List, Dict, Any
from google.cloud import storage
from django.conf import settings
import os

class ServicioGCS:
    def __init__(self):
        """Inicializa el cliente de Google Cloud Storage."""
        if not os.path.exists(settings.GCP_SERVICE_ACCOUNT_PATH):
            raise Exception(f"No se encontró el archivo de credenciales en: {settings.GCP_SERVICE_ACCOUNT_PATH}")
        self.cliente = storage.Client.from_service_account_json(
            settings.GCP_SERVICE_ACCOUNT_PATH
        )
        self.bucket = self.cliente.get_bucket(settings.GCP_BUCKET_NAME)

    def listar_archivos(self, prefijo: str) -> List[str]:
        """
        Lista todos los archivos en el bucket con un prefijo específico.

        Args:
            prefijo: Prefijo para filtrar archivos (carpeta).

        Returns:
            Lista de nombres de archivos.
        """
        blobs = self.bucket.list_blobs(prefix=prefijo)
        return [blob.name for blob in blobs if blob.name.endswith('.json')]

    def descargar_json(self, nombre_archivo: str) -> Dict[str, Any]:
        """
        Descarga y decodifica un archivo JSON del bucket.

        Args:
            nombre_archivo: Ruta del archivo en el bucket.

        Returns:
            Contenido del archivo JSON como diccionario.
        """
        blob = self.bucket.blob(nombre_archivo)
        contenido = blob.download_as_string()
        return json.loads(contenido)

    def cargar_documentos(self, carpeta: str) -> List[Dict[str, Any]]:
        """
        Carga todos los documentos JSON de una carpeta específica.

        Args:
            carpeta: Nombre de la carpeta en el bucket.

        Returns:
            Lista de documentos cargados.
        """
        documentos = []
        archivos = self.listar_archivos(carpeta)

        for archivo in archivos:
            try:
                documento = self.descargar_json(archivo)
                documento['fuente'] = archivo
                documento['categoria'] = carpeta
                documentos.append(documento)
            except Exception as e:
                print(f"Error al cargar {archivo}: {str(e)}")

        return documentos