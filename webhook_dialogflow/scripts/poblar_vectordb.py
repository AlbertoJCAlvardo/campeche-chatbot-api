import json
import chromadb
from chromadb.config import Settings
import os
from pathlib import Path
from google.cloud import storage
from datetime import datetime

def get_storage_client():
    """Inicializa el cliente de Google Cloud Storage."""
    return storage.Client()

def download_json_from_gcs(bucket_name, prefix):
    """
    Descarga y combina todos los archivos JSON que coincidan con el prefijo.
    
    Args:
        bucket_name: Nombre del bucket de GCS
        prefix: Prefijo de los archivos a buscar
    
    Returns:
        List[Dict]: Lista de documentos JSON combinados
    """
    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    
    combined_data = []
    for blob in blobs:
        if blob.name.endswith('.json'):
            content = blob.download_as_string()
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    combined_data.extend(data)
                else:
                    combined_data.append(data)
            except json.JSONDecodeError as e:
                print(f"Error decodificando {blob.name}: {str(e)}")
    
    return combined_data

def inicializar_chromadb():
    """Inicializa las colecciones de ChromaDB."""
    # Configurar ChromaDB
    chroma_client = chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory="./data/chromadb"
    ))

    # Eliminar colecciones existentes si existen
    try:
        chroma_client.delete_collection("destinos_turisticos")
        chroma_client.delete_collection("salud_mental")
    except:
        pass

    # Crear nuevas colecciones
    collection_turismo = chroma_client.create_collection(name="destinos_turisticos")
    collection_salud = chroma_client.create_collection(name="salud_mental")

    return collection_turismo, collection_salud

def cargar_datos_turismo(collection, datos):
    """Carga los datos turísticos en ChromaDB."""
    if not datos:
        print("No se encontraron datos de turismo para cargar")
        return

    # Preparar los datos para ChromaDB
    ids = [f"destino_{i}" for i in range(len(datos))]
    documentos = [json.dumps(dato, ensure_ascii=False) for dato in datos]
    metadatos = [{"ciudad": dato["ciudad"]} for dato in datos]
    
    # Crear embeddings de los resúmenes turísticos
    textos = [dato["informacion_turistica"]["resumen_turistico"] for dato in datos]
    
    # Añadir a la colección
    collection.add(
        documents=documentos,
        metadatas=metadatos,
        ids=ids
    )
    print(f"Cargados {len(datos)} destinos turísticos")

def cargar_datos_salud_mental(collection, datos):
    """Carga los datos de salud mental en ChromaDB."""
    if not datos:
        print("No se encontraron datos de salud mental para cargar")
        return

    # Preparar los datos para ChromaDB
    ids = [f"salud_{i}" for i in range(len(datos))]
    documentos = [json.dumps(dato, ensure_ascii=False) for dato in datos]
    metadatos = [{"ciudad": dato["ciudad"]} for dato in datos]
    
    # Crear embeddings de los resúmenes de salud mental
    textos = [dato["informacion_salud_mental"]["resumen_salud_mental"] for dato in datos]
    
    # Añadir a la colección
    collection.add(
        documents=documentos,
        metadatas=metadatos,
        ids=ids
    )
    print(f"Cargados {len(datos)} registros de salud mental")

def main():
    # Configuración
    BUCKET_NAME = "chatbot-api-campeche"
    TURISMO_PREFIX = "turismo/turismo_"
    SALUD_MENTAL_PREFIX = "salud_mental/salud_mental_"
    
    print("Iniciando proceso de población de la base de datos vectorial...")
    
    # Crear directorio para ChromaDB si no existe
    os.makedirs("./data/chromadb", exist_ok=True)
    
    # Descargar datos de GCS
    print("Descargando datos de turismo...")
    datos_turismo = download_json_from_gcs(BUCKET_NAME, TURISMO_PREFIX)
    
    print("Descargando datos de salud mental...")
    datos_salud = download_json_from_gcs(BUCKET_NAME, SALUD_MENTAL_PREFIX)
    
    # Inicializar ChromaDB
    print("Inicializando ChromaDB...")
    collection_turismo, collection_salud = inicializar_chromadb()
    
    # Cargar datos
    print("Cargando datos de turismo...")
    cargar_datos_turismo(collection_turismo, datos_turismo)
    
    print("Cargando datos de salud mental...")
    cargar_datos_salud_mental(collection_salud, datos_salud)
    
    print("Base de datos vectorial poblada exitosamente.")
    print(f"Total de destinos turísticos: {len(datos_turismo)}")
    print(f"Total de registros de salud mental: {len(datos_salud)}")

if __name__ == "__main__":
    main()