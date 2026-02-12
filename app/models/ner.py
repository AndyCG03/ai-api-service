from transformers import pipeline
from loguru import logger
from app.config import settings


def load_ner_model():
    """
    Carga modelo de reconocimiento de entidades nombradas (NER) en español.
    """
    logger.info(f"🔍 Cargando modelo NER: {settings.ner_model_name}")
    
    try:
        ner_pipeline = pipeline(
            "ner",
            model=settings.ner_model_name,
            tokenizer=settings.ner_model_name,
            device=-1,
            aggregation_strategy="simple"  # Agrupa tokens de la misma entidad
        )
        
        logger.success(f"✅ Modelo NER cargado")
        return ner_pipeline
        
    except Exception as e:
        logger.error(f"❌ Error cargando modelo NER: {e}")
        
        # Fallback a modelo multilingüe
        logger.info("🔄 Intentando cargar modelo multilingüe...")
        try:
            ner_pipeline = pipeline(
                "ner",
                model="Davlan/bert-base-multilingual-cased-ner-hrl",
                device=-1,
                aggregation_strategy="simple"
            )
            logger.success("✅ Modelo NER multilingüe cargado")
            return ner_pipeline
        except Exception as e2:
            logger.error(f"❌ Error con modelo alternativo: {e2}")
            raise Exception(f"No se pudo cargar modelo NER: {e2}")