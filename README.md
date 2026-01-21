# AI API Service

API de servicios de IA con FastAPI para dispositivos de bajos recursos.

## 🚀 Inicio Rápido

### 1. Crear entorno virtual
```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno
```bash
copy .env.example .env
# Editar .env con tu configuración
```

### 4. Ejecutar la API
```bash
python app/main.py
```

O con uvicorn:
```bash
uvicorn app.main:app --reload
```

## 📚 Documentación

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔑 Autenticación

Incluye el header `X-API-Key` en tus requests:
```
X-API-Key: demo_key_123456789
```

## 📡 Endpoints

### Generación de Texto
```bash
curl -X POST "http://localhost:8000/generate/" \
  -H "X-API-Key: demo_key_123456789" \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"Hola, ¿cómo estás?\",\"max_tokens\":100}"
```

### Transcripción de Audio
```bash
curl -X POST "http://localhost:8000/transcribe/" \
  -H "X-API-Key: demo_key_123456789" \
  -F "file=@audio.mp3"
```

### Embeddings
```bash
curl -X POST "http://localhost:8000/embeddings/" \
  -H "X-API-Key: demo_key_123456789" \
  -H "Content-Type: application/json" \
  -d "{\"texts\":[\"texto 1\",\"texto 2\"]}"
```

## 🔧 Configuración

Edita `.env` para personalizar:
- API keys
- Modelos a cargar
- Límites de rate limiting
- Configuración de servidor

## 📦 Modelos

Coloca tus modelos en `data/models/` o déjalos descargarse automáticamente.
