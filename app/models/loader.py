# app/models/loader.py
from loguru import logger
from app.config import settings

from app.models.llm import load_llm_model
from app.models.whisper import load_whisper_model
from app.models.embeddings import load_embedding_model
from app.models.ocr import load_ocr_model
# Nuevos imports
from app.models.classifier import load_classifier_model
from app.models.sentiment import load_sentiment_model
from app.models.ner import load_ner_model
from app.models.summarizer import load_summarizer_model
from app.models.translator import load_translator_model


class ModelLoader:
    """
    Gestor centralizado de carga de modelos con manejo robusto de errores.
    Cada modelo se carga independientemente, permitiendo que la aplicación
    funcione incluso si algunos modelos fallan.
    """
    
    def __init__(self):
        # Modelos existentes
        self.llm_model = None
        self.whisper_model = None
        self.embedding_model = None
        self.ocr_model = None
        
        # Nuevos modelos
        self.classifier_model = None
        self.sentiment_model = None
        self.ner_model = None
        self.summarizer_model = None
        self.translator_model = None
        
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
        except Exception as e:
            logger.error(f"❌ Error cargando LLM: {type(e).__name__}: {e}")
            logger.warning("⚠️  La aplicación funcionará sin capacidades de LLM local")

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

    def load_classifier(self):
        """Carga el modelo de clasificación de texto."""
        if not settings.enable_classifier:
            logger.warning("⚠️  Classifier deshabilitado en configuración")
            return
        
        try:
            logger.info("🏷️  Cargando modelo de Clasificación...")
            self.classifier_model = load_classifier_model()
            logger.info("✅ Modelo de Clasificación cargado exitosamente")
            self.models_loaded += 1
        except Exception as e:
            logger.error(f"❌ Error cargando Classifier: {type(e).__name__}: {e}")
            logger.warning("⚠️  La aplicación funcionará sin clasificación de texto")

    def load_sentiment(self):
        """Carga el modelo de análisis de sentimiento."""
        if not settings.enable_sentiment:
            logger.warning("😊 Sentiment deshabilitado en configuración")
            return
        
        try:
            logger.info("😊 Cargando modelo de Análisis de Sentimiento...")
            self.sentiment_model = load_sentiment_model()
            logger.info("✅ Modelo de Sentimiento cargado exitosamente")
            self.models_loaded += 1
        except Exception as e:
            logger.error(f"❌ Error cargando Sentiment: {type(e).__name__}: {e}")
            logger.warning("⚠️  La aplicación funcionará sin análisis de sentimiento")

    def load_ner(self):
        """Carga el modelo de extracción de entidades."""
        if not settings.enable_ner:
            logger.warning("🔍 NER deshabilitado en configuración")
            return
        
        try:
            logger.info("🔍 Cargando modelo de Extracción de Entidades (NER)...")
            self.ner_model = load_ner_model()
            logger.info("✅ Modelo NER cargado exitosamente")
            self.models_loaded += 1
        except Exception as e:
            logger.error(f"❌ Error cargando NER: {type(e).__name__}: {e}")
            logger.warning("⚠️  La aplicación funcionará sin extracción de entidades")

    def load_summarizer(self):
        """Carga el modelo de resumen de texto."""
        if not settings.enable_summarizer:
            logger.warning("📝 Summarizer deshabilitado en configuración")
            return
        
        try:
            logger.info("📝 Cargando modelo de Resumen de Texto...")
            self.summarizer_model = load_summarizer_model()
            logger.info("✅ Modelo de Resumen cargado exitosamente")
            self.models_loaded += 1
        except Exception as e:
            logger.error(f"❌ Error cargando Summarizer: {type(e).__name__}: {e}")
            logger.warning("⚠️  La aplicación funcionará sin resumen de texto")

    def load_translator(self):
        """Carga el modelo de traducción."""
        if not settings.enable_translator:
            logger.warning("🌐 Translator deshabilitado en configuración")
            return
        
        try:
            logger.info("🌐 Cargando modelo de Traducción...")
            self.translator_model = load_translator_model()
            logger.info("✅ Modelo de Traducción cargado exitosamente")
            self.models_loaded += 1
        except Exception as e:
            logger.error(f"❌ Error cargando Translator: {type(e).__name__}: {e}")
            logger.warning("⚠️  La aplicación funcionará sin traducción")

    def load_all(self):
        """
        Carga todos los modelos habilitados.
        Cada modelo se carga independientemente, permitiendo que la aplicación
        funcione incluso si algunos modelos fallan.
        """
        logger.info("🚀 Iniciando carga de modelos de IA...")
        
        # Contar modelos habilitados
        total_enabled = sum([
            settings.enable_llm,
            settings.enable_whisper,
            settings.enable_embeddings,
            settings.enable_ocr,
            settings.enable_classifier,
            settings.enable_sentiment,
            settings.enable_ner,
            settings.enable_summarizer,
            settings.enable_translator
        ])
        
        if total_enabled == 0:
            logger.warning("⚠️  No hay modelos habilitados en la configuración")
            return
        
        # Cargar cada modelo individualmente
        self.load_llm()
        self.load_whisper()
        self.load_embeddings()
        self.load_ocr()
        self.load_classifier()
        self.load_sentiment()
        self.load_ner()
        self.load_summarizer()
        self.load_translator()
        
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