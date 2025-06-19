#!/bin/bash
# Deploy script completo para webhook_dialogflow
# Funciona tanto con proyecto existente como desde cero

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; exit 1; }

# Variables
PROJECT_NAME="webhook_dialogflow"
CURRENT_USER=$(whoami)
CURRENT_HOME=$(eval echo ~$CURRENT_USER)
PROJECT_ROOT="$CURRENT_HOME/$PROJECT_NAME"
DJANGO_ROOT="$PROJECT_ROOT/$PROJECT_NAME"
VENV_PATH="$PROJECT_ROOT/venv"

echo "🚀 DEPLOY WEBHOOK DIALOGFLOW CX"
echo "==============================="
echo "Usuario: $CURRENT_USER"
echo "Proyecto: $PROJECT_ROOT"
echo "Django: $DJANGO_ROOT"
echo "Venv: $VENV_PATH"
echo ""

# 1. CREAR ESTRUCTURA DE PROYECTO SI NO EXISTE
log "1. Verificando/Creando estructura del proyecto..."

if [ ! -d "$PROJECT_ROOT" ]; then
    log "Creando directorio del proyecto..."
    mkdir -p "$PROJECT_ROOT"
    cd "$PROJECT_ROOT"
    
    # Crear proyecto Django desde cero
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install Django==4.2.7
    django-admin startproject $PROJECT_NAME .
    python manage.py startapp agentes
    
    success "Proyecto Django creado desde cero"
else
    cd "$PROJECT_ROOT"
    success "Directorio del proyecto existe"
fi

# 2. CONFIGURAR ENTORNO VIRTUAL
log "2. Configurando entorno virtual..."

# Recrear venv si es necesario
if [ ! -f "$VENV_PATH/bin/activate" ]; then
    warning "Recreando entorno virtual..."
    rm -rf venv
    python3 -m venv venv
fi

source venv/bin/activate

# Instalar dependencias
log "Instalando dependencias básicas..."
pip install --upgrade pip
pip install Django==4.2.7
pip install python-dotenv==1.0.0
pip install gunicorn==21.2.0
pip install djangorestframework==3.14.0
pip install django-cors-headers==4.3.1

# Verificar gunicorn
if [ ! -f "$VENV_PATH/bin/gunicorn" ]; then
    error "Gunicorn no se instaló correctamente"
fi
success "Entorno virtual configurado"

# 3. CONFIGURAR DJANGO
log "3. Configurando Django..."

cd "$DJANGO_ROOT"

# Crear/actualizar settings.py
log "Configurando settings.py..."
cat > "$PROJECT_NAME/settings.py" << 'EOF'
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'clave-temporal-super-secreta-123456789-desarrollo')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'agentes',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'webhook_dialogflow.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'webhook_dialogflow.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    "https://dialogflow.cloud.google.com",
]

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'django.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'agentes': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
EOF

# Crear/actualizar URLs principales
log "Configurando URLs principales..."
cat > "$PROJECT_NAME/urls.py" << 'EOF'
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'ok', 'message': 'Webhook Dialogflow CX funcionando'})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('webhook/', include('agentes.urls')),
    path('health/', health_check, name='health'),
    path('', health_check, name='home'),
]
EOF

# Crear directorio agentes si no existe
mkdir -p agentes

# Crear/actualizar URLs de agentes
log "Configurando URLs de agentes..."
cat > "agentes/urls.py" << 'EOF'
from django.urls import path
from . import views

app_name = 'agentes'

urlpatterns = [
    path('turismo/', views.webhook_turismo, name='webhook_turismo'),
    path('salud_mental/', views.webhook_salud_mental, name='webhook_salud_mental'),
]
EOF

