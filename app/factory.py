from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from loguru import logger

from app.config import settings
from app.auth.rate_limit import limiter
from app.models.loader import model_loader
from app.routers import admin, generate, ocr, transcribe, embeddings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager para manejar el ciclo de vida de la aplicación.
    Reemplaza los eventos startup/shutdown deprecados.
    """
    # === STARTUP ===
    logger.info("🚀 Iniciando AI API Service v{}", settings.api_version)
    
    try:
        model_loader.load_all()
        
        if model_loader.models_loaded > 0:
            logger.success(f"✅ {model_loader.models_loaded} modelos de IA cargados exitosamente")
        else:
            logger.warning("⚠️  No se cargaron modelos - La API funcionará con capacidades limitadas")
            
    except Exception as e:
        logger.error(f"❌ Error crítico al cargar modelos: {e}")
        logger.warning("⚠️  La aplicación continuará sin modelos de IA")
        import traceback
        logger.debug(traceback.format_exc())
    
    logger.info("✅ AI API Service iniciado correctamente")
    
    yield  # La aplicación está corriendo aquí
    
    # === SHUTDOWN ===
    logger.info("👋 Deteniendo AI API Service")
    # Aquí puedes liberar recursos si es necesario
    logger.info("✅ Recursos liberados correctamente")


def create_app() -> FastAPI:
    """
    Factory principal para crear la aplicación FastAPI.
    
    Returns:
        FastAPI: Instancia completamente configurada de la aplicación
    """
    app = FastAPI(
        title="AI API Service",
        description="API de servicios de IA con modelos optimizados locales",
        version=settings.api_version,
        docs_url=None,
        redoc_url=None,
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    _configure_static(app)
    _configure_middlewares(app)
    _configure_rate_limiting(app)
    _configure_routes(app)

    logger.info("✅ Aplicación FastAPI creada exitosamente")
    return app


# =====================================================
# Configuration blocks
# =====================================================

def _configure_static(app: FastAPI):
    """Configura servidor de archivos estáticos para Swagger UI offline."""
    static_dir = Path("static")
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        logger.info("📄 Archivos estáticos montados en /static")
    else:
        logger.warning("⚠️  Directorio 'static' no encontrado - Swagger UI offline no disponible")


def _configure_middlewares(app: FastAPI):
    """Configura middlewares de la aplicación."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else ["https://tu-dominio.com"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    logger.info("✅ Middleware CORS configurado")


def _configure_rate_limiting(app: FastAPI):
    """Configura rate limiting con SlowAPI."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("✅ Rate limiting configurado")


def _configure_routes(app: FastAPI):
    """Registra todos los routers y endpoints básicos de la aplicación."""
    routers_loaded = 0
    
    # Registrar routers con manejo de errores individual
    routers = [
        ("admin", admin.router),
        ("generate", generate.router),
        ("transcribe", transcribe.router),
        ("embeddings", embeddings.router),
        ("ocr", ocr.router), 
    ]
    
    for name, router in routers:
        try:
            app.include_router(router)
            routers_loaded += 1
            logger.info(f"✅ Router '{name}' cargado")
        except Exception as e:
            logger.error(f"❌ Error cargando router '{name}': {e}")
    
    logger.info(f"✅ {routers_loaded}/{len(routers)} routers cargados exitosamente")

    # Endpoints básicos
    @app.get("/", include_in_schema=False)
    async def root():
        """Endpoint raíz con información básica de la API."""
        return {
            "message": "AI API Service",
            "version": settings.api_version,
            "docs": "/docs",
            "health": "/health",
            "status": "running"
        }

    @app.get("/health", include_in_schema=False)
    async def health():
        """Health check para monitoreo y verificación de modelos."""
        return {
            "status": "healthy",
            "version": settings.api_version,
            "models_loaded": model_loader.models_loaded,
            "models": {
                "llm": model_loader.llm_model is not None,
                "whisper": model_loader.whisper_model is not None,
                "embeddings": model_loader.embedding_model is not None,
                "ocr": model_loader.ocr_model is not None,
            }
        }

    @app.get("/docs", include_in_schema=False, response_class=HTMLResponse)
    async def custom_swagger_ui():
        """Swagger UI offline personalizado."""
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link rel="stylesheet" href="/static/swagger-ui/swagger-ui.css">
                <link rel="icon" href="/static/swagger-ui/favicon-32x32.png" sizes="32x32">
                <link rel="icon" href="/static/swagger-ui/favicon-16x16.png" sizes="16x16">
                <title>AI API Service {settings.api_version} - Swagger UI</title>
                <style>
                    html {{ box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }}
                    *, *:before, *:after {{ box-sizing: inherit; }}
                    body {{ margin: 0; padding: 0; background: #fafafa; }}
                </style>
            </head>
            <body>
                <div id="swagger-ui"></div>
                <script src="/static/swagger-ui/swagger-ui-bundle.js" charset="UTF-8"></script>
                <script src="/static/swagger-ui/swagger-ui-standalone-preset.js" charset="UTF-8"></script>
                <script>
                window.onload = function() {{
                    const ui = SwaggerUIBundle({{
                        url: '/openapi.json',
                        dom_id: '#swagger-ui',
                        deepLinking: true,
                        presets: [
                            SwaggerUIBundle.presets.apis,
                            SwaggerUIStandalonePreset
                        ],
                        plugins: [
                            SwaggerUIBundle.plugins.DownloadUrl
                        ],
                        layout: "StandaloneLayout",
                        validatorUrl: null
                    }});
                    window.ui = ui;
                }};
                </script>
            </body>
            </html>
            """
        )