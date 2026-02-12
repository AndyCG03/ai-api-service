from sentence_transformers import SentenceTransformer
from loguru import logger
from pathlib import Path
from app.config import settings

# app/models/embeddings.py
def load_embedding_model():
    model_path = Path(settings.embedding_model_path)
    
    if not model_path.exists():
        raise FileNotFoundError(f"Embedding model not found: {model_path}")
    
    logger.info(f"🧠 Cargando embeddings desde {model_path}")
    
    try:
        # Intenta cargar como ruta local
        model = SentenceTransformer(str(model_path))
        logger.success("✅ Embeddings cargados desde ruta local")
        return model
    except Exception as e:
        logger.warning(f"⚠️  Falló carga local: {e}")
        
        # Intenta cargar por nombre (descargará si no existe)
        try:
            logger.info("🔄 Intentando cargar 'all-MiniLM-L12-v2' por nombre...")
            model = SentenceTransformer('all-MiniLM-L12-v2')
            # Guarda para futuras ejecuciones
            model.save(str(model_path))
            logger.success("✅ Embeddings descargados y guardados localmente")
            return model
        except Exception as e2:
            logger.error(f"❌ Error cargando embeddings: {e2}")
            raise