# Crear views básicas para agentes
log "Configurando views de agentes..."
cat > "agentes/views.py" << 'EOF'
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def webhook_turismo(request):
    """Webhook para el agente de turismo"""
    try:
        data = json.loads(request.body.decode('utf-8'))
        
        # Extraer información de Dialogflow
        session = data.get('sessionInfo', {}).get('session', '')
        intent = data.get('intentInfo', {}).get('displayName', '')
        text = data.get('text', '')
        
        logger.info(f"Turismo - Session: {session}, Intent: {intent}, Text: {text}")
        
        # Respuesta básica
        response = {
            "fulfillmentResponse": {
                "messages": [
                    {
                        "text": {
                            "text": ["¡Hola! Soy tu asistente de turismo. ¿En qué puedo ayudarte hoy?"]
                        }
                    }
                ]
            }
        }
        
        return JsonResponse(response)
        
    except Exception as e:
        logger.error(f"Error en webhook turismo: {str(e)}")
        return JsonResponse({
            "fulfillmentResponse": {
                "messages": [
                    {
                        "text": {
                            "text": ["Lo siento, ocurrió un error. Por favor intenta de nuevo."]
                        }
                    }
                ]
            }
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def webhook_salud_mental(request):
    """Webhook para el agente de salud mental"""
    try:
        data = json.loads(request.body.decode('utf-8'))
        
        # Extraer información de Dialogflow
        session = data.get('sessionInfo', {}).get('session', '')
        intent = data.get('intentInfo', {}).get('displayName', '')
        text = data.get('text', '')
        
        logger.info(f"Salud Mental - Session: {session}, Intent: {intent}, Text: {text}")
        
        # Respuesta básica
        response = {
            "fulfillmentResponse": {
                "messages": [
                    {
                        "text": {
                            "text": ["Hola, estoy aquí para apoyarte. ¿Cómo te sientes hoy?"]
                        }
                    }
                ]
            }
        }
        
        return JsonResponse(response)
        
    except Exception as e:
        logger.error(f"Error en webhook salud mental: {str(e)}")
        return JsonResponse({
            "fulfillmentResponse": {
                "messages": [
                    {
                        "text": {
                            "text": ["Entiendo que puedes estar pasando por un momento difícil. ¿Quieres intentar de nuevo?"]
                        }
                    }
                ]
            }
        }, status=500)
EOF

# Crear models.py y admin.py básicos
touch agentes/__init__.py
cat > "agentes/models.py" << 'EOF'
from django.db import models

# Modelos básicos para el proyecto
class ConversationLog(models.Model):
    session_id = models.CharField(max_length=255)
    intent = models.CharField(max_length=255, blank=True)
    user_text = models.TextField()
    bot_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    agent_type = models.CharField(max_length=50)  # 'turismo' o 'salud_mental'
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.agent_type} - {self.session_id} - {self.timestamp}"
EOF

cat > "agentes/admin.py" << 'EOF'
from django.contrib import admin
from .models import ConversationLog

@admin.register(ConversationLog)
class ConversationLogAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'agent_type', 'intent', 'timestamp']
    list_filter = ['agent_type', 'timestamp']
    search_fields = ['session_id', 'intent', 'user_text']
    readonly_fields = ['timestamp']
EOF

cat > "agentes/apps.py" << 'EOF'
from django.apps import AppConfig

class AgentesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'agentes'
EOF

# Crear archivo .env si no existe
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    log "Creando archivo .env..."
    cat > "$PROJECT_ROOT/.env" << 'EOF'
DJANGO_SECRET_KEY=clave-temporal-super-secreta-123456789-desarrollo
DEBUG=False
PROJECT_ID=lab-asistente-turistico
REGION=us-central1
ALLOWED_HOSTS=localhost,127.0.0.1,*.googleapis.com
EOF
fi

success "Configuración de Django completada"

# 4. MIGRACIONES Y SETUP DE DJANGO
log "4. Ejecutando migraciones y setup..."

python manage.py makemigrations agentes
python manage.py migrate --run-syncdb

# Crear superuser
log "Creando superuser admin..."
echo "from django.contrib.auth.models import User; User.objects.filter(username='admin').delete(); User.objects.create_superuser('admin', 'admin@test.com', 'admin123')" | python manage.py shell

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Test Django
python manage.py check
success "Django configurado correctamente"

# 5. TEST DE GUNICORN
log "5. Probando Gunicorn..."
gunicorn --bind 127.0.0.1:8000 --timeout 30 webhook_dialogflow.wsgi:application &
GUNICORN_PID=$!
sleep 5

# Test local
TEST_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ 2>/dev/null)
kill $GUNICORN_PID 2>/dev/null || true

if [ "$TEST_RESPONSE" = "200" ]; then
    success "Gunicorn funciona correctamente"
else
    error "Gunicorn test falló (HTTP $TEST_RESPONSE)"
fi

# 6. CONFIGURAR SUPERVISOR
log "6. Configurando Supervisor..."

sudo supervisorctl stop django_app 2>/dev/null || true

sudo tee /etc/supervisor/conf.d/django_app.conf > /dev/null << EOF
[program:django_app]
command=$VENV_PATH/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 --timeout 120 --max-requests 1000 --max-requests-jitter 100 webhook_dialogflow.wsgi:application
directory=$DJANGO_ROOT
autostart=true
autorestart=true
stderr_logfile=/var/log/django_app.err.log
stdout_logfile=/var/log/django_app.out.log
environment=DJANGO_SETTINGS_MODULE="webhook_dialogflow.settings"
user=$CURRENT_USER
stopasgroup=true
killasgroup=true
priority=999
EOF

