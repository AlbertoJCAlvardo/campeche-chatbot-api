import google.generativeai as genai
from django.conf import settings
from typing import Dict, Any, Optional, List
import json

class ServicioGemini:
    def __init__(self):
        """Inicializa el cliente de Gemini AI."""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
    def generate_response(self, 
                         prompt: str, 
                         context: Optional[Dict[str, Any]] = None,
                         history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Genera una respuesta usando Gemini.
        
        Args:
            prompt: El prompt principal para Gemini
            context: Contexto adicional del usuario/conversación
            history: Historial de la conversación si existe
        
        Returns:
            str: La respuesta generada
        """
        # Construir el prompt completo con el contexto
        full_prompt = self._build_prompt(prompt, context)
        
        # Si hay historial, usar chat
        if history:
            chat = self.model.start_chat(history=history)
            response = chat.send_message(full_prompt)
        else:
            response = self.model.generate_content(full_prompt)
            
        return response.text

    def _build_prompt(self, base_prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Construye el prompt completo basado en el contexto.
        
        Args:
            base_prompt: El prompt base
            context: Contexto adicional
            
        Returns:
            str: Prompt completo formateado
        """
        if not context:
            return base_prompt
            
        prompt_template = """
        Sistema: Eres un asistente gubernamental amigable y profesional del estado de Campeche.
        Tu objetivo es proporcionar información clara y precisa, manteniendo un tono respetuoso y cercano.

        Contexto del Usuario:
        - Nombre: {nombre_usuario}
        - Tipo de Consulta: {tipo_consulta}
        - Información Adicional: {info_adicional}

        Historial Relevante:
        {historial}

        Consulta Actual:
        {consulta}

        Por favor, responde de manera:
        1. Profesional pero amigable
        2. Clara y concisa
        3. Específica para el contexto de Campeche
        4. Con información verificable cuando sea posible
        5. Incluyendo próximos pasos si aplica

        Respuesta:
        """
        
        # Formatear el historial si existe
        historial_str = ""
        if 'historial' in context:
            historial_str = "\n".join([f"- {h}" for h in context['historial']])
        
        return prompt_template.format(
            nombre_usuario=context.get('nombre_usuario', 'Usuario'),
            tipo_consulta=context.get('tipo_consulta', 'General'),
            info_adicional=context.get('info_adicional', 'No proporcionada'),
            historial=historial_str,
            consulta=base_prompt
        )

    def generate_response_for_intent(self, intent_name: str, parameters: Dict[str, Any]) -> str:
        """
        Genera una respuesta específica basada en el intent de Dialogflow.
        
        Args:
            intent_name: Nombre del intent de Dialogflow
            parameters: Parámetros extraídos por Dialogflow
            
        Returns:
            str: Respuesta generada
        """
        # Mapeo de intents a prompts específicos
        intent_prompts = {
            'Bienvenida': """
            Genera un saludo amigable y profesional para un ciudadano de Campeche.
            Menciona que eres un asistente del gobierno estatal y pregunta en qué puedes ayudar.
            Parámetros del usuario: {params}
            """,
            
            'Tramites': """
            Proporciona información sobre el trámite solicitado en Campeche.
            Trámite específico: {tramite}
            Incluye:
            1. Requisitos principales
            2. Horarios de atención
            3. Ubicación de oficinas
            4. Costos aproximados si aplica
            5. Tiempo estimado del trámite
            """,
            
            'Servicios': """
            Describe el servicio gubernamental solicitado en Campeche.
            Servicio: {servicio}
            Incluye:
            1. Descripción del servicio
            2. Cómo acceder al servicio
            3. Documentación necesaria
            4. Proceso general
            5. Información de contacto relevante
            """,
            
            'Default': """
            Genera una respuesta útil y profesional para la siguiente consulta
            relacionada con servicios gubernamentales en Campeche.
            Consulta: {query}
            Contexto: {context}
            """
        }
        
        # Obtener el template del prompt según el intent
        prompt_template = intent_prompts.get(intent_name, intent_prompts['Default'])
        
        # Formatear el prompt con los parámetros
        formatted_prompt = prompt_template.format(
            params=json.dumps(parameters, ensure_ascii=False),
            tramite=parameters.get('tramite', 'no especificado'),
            servicio=parameters.get('servicio', 'no especificado'),
            query=parameters.get('query', 'consulta general'),
            context=parameters.get('context', {})
        )
        
        # Generar y retornar la respuesta
        return self.generate_response(formatted_prompt, context=parameters)