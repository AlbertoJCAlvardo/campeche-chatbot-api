import json
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from django.conf import settings
from .chromadb_service import ServicioChromaDB
import logging

logger = logging.getLogger(__name__)

class RAGTurismo:
    def __init__(self):
        """Inicializa el servicio RAG para turismo."""
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.chroma_db = ServicioChromaDB()
        except Exception as e:
            logger.error(f"Error inicializando RAGTurismo: {str(e)}")
            raise RuntimeError("No se pudo inicializar el servicio RAG de turismo")
        
    def get_city_info(self, city: str) -> Optional[Dict[str, Any]]:
        """
        Busca información sobre una ciudad usando ChromaDB.
        
        Args:
            city: Nombre de la ciudad a buscar.
            
        Returns:
            Información de la ciudad o None si no se encuentra.
        """
        try:
            # Buscar con filtro exacto primero
            results = self.chroma_db.query_collection(
                "destinos_turisticos",
                city,
                n_results=1,
                filtro={"ciudad": city}
            )
            
            if not results:
                # Si no hay resultados exactos, buscar sin filtro
                results = self.chroma_db.query_collection(
                    "destinos_turisticos",
                    city,
                    n_results=1
                )
            
            return results[0] if results else None
            
        except Exception as e:
            logger.error(f"Error buscando información de {city}: {str(e)}")
            return None

    def generate_response(self, user_query: str, city_data: Dict[str, Any]) -> str:
        """
        Genera una respuesta usando RAG con Gemini.
        
        Args:
            user_query: Consulta del usuario.
            city_data: Datos de la ciudad.
            
        Returns:
            Respuesta generada.
        """
        try:
            # Extraer información relevante
            info_turistica = city_data.get("informacion_turistica", {})
            campos = info_turistica.get("campos_extraidos", {})
            resumen = info_turistica.get("resumen_turistico", "")
            
            # Construir el prompt con la información estructurada
            prompt_template = """
            Actúa como un experto guía turístico de México. Responde la pregunta del usuario
            usando la siguiente información verificada sobre el destino.

            Destino: {ciudad}

            Resumen general:
            {resumen}

            Información específica disponible:
            - Hoteles: {hoteles}
            - Actividades: {actividades}
            - Restaurantes: {restaurantes}
            - Comida típica: {comida}
            - Lugares turísticos: {lugares}
            - Consejos para viajeros: {consejos}

            Pregunta del usuario:
            {query}

            Instrucciones para la respuesta:
            1. Sé específico y usa datos concretos de la información proporcionada
            2. Mantén un tono amigable y profesional
            3. Si la información específica solicitada no está disponible, menciona alternativas del destino
            4. Organiza la respuesta de manera clara y estructurada
            5. Incluye consejos prácticos relevantes para la consulta
            6. No inventes información que no esté en los datos proporcionados
            """

            prompt = prompt_template.format(
                ciudad=city_data.get("ciudad", ""),
                resumen=resumen,
                hoteles=", ".join(campos.get("hoteles", []))[:200],
                actividades=", ".join(campos.get("actividades", []))[:200],
                restaurantes=", ".join(campos.get("restaurantes", []))[:200],
                comida=", ".join(campos.get("comida_tipica", []))[:200],
                lugares=", ".join(campos.get("lugares_turisticos", []))[:200],
                consejos=", ".join(campos.get("consejos_viajero", []))[:200],
                query=user_query
            )

            safety_settings = [
                {
                    "category": genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                    "threshold": genai.types.HarmBlockThreshold.BLOCK_NONE
                },
                {
                    "category": genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    "threshold": genai.types.HarmBlockThreshold.BLOCK_NONE
                },
                {
                    "category": genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    "threshold": genai.types.HarmBlockThreshold.BLOCK_NONE
                },
                {
                    "category": genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    "threshold": genai.types.HarmBlockThreshold.BLOCK_NONE
                }
            ]

            response = self.model.generate_content(
                prompt,
                safety_settings=safety_settings,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                }
            )
            
            return response.text

        except Exception as e:
            logger.error(f"Error generando respuesta: {str(e)}")
            return "Lo siento, hubo un error al generar la respuesta. Por favor, intenta reformular tu pregunta."

    def process_query(self, user_query: str, destination: str = None) -> str:
        """
        Procesa una consulta turística completa.
        
        Args:
            user_query: Consulta del usuario.
            destination: Destino específico (opcional).
            
        Returns:
            Respuesta procesada.
        """
        try:
            # Si no se especifica destino, intentar extraerlo de la consulta
            if not destination:
                extraction_prompt = f"""
                Analiza la siguiente consulta y extrae el nombre de la ciudad o destino turístico mexicano mencionado.
                Si no hay ninguno mencionado explícitamente, responde "None".
                
                Consulta: {user_query}
                
                Responde ÚNICAMENTE con el nombre del destino, sin texto adicional:
                """
                
                try:
                    destination_response = self.model.generate_content(extraction_prompt)
                    destination = destination_response.text.strip()
                except Exception as e:
                    logger.error(f"Error extrayendo destino: {str(e)}")
                    destination = "None"

            if destination.lower() == "none":
                return ("Por favor, especifica el destino turístico de México sobre el que "
                       "quieres información. Por ejemplo: 'Cancún', 'Ciudad de México', etc.")

            # Obtener información de la ciudad
            city_data = self.get_city_info(destination)
            if not city_data:
                return (f"Lo siento, no tengo información disponible sobre {destination}. "
                       "¿Te gustaría información sobre otro destino turístico de México?")

            # Generar respuesta
            return self.generate_response(user_query, city_data)

        except Exception as e:
            logger.error(f"Error procesando consulta turística: {str(e)}")
            return ("Lo siento, hubo un error al procesar tu consulta. "
                   "Por favor, intenta de nuevo con una pregunta más específica.")