# 7. CONFIGURAR NGINX
log "7. Configurando Nginx..."

# Obtener IP externa
EXTERNAL_IP=$(curl -s ifconfig.me 2>/dev/null || echo "localhost")

sudo tee /etc/nginx/sites-available/webhook_dialogflow > /dev/null << EOF
server {
    listen 80;
    server_name $EXTERNAL_IP _;
    
    client_max_body_size 4M;
    
    location = /favicon.ico { 
        access_log off; 
        log_not_found off; 
    }
    
    location /static/ {
        alias $DJANGO_ROOT/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
EOF

# Activar sitio
sudo ln -sf /etc/nginx/sites-available/webhook_dialogflow /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx
if ! sudo nginx -t; then
    error "Error en configuración de Nginx"
fi

success "Nginx configurado"

# 8. INICIAR SERVICIOS
log "8. Iniciando servicios..."

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start django_app
sudo systemctl reload nginx

# Esperar a que inicie
sleep 10

# 9. VERIFICACIÓN FINAL
log "9. Verificación final..."

# Estado de servicios
echo "Estado de Supervisor:"
sudo supervisorctl status django_app

echo ""
echo "Estado de Nginx:"
sudo systemctl is-active nginx && echo "✅ Nginx activo" || echo "❌ Nginx inactivo"

# Tests de conectividad
echo ""
log "Probando conectividad..."

# Test local
LOCAL_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ 2>/dev/null)
if [ "$LOCAL_TEST" = "200" ]; then
    success "Local: OK (HTTP $LOCAL_TEST)"
else
    warning "Local: FALLO (HTTP $LOCAL_TEST)"
    echo "Logs de error:"
    sudo tail -10 /var/log/django_app.err.log 2>/dev/null || echo "No hay logs"
fi

# Test externo
EXTERNAL_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://$EXTERNAL_IP/ 2>/dev/null)
if [ "$EXTERNAL_TEST" = "200" ]; then
    success "Externo: OK (HTTP $EXTERNAL_TEST)"
else
    warning "Externo: Puede fallar por firewall (HTTP $EXTERNAL_TEST)"
fi

# Test webhooks
echo ""
log "Probando webhooks..."

WEBHOOK_TURISMO=$(curl -s -X POST http://127.0.0.1:8000/webhook/turismo/ \
  -H "Content-Type: application/json" \
  -d '{"sessionInfo": {"session": "test"}, "text": "Hola"}' \
  -o /dev/null -w "%{http_code}" 2>/dev/null)

if [ "$WEBHOOK_TURISMO" = "200" ]; then
    success "Webhook Turismo: OK"
else
    warning "Webhook Turismo: FALLO (HTTP $WEBHOOK_TURISMO)"
fi

WEBHOOK_SALUD=$(curl -s -X POST http://127.0.0.1:8000/webhook/salud_mental/ \
  -H "Content-Type: application/json" \
  -d '{"sessionInfo": {"session": "test"}, "text": "Hola"}' \
  -o /dev/null -w "%{http_code}" 2>/dev/null)

if [ "$WEBHOOK_SALUD" = "200" ]; then
    success "Webhook Salud Mental: OK"
else
    warning "Webhook Salud Mental: FALLO (HTTP $WEBHOOK_SALUD)"
fi

echo ""
echo "🎉 DEPLOY COMPLETADO!"
echo "===================="
echo ""
echo "🌐 URLs disponibles:"
echo "  Principal: http://$EXTERNAL_IP/"
echo "  Health: http://$EXTERNAL_IP/health/"
echo "  Admin: http://$EXTERNAL_IP/admin/ (admin/admin123)"
echo "  Webhook Turismo: http://$EXTERNAL_IP/webhook/turismo/"
echo "  Webhook Salud Mental: http://$EXTERNAL_IP/webhook/salud_mental/"
echo ""
echo "🔧 Comandos útiles:"
echo "  Logs: sudo tail -f /var/log/django_app.out.log"
echo "  Errores: sudo tail -f /var/log/django_app.err.log"
echo "  Reiniciar: sudo supervisorctl restart django_app"
echo "  Estado: sudo supervisorctl status"
echo "  Nginx: sudo systemctl status nginx"
echo ""
echo "📋 Para Dialogflow CX, usa estas URLs:"
echo "  Webhook Turismo: http://$EXTERNAL_IP/webhook/turismo/"
echo "  Webhook Salud Mental: http://$EXTERNAL_IP/webhook/salud_mental/"

deactivate