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

### 4. Crear primera clave de administrador
```bash
python scripts/init_admin.py
```

### 5. Ejecutar la API
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

El sistema utiliza API Keys con control de acceso granular. Incluye el header:
```
X-API-Key: tu_api_key_aqui
```

**Primer uso**: Ejecuta `scripts/init_admin.py` para crear tu primera clave de administrador.

## 📡 Endpoints Principales

### Generación de Texto
```bash
curl -X POST "http://localhost:8000/generate/chat" \
  -H "X-API-Key: TU_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hola"}]}'
```

### Transcripción de Audio
```bash
curl -X POST "http://localhost:8000/transcribe/" \
  -H "X-API-Key: TU_API_KEY" \
  -F "file=@audio.mp3"
```

### Embeddings
```bash
curl -X POST "http://localhost:8000/embeddings/" \
  -H "X-API-Key: TU_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"texts":["Texto de ejemplo"]}'
```

### OCR (Reconocimiento de Texto)
```bash
curl -X POST "http://localhost:8000/ocr/recognize" \
  -H "X-API-Key: TU_API_KEY" \
  -F "image=@documento.jpg"
```

## 📦 Modelos Compatibles

### LLM: GGUF (llama.cpp)
- Formatos: .gguf
- Ubicación: `data/models/llm/`
- Ejemplo: `mistral-7b-instruct-v0.2.Q4_K_M.gguf`

### STT: Whisper (PyTorch)
- Se descarga automáticamente
- Tamaños: tiny, base, small, medium, large-v3

### Embeddings: Sentence Transformers
- Se descarga automáticamente
- Ejemplo: `all-MiniLM-L12-v2`

### OCR: EasyOCR
- Se descarga automáticamente
- Idiomas: español, inglés, +80 idiomas

## 🔧 Configuración

Edita `.env` para personalizar:
- **API**: Versión, host, puerto
- **Modelos**: Qué cargar y rutas
- **Seguridad**: Rate limiting, CORS
- **Rutas**: Directorios de datos y logs

## 📦 Gestión de Modelos

Coloca modelos GGUF en `data/models/llm/` o déjalos descargarse automáticamente. Los modelos de Whisper, Embeddings y OCR se descargan automáticamente en la primera ejecución.

## 🔐 Administración de API Keys

Usa el endpoint `/admin/keys/` con una clave de administrador para:
- Crear nuevas API keys con permisos específicos
- Listar/revocar/activar keys existentes
- Ver estadísticas de uso

**Importante**: Guarda las API keys al crearlas, no podrás verlas nuevamente.