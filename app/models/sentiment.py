from transformers import pipeline
from loguru import logger
from app.config import settings


def load_sentiment_model():
    """
    Carga modelo de análisis de sentimiento en español.
    """
    logger.info(f"😊 Cargando analizador de sentimiento: {settings.sentiment_model_name}")
    
    try:
        sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model=settings.sentiment_model_name,
            tokenizer=settings.sentiment_model_name,
            device=-1
        )
        
        logger.success(f"✅ Analizador de sentimiento cargado")
        return sentiment_analyzer
        
    except Exception as e:
        logger.error(f"❌ Error cargando analizador de sentimiento: {e}")
        
        # Fallback a modelo multilingüe
        logger.info("🔄 Intentando cargar modelo multilingüe...")
        try:
            sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="nlptown/bert-base-multilingual-uncased-sentiment",
                device=-1
            )
            logger.success("✅ Analizador multilingüe cargado")
            return sentiment_analyzer
        except Exception as e2:
            logger.error(f"❌ Error con modelo alternativo: {e2}")
            raise Exception(f"No se pudo cargar analizador de sentimiento: {e2}")