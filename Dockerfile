# Usar Python 3.12
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Create working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    gcc \
    g++ \
    pkg-config \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Actualizar pip y instalar setuptools PRIMERO
RUN pip install --upgrade pip setuptools>=69.0.0

# Copy requirements
COPY requirements.txt .

# Install Python dependencies (setuptools ya estará disponible)
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data/chromadb /app/static /app/staticfiles

# Set permissions
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8000

# Entrypoint command
ENTRYPOINT ["/app/entrypoint.sh"]