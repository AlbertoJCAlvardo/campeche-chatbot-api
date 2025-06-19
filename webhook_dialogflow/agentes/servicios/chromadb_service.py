"""
Servicio para gestionar la base de datos vectorial ChromaDB.
"""
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from django.conf import settings
import os
import json
import logging

logger = logging.getLogger(__name__)

class ServicioChromaDB:
    def __init__(self):
        """Inicializa el cliente de ChromaDB con persistencia."""
        # Asegurar que el directorio de persistencia existe
        persist_dir = os.path.join(settings.BASE_DIR, 'data', 'chromadb')
        os.makedirs(persist_dir, exist_ok=True)
        
        try:
            self.cliente = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=persist_dir
            ))
        except Exception as e:
            logger.error(f"Error inicializando ChromaDB: {str(e)}")
            raise RuntimeError("No se pudo inicializar ChromaDB")
        
    def crear_coleccion(self, nombre: str) -> Any:
        """
        Crea o obtiene una colección existente.
        
        Args:
            nombre: Nombre de la colección.
            
        Returns:
            Colección de ChromaDB.
        """
        try:
            return self.cliente.create_collection(name=nombre)
        except ValueError:
            # La colección ya existe
            return self.cliente.get_collection(name=nombre)
        except Exception as e:
            logger.error(f"Error creando/obteniendo colección {nombre}: {str(e)}")
            raise
            
    def agregar_documentos(
        self,
        nombre_coleccion: str,
        documentos: List[Dict[str, Any]]
    ) -> None:
        """
        Agrega documentos a la colección.
        
        Args:
            nombre_coleccion: Nombre de la colección.
            documentos: Lista de documentos a agregar.
        """
        try:
            coleccion = self.crear_coleccion(nombre_coleccion)
            
            # Preparar los datos para inserción
            ids = [f"doc_{i}" for i in range(len(documentos))]
            docs_json = [json.dumps(doc, ensure_ascii=False) for doc in documentos]
            
            # Extraer metadatos relevantes
            metadatos = []
            for doc in documentos:
                metadata = {}
                if nombre_coleccion == "destinos_turisticos":
                    metadata["ciudad"] = doc.get("ciudad", "")
                    metadata["tipo"] = "turismo"
                elif nombre_coleccion == "salud_mental":
                    metadata["ciudad"] = doc.get("ciudad", "")
                    metadata["tipo"] = "salud_mental"
                metadatos.append(metadata)
            
            # Agregar documentos a la colección
            coleccion.add(
                ids=ids,
                documents=docs_json,
                metadatas=metadatos
            )
            
            logger.info(f"Agregados {len(documentos)} documentos a la colección {nombre_coleccion}")
            
        except Exception as e:
            logger.error(f"Error agregando documentos a {nombre_coleccion}: {str(e)}")
            raise
        
    def query_collection(
        self,
        nombre_coleccion: str,
        query_text: str,
        n_results: int = 3,
        filtro: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca documentos en la colección basados en texto.
        
        Args:
            nombre_coleccion: Nombre de la colección.
            query_text: Texto de búsqueda.
            n_results: Número de resultados a retornar.
            filtro: Filtro opcional para la búsqueda (ej: {"ciudad": "Cancún"})
            
        Returns:
            Lista de documentos encontrados.
        """
        try:
            coleccion = self.crear_coleccion(nombre_coleccion)
            
            # Realizar la búsqueda
            resultados = coleccion.query(
                query_texts=[query_text],
                n_results=n_results,
                where=filtro if filtro else None
            )
            
            # Procesar resultados
            documentos = []
            for i, doc_str in enumerate(resultados['documents'][0]):
                try:
                    doc = json.loads(doc_str)
                    # Agregar metadatos y score
                    doc['_metadata'] = resultados['metadatas'][0][i]
                    doc['_score'] = resultados['distances'][0][i] if 'distances' in resultados else None
                    documentos.append(doc)
                except json.JSONDecodeError as e:
                    logger.warning(f"Error decodificando documento: {str(e)}")
                    continue
                    
            return documentos
            
        except Exception as e:
            logger.error(f"Error en búsqueda de {nombre_coleccion}: {str(e)}")
            return []
            
    def reset_collection(self, nombre_coleccion: str) -> None:
        """
        Elimina y recrea una colección.
        
        Args:
            nombre_coleccion: Nombre de la colección a resetear.
        """
        try:
            self.cliente.delete_collection(nombre_coleccion)
            self.crear_coleccion(nombre_coleccion)
            logger.info(f"Colección {nombre_coleccion} reseteada exitosamente")
        except Exception as e:
            logger.error(f"Error reseteando colección {nombre_coleccion}: {str(e)}")
            raise
