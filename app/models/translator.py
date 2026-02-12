from transformers import pipeline
from loguru import logger
from app.config import settings


def load_translator_model():
    """
    Carga modelo de traducción español-inglés.
    """
    logger.info(f"🌐 Cargando modelo de traducción: {settings.translator_model_name}")
    
    try:
        translator = pipeline(
            "translation",
            model=settings.translator_model_name,
            device=-1
        )
        
        logger.success(f"✅ Modelo de traducción cargado")
        return translator
        
    except Exception as e:
        logger.error(f"❌ Error cargando modelo de traducción: {e}")
        
        # Fallback a otro modelo
        logger.info("🔄 Intentando cargar modelo alternativo...")
        try:
            translator = pipeline(
                "translation_es_to_en",
                model="Helsinki-NLP/opus-mt-es-en",
                device=-1
            )
            logger.success("✅ Modelo de traducción alternativo cargado")
            return translator
        except Exception as e2:
            logger.error(f"❌ Error con modelo alternativo: {e2}")
            raise Exception(f"No se pudo cargar modelo de traducción: {e2}")