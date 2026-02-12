import whisper
from loguru import logger
from pathlib import Path
from app.config import settings

def load_whisper_model():
    model_path = Path(settings.whisper_model_path)

    if not model_path.exists():
        raise FileNotFoundError(f"Whisper model not found: {model_path}")

    logger.info(f"🎙️ Cargando Whisper desde {model_path}")

    model = whisper.load_model(str(model_path))

    logger.success("✅ Whisper cargado correctamente")
    return model
