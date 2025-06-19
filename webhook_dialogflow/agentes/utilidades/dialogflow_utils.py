"""
Utilidades para procesar peticiones y respuestas de Dialogflow.
"""
from typing import Dict, Any, Optional, List

def extraer_parametros_dialogflow(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrae parámetros relevantes de la petición de Dialogflow.
    
    Args:
        request_data: Datos de la petición de Dialogflow.
        
    Returns:
        Diccionario con los parámetros extraídos.
    """
    try:
        session_info = request_data.get('sessionInfo', {})
        parameters = session_info.get('parameters', {})
        
        return {
            'intent': session_info.get('matchedIntent', ''),
            'parameters': parameters,
            'query': request_data.get('text', ''),
            'language_code': session_info.get('languageCode', 'es')
        }
    except Exception as e:
        print(f"Error al extraer parámetros: {str(e)}")
        return {}

def generar_respuesta_dialogflow(
    texto: str,
    sugerencias: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Genera una respuesta en el formato esperado por Dialogflow.
    
    Args:
        texto: Texto principal de la respuesta.
        sugerencias: Lista opcional de sugerencias.
        
    Returns:
        Diccionario con la respuesta formateada.
    """
    respuesta = {
        "fulfillmentResponse": {
            "messages": [
                {
                    "text": {
                        "text": [texto]
                    }
                }
            ]
        }
    }
    
    # Agregar sugerencias si existen
    if sugerencias:
        respuesta["fulfillmentResponse"]["messages"].append({
            "payload": {
                "richContent": [
                    [
                        {
                            "type": "chips",
                            "options": [
                                {"text": sugerencia}
                                for sugerencia in sugerencias
                            ]
                        }
                    ]
                ]
            }
        })
    
    return respuesta

def generar_prompt_busqueda(parametros: Dict[str, Any], intent: str) -> str:
    """
    Genera un prompt de búsqueda basado en los parámetros e intent.
    
    Args:
        parametros: Parámetros extraídos de la petición.
        intent: Intent detectado.
        
    Returns:
        Prompt generado para la búsqueda.
    """
    prompt_base = ""
    
    if 'turismo' in intent.lower():
        ciudad = parametros.get('ciudad', '')
        tipo_lugar = parametros.get('tipo_lugar', '')
        prompt_base = f"Información turística sobre {tipo_lugar} en {ciudad}"
        
    elif 'salud_mental' in intent.lower():
        tema = parametros.get('tema', '')
        situacion = parametros.get('situacion', '')
        prompt_base = f"Información sobre {tema} en relación con {situacion}"
    
    return prompt_base