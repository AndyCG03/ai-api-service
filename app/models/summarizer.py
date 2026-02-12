from transformers import pipeline
from loguru import logger
from app.config import settings


def load_summarizer_model():
    """
    Carga modelo de resumen de texto.
    """
    logger.info(f"📝 Cargando modelo de resumen: {settings.summarizer_model_name}")
    
    try:
        summarizer = pipeline(
            "summarization",
            model=settings.summarizer_model_name,
            tokenizer=settings.summarizer_model_name,
            device=-1
        )
        
        logger.success(f"✅ Modelo de resumen cargado")
        return summarizer
        
    except Exception as e:
        logger.error(f"❌ Error cargando modelo de resumen: {e}")
        
        # Fallback a modelo más pequeño
        logger.info("🔄 Intentando cargar modelo alternativo...")
        try:
            summarizer = pipeline(
                "summarization",
                model="sshleifer/distilbart-cnn-12-6",
                device=-1
            )
            logger.success("✅ Modelo de resumen alternativo cargado")
            return summarizer
        except Exception as e2:
            logger.error(f"❌ Error con modelo alternativo: {e2}")
            raise Exception(f"No se pudo cargar modelo de resumen: {e2}")