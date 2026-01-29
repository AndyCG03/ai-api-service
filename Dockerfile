FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# PASO 1: Instalar PyTorch CPU primero
RUN pip install --upgrade pip && \
    pip install torch==2.7.1+cpu torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cpu

# PASO 2: Copiar e instalar el resto de dependencias
COPY requirements-docker.txt .
RUN pip install -r requirements-docker.txt

# Copiar código
COPY ./app /app/app
COPY ./static /app/static

# Crear directorio para modelos
RUN mkdir -p /app/data/models

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]