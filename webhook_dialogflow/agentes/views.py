from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .servicios.rag_turismo import RAGTurismo
from .servicios.rag_salud_mental import RAGSaludMental

@csrf_exempt
@require_http_methods(["POST"])
def webhook_turismo(request):
    """
    Webhook para el agente de turismo.
    """
    try:
        # Parsear el body de la solicitud
        body = json.loads(request.body)
        
        # Extraer información relevante
        query_result = body.get('queryResult', {})
        query_text = query_result.get('queryText', '')
        parameters = query_result.get('parameters', {})
        
        # Obtener el destino si está en los parámetros
        destination = parameters.get('destination', None)
        
        # Inicializar el servicio RAG de turismo
        rag_turismo = RAGTurismo()
        
        # Procesar la consulta
        response_text = rag_turismo.process_query(query_text, destination)
        
        # Construir la respuesta para Dialogflow
        response = {
            "fulfillmentText": response_text,
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [response_text]
                    }
                }
            ]
        }
        
        return JsonResponse(response)
        
    except Exception as e:
        print(f"Error en webhook_turismo: {str(e)}")
        return JsonResponse({
            "fulfillmentText": "Lo siento, ocurrió un error al procesar tu consulta turística. ¿Podrías intentar de nuevo?"
        })

@csrf_exempt
@require_http_methods(["POST"])
def webhook_salud_mental(request):
    """
    Webhook para el agente de salud mental.
    """
    try:
        # Parsear el body de la solicitud
        body = json.loads(request.body)
        
        # Extraer información relevante
        query_result = body.get('queryResult', {})
        query_text = query_result.get('queryText', '')
        parameters = query_result.get('parameters', {})
        
        # Obtener la ciudad si está en los parámetros
        city = parameters.get('city', None)
        
        # Inicializar el servicio RAG de salud mental
        rag_salud_mental = RAGSaludMental()
        
        # Procesar la consulta
        response_text = rag_salud_mental.process_query(query_text, city)
        
        # Construir la respuesta para Dialogflow
        response = {
            "fulfillmentText": response_text,
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [response_text]
                    }
                }
            ]
        }
        
        return JsonResponse(response)
        
    except Exception as e:
        print(f"Error en webhook_salud_mental: {str(e)}")
        return JsonResponse({
            "fulfillmentText": "Si necesitas ayuda inmediata, por favor llama a la Línea de la Vida: 800-911-2000 (24 horas) o al 911."
        })
