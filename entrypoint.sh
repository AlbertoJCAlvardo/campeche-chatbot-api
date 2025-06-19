#!/bin/bash

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Iniciando aplicación Django...${NC}"

# Función para verificar si ChromaDB está vacío
check_chromadb_empty() {
    if [ ! -f "/app/data/chromadb/chroma-collections.parquet" ] || [ ! -s "/app/data/chromadb/chroma-collections.parquet" ]; then
        return 0  # Está vacío
    else
        return 1  # No está vacío
    fi
}

# Ejecutar migraciones
echo -e "${YELLOW}📦 Ejecutando migraciones de Django...${NC}"
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Recolectar archivos estáticos
echo -e "${YELLOW}📂 Recolectando archivos estáticos...${NC}"
python manage.py collectstatic --noinput

# Verificar y poblar ChromaDB si está vacío
echo -e "${YELLOW}🔍 Verificando estado de ChromaDB...${NC}"
if check_chromadb_empty; then
    echo -e "${YELLOW}📊 ChromaDB está vacío. Poblando base de datos vectorial...${NC}"
    cd /app/scripts
    python poblar_vectordb.py
    cd /app
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Base de datos vectorial poblada exitosamente${NC}"
    else
        echo -e "${RED}❌ Error poblando la base de datos vectorial${NC}"
    fi
else
    echo -e "${GREEN}✅ ChromaDB ya contiene datos${NC}"
fi

# Verificar variables de entorno críticas
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}⚠️  WARNING: GEMINI_API_KEY no está configurada${NC}"
fi

if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo -e "${RED}⚠️  WARNING: GOOGLE_APPLICATION_CREDENTIALS no está configurada${NC}"
fi

# Iniciar la aplicación con Gunicorn
echo -e "${GREEN}🌐 Iniciando servidor web...${NC}"
exec gunicorn webhook_dialogflow.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile -