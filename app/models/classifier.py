from transformers import pipeline
from loguru import logger
from app.config import settings


def load_classifier_model():
    """
    Carga modelo de clasificación de texto.
    Zero-shot classification permite clasificar en categorías dinámicas.
    """
    logger.info(f"🏷️  Cargando clasificador: {settings.classifier_model_name}")
    
    try:
        # Zero-shot classification - no necesita entrenamiento específico
        classifier = pipeline(
            "zero-shot-classification",
            model=settings.classifier_model_name,
            device=-1  # CPU por defecto
        )
        
        logger.success(f"✅ Clasificador '{settings.classifier_model_name}' cargado")
        return classifier
        
    except Exception as e:
        logger.error(f"❌ Error cargando clasificador: {e}")
        
        # Fallback a modelo más simple
        logger.info("🔄 Intentando cargar modelo alternativo...")
        try:
            classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=-1
            )
            logger.success("✅ Clasificador alternativo cargado")
            return classifier
        except Exception as e2:
            logger.error(f"❌ Error con modelo alternativo: {e2}")
            raise Exception(f"No se pudo cargar ningún clasificador: {e2}")