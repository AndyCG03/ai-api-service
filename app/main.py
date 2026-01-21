import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.config import settings
from app.auth.rate_limit import limiter
from app.routers import generate, transcribe, embeddings
from app.models.loader import model_loader
from loguru import logger

# 1. Creamos la app desactivando las URLs por defecto de la documentación
app = FastAPI(
    title="AI API Service",
    description="API de servicios de IA con modelos optimizados",
    version=settings.api_version,
    docs_url=None,      # Desactiva Swagger online
    redoc_url=None,     # Desactiva ReDoc online
    openapi_url="/openapi.json"
)

# --- Configuración de Archivos Estáticos (Swagger Offline) ---
# Asegúrate de tener la carpeta 'static/swagger-ui' con los .js y .css
STATIC_DIR = Path("static")
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    logger.info("✅ Archivos estáticos de Swagger montados")

# --- Rate limiting & Middleware ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://tu-dominio.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# --- Rutas para Documentación Offline ---
@app.get("/docs", include_in_schema=False, response_class=HTMLResponse)
async def custom_swagger_ui():
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
    <link type="text/css" rel="stylesheet" href="/static/swagger-ui/swagger-ui.css">
    <link rel="shortcut icon" href="/static/swagger-ui/favicon-32x32.png">
    <title>{app.title} - Swagger UI</title>
    </head>
    <body>
    <div id="swagger-ui"></div>
    <script src="/static/swagger-ui/swagger-ui-bundle.js"></script>
    <script src="/static/swagger-ui/swagger-ui-standalone-preset.js"></script>
    <script>
    window.onload = function() {{
        window.ui = SwaggerUIBundle({{
            url: '/openapi.json',
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
            layout: "StandaloneLayout",
            validatorUrl: null
        }});
    }};
    </script>
    </body>
    </html>
    """)

# --- Eventos y Routers ---
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Iniciando API...")
    try:
        model_loader.load_all() # Carga tus modelos locales de EasyOCR
        logger.info("✅ Modelos cargados")
    except Exception as e:
        logger.error(f"❌ Error cargando modelos: {e}")
    logger.info("✅ API lista y Swagger disponible en /docs")

app.include_router(generate.router)
app.include_router(transcribe.router)
app.include_router(embeddings.router)

@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "AI API Service",
        "version": settings.api_version,
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.debug)