import json
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from django.conf import settings
from .chromadb_service import ServicioChromaDB
import logging

logger = logging.getLogger(__name__)

class RAGSaludMental:
    def __init__(self):
        """Inicializa el servicio RAG para salud mental."""
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.chroma_db = ServicioChromaDB()
            
            # Números de emergencia nacionales (constantes)
            self.NUMEROS_EMERGENCIA = {
                "Línea de la Vida": "800-911-2000",
                "SAPTEL": "55-5259-8121",
                "Emergencias": "911",
                "Consejo Ciudadano": "55-5533-5533",
                "Cruz Roja": "065"
            }
            
        except Exception as e:
            logger.error(f"Error inicializando RAGSaludMental: {str(e)}")
            raise RuntimeError("No se pudo inicializar el servicio RAG de salud mental")
        
    def get_city_mental_health_info(self, city: str) -> Optional[Dict[str, Any]]:
        """
        Busca información sobre servicios de salud mental en una ciudad.
        
        Args:
            city: Nombre de la ciudad a buscar.
            
        Returns:
            Información de salud mental de la ciudad o None si no se encuentra.
        """
        try:
            # Buscar con filtro exacto primero
            results = self.chroma_db.query_collection(
                "salud_mental",
                city,
                n_results=1,
                filtro={"ciudad": city}
            )
            
            if not results:
                # Si no hay resultados exactos, buscar sin filtro
                results = self.chroma_db.query_collection(
                    "salud_mental",
                    city,
                    n_results=1
                )
            
            return results[0] if results else None
            
        except Exception as e:
            logger.error(f"Error buscando información de salud mental para {city}: {str(e)}")
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
            info_salud = city_data.get("informacion_salud_mental", {})
            campos = info_salud.get("campos_extraidos", {})
            resumen = info_salud.get("resumen_salud_mental", "")
            contactos = city_data.get("contactos_nacionales", [])
            
            # Construir el prompt con la información estructurada
            prompt_template = """
            Actúa como un profesional de la salud mental empático y comprensivo. Tu prioridad es la 
            seguridad y el bienestar de la persona. Usa la siguiente información verificada para 
            proporcionar ayuda y recursos.

            Ciudad: {ciudad}

            Resumen de servicios disponibles:
            {resumen}

            Recursos locales disponibles:
            - Centros de atención: {centros}
            - Servicios gratuitos: {servicios}
            - Líneas de ayuda locales: {lineas_locales}
            - Organizaciones de apoyo: {organizaciones}
            - Hospitales: {hospitales}

            Números de emergencia (SIEMPRE INCLUIR EN LA RESPUESTA):
            {numeros_emergencia}

            Consulta del usuario:
            {query}

            Instrucciones CRÍTICAS para la respuesta:
            1. SIEMPRE prioriza la seguridad del usuario
            2. SIEMPRE incluye números de emergencia relevantes
            3. Mantén un tono empático, comprensivo y esperanzador
            4. Proporciona recursos específicos de la localidad cuando estén disponibles
            5. Anima activamente a buscar ayuda profesional
            6. Si detectas riesgo, enfatiza la importancia de contactar servicios de emergencia
            7. NO minimices la situación ni des consejos genéricos
            8. Responde con estructura clara: Empatía → Recursos → Próximos pasos
            """
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
            # Formatear números de emergencia
            numeros_fmt = "\n".join([f"- {nombre}: {numero}" 
                                   for nombre, numero in self.NUMEROS_EMERGENCIA.items()])

            prompt = prompt_template.format(
                ciudad=city_data.get("ciudad", ""),
                resumen=resumen,
                centros=", ".join(campos.get("centros_locales", [])) or "Consulta el número de emergencias",
                servicios=", ".join(campos.get("servicios_gratuitos", [])) or "Disponibles a través de líneas nacionales",
                lineas_locales=", ".join(campos.get("lineas_ayuda_locales", [])) or "Ver números nacionales",
                organizaciones=", ".join(campos.get("organizaciones_apoyo", [])) or "Consulta líneas de ayuda",
                hospitales=", ".join(campos.get("hospitales_psiquiatricos", [])) or "Acude a urgencias del hospital más cercano",
                numeros_emergencia=numeros_fmt,
                query=user_query
            )

            response = self.model.generate_content(
                prompt,
                safety_settings=safety_settings,
                generation_config={
                    "temperature": 0.3,  # Más conservador para temas sensibles
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                }
            )
            
            return response.text

        except Exception as e:
            logger.error(f"Error generando respuesta de salud mental: {str(e)}")
            return (f"Si necesitas ayuda inmediata, por favor llama a:\n"
                   f"- Línea de la Vida: {self.NUMEROS_EMERGENCIA['Línea de la Vida']} (24 horas)\n"
                   f"- Emergencias: {self.NUMEROS_EMERGENCIA['Emergencias']}")

    def process_query(self, user_query: str, city: str = None) -> str:
        """
        Procesa una consulta sobre salud mental.
        
        Args:
            user_query: Consulta del usuario.
            city: Ciudad específica (opcional).
            
        Returns:
            Respuesta procesada.
        """
        try:
            # Si no se especifica ciudad, intentar extraerla de la consulta
            if not city:
                extraction_prompt = f"""
                Analiza la siguiente consulta y extrae el nombre de la ciudad mexicana mencionada.
                Si no hay ninguna mencionada explícitamente, responde "None".
                
                Consulta: {user_query}
                
                Responde ÚNICAMENTE con el nombre de la ciudad, sin texto adicional:
                """
                
                try:
                    city_response = self.model.generate_content(extraction_prompt)
                    city = city_response.text.strip()
                except Exception as e:
                    logger.error(f"Error extrayendo ciudad: {str(e)}")
                    city = "None"

            # Preparar datos nacionales base
            national_data = {
                "ciudad": "Nacional",
                "informacion_salud_mental": {
                    "campos_extraidos": {
                        "numeros_emergencia": list(self.NUMEROS_EMERGENCIA.values()),
                        "servicios_gratuitos": [
                            "Línea de la Vida - Atención 24/7",
                            "SAPTEL - Sistema de Ayuda Psicológica por Teléfono",
                            "Consejo Ciudadano - Atención psicológica gratuita"
                        ]
                    },
                    "resumen_salud_mental": (
                        "Existen servicios nacionales de ayuda disponibles 24/7 para toda la República Mexicana. "
                        "Estos servicios son gratuitos y confidenciales, atendidos por profesionales capacitados."
                    )
                },
                "contactos_nacionales": [
                    {"nombre": k, "telefono": v} for k, v in self.NUMEROS_EMERGENCIA.items()
                ]
            }

            if city.lower() == "none":
                # Usar información nacional
                return self.generate_response(user_query, national_data)

            # Obtener información local de salud mental
            city_data = self.get_city_mental_health_info(city)
            if not city_data:
                # Combinar información nacional con mensaje sobre la ciudad
                national_data["nota_ciudad"] = (
                    f"No se encontró información específica para {city}. "
                    "Te proporcionamos recursos nacionales disponibles para todo México."
                )
                return self.generate_response(user_query, national_data)

            # Generar respuesta con información local
            return self.generate_response(user_query, city_data)

        except Exception as e:
            logger.error(f"Error procesando consulta de salud mental: {str(e)}")
            emergency_msg = (f"Si necesitas ayuda inmediata, por favor llama a:\n"
                           f"- Línea de la Vida: {self.NUMEROS_EMERGENCIA['Línea de la Vida']} (24 horas)\n"
                           f"- Emergencias: {self.NUMEROS_EMERGENCIA['Emergencias']}")
            return emergency_msg
