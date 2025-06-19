# Webhook DialogFlow - Sistema de Asistencia Turística y Salud Mental

Sistema de chatbot inteligente desarrollado con Django que proporciona información turística y servicios de salud mental para México utilizando tecnologías de IA y bases de datos vectoriales.

## Descripción

Este proyecto implementa un webhook para DialogFlow que procesa consultas sobre turismo y salud mental en México. Utiliza técnicas de RAG (Retrieval Augmented Generation) para proporcionar respuestas precisas y contextuales basadas en datos estructurados almacenados en ChromaDB.

## Funcionalidades

### Módulo de Turismo
- Información detallada sobre destinos turísticos mexicanos
- Recomendaciones de hoteles, restaurantes y actividades
- Datos sobre comida típica y lugares de interés
- Consejos prácticos para viajeros

### Módulo de Salud Mental
- Directorio de servicios de salud mental por ciudad
- Números de emergencia nacionales y locales
- Recursos de apoyo psicológico gratuitos
- Información sobre centros de atención especializados

## Arquitectura Técnica

- **Framework Backend**: Django 4.2
- **Motor de IA**: Google Gemini 2.5 Flash
- **Base de Datos Vectorial**: ChromaDB con embeddings
- **Almacenamiento**: Google Cloud Storage
- **Infraestructura**: Docker containerizado
- **Servidor de Producción**: Gunicorn

## Estructura del Proyecto

```
webhook_dialogflow/
├── agentes/                    # Aplicación principal Django
│   ├── servicios/              # Servicios de IA y procesamiento
│   │   ├── rag_turismo.py     # Sistema RAG para consultas turísticas
│   │   ├── rag_salud_mental.py # Sistema RAG para salud mental
│   │   ├── chromadb_service.py # Interfaz con base de datos vectorial
│   │   ├── gemini_service.py   # Integración con Gemini AI
│   │   └── gcs_service.py      # Servicio Google Cloud Storage
│   ├── utilidades/             # Herramientas DialogFlow
│   └── views.py                # Endpoints del webhook
├── data/chromadb/              # Base de datos vectorial local
├── scripts/                    # Scripts de inicialización
│   └── poblar_vectordb.py     # Población de datos desde GCS
├── webhook_dialogflow/         # Configuración Django
└── service_account.json        # Credenciales GCP
```

## Instalación y Despliegue

### Requisitos Previos
- Docker y Docker Compose
- Cuenta de Google Cloud Platform
- API Key de Gemini AI
- Credenciales de Service Account de GCP

### Variables de Entorno
```bash
GEMINI_API_KEY=tu_api_key_gemini
GOOGLE_APPLICATION_CREDENTIALS=/app/service_account.json
DJANGO_SETTINGS_MODULE=webhook_dialogflow.settings
```

### Despliegue con Docker

1. Clonar el repositorio
```bash
git clone <repository-url>
cd webhook_dialogflow
```

2. Configurar variables de entorno
```bash
export GEMINI_API_KEY="tu_api_key"
```

3. Construir y ejecutar
```bash
docker-compose up --build
```

4. El servicio estará disponible en `http://localhost:8000`

### Despliegue en Google Cloud Platform

1. Crear una VM en Compute Engine
2. Instalar Docker y Docker Compose
3. Transferir el proyecto y credenciales
4. Ejecutar con Docker Compose
5. Configurar firewall para puerto 8000

## Flujo de Datos

1. **Inicialización**: El script `poblar_vectordb.py` descarga datos desde Google Cloud Storage
2. **Indexación**: Los datos se procesan y almacenan en ChromaDB con embeddings
3. **Consulta**: Las peticiones llegan via webhook de DialogFlow
4. **Procesamiento**: El sistema RAG busca información relevante en ChromaDB
5. **Generación**: Gemini AI genera respuestas contextuales basadas en los datos encontrados
6. **Respuesta**: Se envía la respuesta estructurada de vuelta a DialogFlow

## API Endpoints

- `POST /webhook/` - Endpoint principal para DialogFlow
- `GET /health/` - Health check del servicio

## Configuración de ChromaDB

La base de datos vectorial se inicializa automáticamente al arrancar el contenedor si no contiene datos. El proceso incluye:

- Descarga de archivos JSON desde Google Cloud Storage
- Creación de embeddings para búsqueda semántica
- Indexación en colecciones separadas por dominio (turismo/salud mental)

## Monitoreo y Logs

El sistema incluye logging detallado para:
- Errores de inicialización
- Consultas procesadas
- Respuestas de IA generadas
- Estado de la base de datos vectorial

## Consideraciones de Seguridad

- Credenciales de GCP almacenadas como secretos
- API Keys manejadas via variables de entorno
- Logs sanitizados para evitar exposición de datos sensibles
- Validación de entrada en todos los endpoints

## Licencia

Este proyecto está desarrollado para fines académicos y de investigación.