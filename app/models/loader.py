# app/models/loader.py
from loguru import logger
from app.config import settings

from app.models.llm import load_llm_model
from app.models.whisper import load_whisper_model
from app.models.embeddings import load_embedding_model
from app.models.ocr import load_ocr_model


class ModelLoader:
    """
    Gestor centralizado de carga de modelos con manejo robusto de errores.
    Cada modelo se carga independientemente, permitiendo que la aplicación
    funcione incluso si algunos modelos fallan.
    """
    
    def __init__(self):
        self.llm_model = None
        self.whisper_model = None
        self.embedding_model = None
        self.ocr_model = None
        self.models_loaded = 0

    def load_llm(self):
        """Carga el modelo LLM con manejo de errores."""
        if not settings.enable_llm:
            logger.warning("⚠️  LLM deshabilitado en configuración")
            return
        
        try:
            logger.info("🔄 Cargando modelo LLM...")
            self.llm_model = load_llm_model()
            logger.info("✅ Modelo LLM cargado exitosamente")
            self.models_loaded += 1
        except FileNotFoundError as e:
            logger.error(f"❌ Archivo de modelo LLM no encontrado: {e}")
            logger.warning("⚠️  La aplicación funcionará sin capacidades de LLM local")
        except AssertionError as e:
            logger.error(f"❌ Error de validación al cargar LLM: {e}")
            logger.warning("⚠️  Posible problema: archivo corrupto o versión incompatible de llama-cpp-python")
            logger.warning("💡 Sugerencia: Verifica la integridad del archivo .gguf o actualiza llama-cpp-python")
        except Exception as e:
            logger.error(f"❌ Error inesperado cargando LLM: {type(e).__name__}: {e}")
            logger.warning("⚠️  La aplicación funcionará sin capacidades de LLM local")
            import traceback
            logger.debug(traceback.format_exc())

    def load_whisper(self):
        """Carga el modelo Whisper con manejo de errores."""
        if not settings.enable_whisper:
            logger.warning("⚠️  Whisper deshabilitado en configuración")
            return
        
        try:
            logger.info("🔄 Cargando modelo Whisper...")
            self.whisper_model = load_whisper_model()
            logger.info("✅ Modelo Whisper cargado exitosamente")
            self.models_loaded += 1
        except FileNotFoundError as e:
            logger.error(f"❌ Archivo de modelo Whisper no encontrado: {e}")
            logger.warning("⚠️  La aplicación funcionará sin capacidades de transcripción de audio")
        except Exception as e:
            logger.error(f"❌ Error cargando Whisper: {type(e).__name__}: {e}")
            logger.warning("⚠️  La aplicación funcionará sin capacidades de transcripción de audio")
            import traceback
            logger.debug(traceback.format_exc())

    def load_embeddings(self):
        """Carga el modelo de embeddings con manejo de errores."""
        if not settings.enable_embeddings:
            logger.warning("⚠️  Embeddings deshabilitados en configuración")
            return
        
        try:
            logger.info("🔄 Cargando modelo de Embeddings...")
            self.embedding_model = load_embedding_model()
            logger.info("✅ Modelo de Embeddings cargado exitosamente")
            self.models_loaded += 1
        except FileNotFoundError as e:
            logger.error(f"❌ Archivo de modelo de Embeddings no encontrado: {e}")
            logger.warning("⚠️  La aplicación funcionará sin capacidades de búsqueda semántica")
        except Exception as e:
            logger.error(f"❌ Error cargando Embeddings: {type(e).__name__}: {e}")
            logger.warning("⚠️  La aplicación funcionará sin capacidades de búsqueda semántica")
            import traceback
            logger.debug(traceback.format_exc())

    def load_ocr(self):
        """Carga el modelo OCR con manejo de errores."""
        if not settings.enable_ocr:
            logger.warning("⚠️  OCR deshabilitado en configuración")
            return
        
        try:
            logger.info("🔄 Cargando modelo OCR...")
            self.ocr_model = load_ocr_model()
            logger.info("✅ Modelo OCR cargado exitosamente")
            self.models_loaded += 1
        except FileNotFoundError as e:
            logger.error(f"❌ Archivo de modelo OCR no encontrado: {e}")
            logger.warning("⚠️  La aplicación funcionará sin capacidades de reconocimiento de texto en imágenes")
        except Exception as e:
            logger.error(f"❌ Error cargando OCR: {type(e).__name__}: {e}")
            logger.warning("⚠️  La aplicación funcionará sin capacidades de reconocimiento de texto en imágenes")
            import traceback
            logger.debug(traceback.format_exc())

    def load_all(self):
        """
        Carga todos los modelos habilitados.
        Cada modelo se carga independientemente, permitiendo que la aplicación
        funcione incluso si algunos modelos fallan.
        """
        logger.info("🚀 Iniciando carga de modelos de IA...")
        
        total_enabled = sum([
            settings.enable_llm,
            settings.enable_whisper,
            settings.enable_embeddings,
            settings.enable_ocr
        ])
        
        if total_enabled == 0:
            logger.warning("⚠️  No hay modelos habilitados en la configuración")
            return
        
        # Cargar cada modelo individualmente
        self.load_llm()
        self.load_whisper()
        self.load_embeddings()
        self.load_ocr()
        
        # Resumen final
        if self.models_loaded == 0:
            logger.warning("⚠️  No se pudo cargar ningún modelo de IA")
            logger.warning("⚠️  La aplicación funcionará con funcionalidad limitada")
        elif self.models_loaded < total_enabled:
            logger.warning(f"⚠️  Se cargaron {self.models_loaded}/{total_enabled} modelos")
            logger.info("✅ La aplicación funcionará con funcionalidad parcial")
        else:
            logger.success(f"🎉 Todos los modelos cargados exitosamente ({self.models_loaded}/{total_enabled})")


# Instancia singleton
model_loader = ModelLoader()