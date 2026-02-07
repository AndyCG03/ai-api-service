# AI API Service

<p>
  <img src="assets/ai-api-service.png" alt="AI API Service" width="500"/>
</p>

API de servicios de IA con **FastAPI** optimizada para dispositivos de bajos recursos. Incluye generación de texto, transcripción de audio, embeddings, OCR y capacidades de **Business AI** (clasificación, sentimiento, NER, resumen y traducción).

---

## 🚀 Inicio Rápido

```bash
# 1. Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
copy .env.example .env
# Editar .env con tu configuración

# 4. Crear primera clave de administrador
python scripts/init_admin.py

# 5. Ejecutar la API
python app/main.py
# o con uvicorn
uvicorn app.main:app --reload
```

**Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)

**Autenticación:**
Agregar header `X-API-Key: tu_api_key_aqui`.

---

## 📡 Endpoints Principales

### Generación de Texto

`POST /generate/chat`
Ejemplo con curl:

```bash
curl -X POST "http://localhost:8000/generate/chat" \
  -H "X-API-Key: TU_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hola"}]}'
```

### Transcripción de Audio

`POST /transcribe/`

```bash
curl -X POST "http://localhost:8000/transcribe/" \
  -H "X-API-Key: TU_API_KEY" \
  -F "file=@audio.mp3"
```

### Embeddings

`POST /embeddings/`

```bash
curl -X POST "http://localhost:8000/embeddings/" \
  -H "X-API-Key: TU_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"texts":["Texto de ejemplo"]}'
```

### OCR

`POST /ocr/recognize`

```bash
curl -X POST "http://localhost:8000/ocr/recognize" \
  -H "X-API-Key: TU_API_KEY" \
  -F "image=@documento.jpg"
```

---

## 🏢 Business AI Endpoints

Todos requieren `X-API-Key`.

| Endpoint                          | Método | Descripción                                                                |
| --------------------------------- | ------ | -------------------------------------------------------------------------- |
| `/business/classify`              | POST   | Clasificación de texto en categorías personalizadas (multi-label opcional) |
| `/business/sentiment`             | POST   | Análisis de sentimiento y emociones                                        |
| `/business/entities`              | POST   | Extracción de entidades nombradas (NER)                                    |
| `/business/summarize`             | POST   | Resumen de texto (abstractive o extractive)                                |
| `/business/translate`             | POST   | Traducción de texto (es↔en)                                                |
| `/business/analyze/comprehensive` | POST   | Análisis completo: sentimiento + entidades + resumen                       |
| `/business/health`                | GET    | Verificación del estado de todos los servicios de Business AI              |

> Cada endpoint incluye ejemplos y parámetros en Swagger UI.

---

## 📦 Modelos Compatibles

| Tipo                                   | Modelo                                             | Ubicación / Descarga                      |
| -------------------------------------- | -------------------------------------------------- | ----------------------------------------- |
| **LLM (GGUF)**                         | Ej: `mistral-7b-instruct-v0.2.Q4_K_M.gguf`         | `data/models/llm/` (manual)               |
| **STT (Whisper, PyTorch)**             | tiny → large-v3                                    | Descarga automática                       |
| **Embeddings (Sentence Transformers)** | `all-MiniLM-L12-v2`                                | Descarga automática                       |
| **OCR (EasyOCR)**                      | Español, inglés +80 idiomas                        | Descarga automática                       |
| **Business AI**                        | Classifier, Sentiment, NER, Summarizer, Translator | Descarga automática (según configuración) |

> Modelos GGUF deben colocarse manualmente; el resto se descarga al primer uso.

---

## 🔧 Configuración

Editar `.env` para personalizar:

* **API:** versión, host, puerto
* **Modelos:** rutas y habilitación
* **Seguridad:** rate limiting, CORS
* **Rutas:** directorios de datos y logs

---

## 🔐 Administración de API Keys

Endpoint: `/admin/keys/`
Permite:

* Crear nuevas API keys con permisos específicos
* Listar / revocar / activar keys existentes
* Ver estadísticas de uso

> Guarda las API keys al crearlas; no se pueden recuperar después.

---

## 🐳 Docker

**Dockerfile resumido:**

```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc g++ git ffmpeg libsm6 libxext6 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# PyTorch CPU
RUN pip install --upgrade pip && \
    pip install torch==2.7.1+cpu torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cpu

COPY requirements-docker.txt .
RUN pip install -r requirements-docker.txt

COPY ./app /app/app
COPY ./static /app/static
RUN mkdir -p /app/data/models

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml resumido:**

```yaml
version: '3.8'
services:
  api:
    build: .
    container_name: ai_api_service
    ports:
      - "8000:8000"
    volumes:
      - ./data/models:/app/data/models
      - ./.env:/app/.env
    environment:
      - ENVIRONMENT=production
      - DEBUG=False
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          memory: 4G
```

> Permite montar modelos y `.env` para cambios sin rebuild. Se puede usar hot reload montando `./app:/app/app`.

---

## 📄 Licencia

Copyright © 2026 **Andy Clemente Gago**

Licenciado bajo **GNU GPL v3.0**

* ✅ Uso, modificación y distribución permitida
* ✅ Uso comercial permitido
* ⚠️ Trabajos derivados también deben ser **open source** bajo GPL v3

Archivo completo: [LICENSE](LICENSE)

