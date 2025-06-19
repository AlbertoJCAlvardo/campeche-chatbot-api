from google.cloud import aiplatform
from django.conf import settings
import os
from typing import List, Dict, Any

class ServicioVertexAI:
    def __init__(self):
        if not os.path.exists(settings.GCP_SERVICE_ACCOUNT_PATH):
            raise Exception(f"No se encontró el archivo de credenciales en: {settings.GCP_SERVICE_ACCOUNT_PATH}")

        aiplatform.init(
            credentials=aiplatform.Credentials.from_service_account_file(settings.GCP_SERVICE_ACCOUNT_PATH),
            project=settings.GCP_PROJECT_ID,
            location=settings.GCP_LOCATION
        )

        self.project_id = settings.GCP_PROJECT_ID
        self.location = settings.GCP_LOCATION

    def get_text_embedding(self, text: str) -> List[float]:
        endpoint = aiplatform.Endpoint(
            endpoint_name=settings.VERTEX_AI_ENDPOINT
        )

        response = endpoint.predict([text])
        return response.predictions[0]

    def get_text_generation(self, prompt: str, **kwargs) -> str:
        parameters = {
            "temperature": kwargs.get("temperature", 0.7),
            "max_output_tokens": kwargs.get("max_tokens", 1024),
            "top_p": kwargs.get("top_p", 0.8),
            "top_k": kwargs.get("top_k", 40)
        }

        endpoint = aiplatform.Endpoint(
            endpoint_name=settings.VERTEX_AI_TEXT_ENDPOINT
        )

        response = endpoint.predict(
            instances=[{"prompt": prompt}],
            parameters=parameters
        )
        return response.predictions[0]

    def semantic_search(self, query: str, documents: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        query_embedding = self.get_text_embedding(query)

        return []
