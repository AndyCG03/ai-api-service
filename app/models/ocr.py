# app/models/ocr.py
from loguru import logger
from app.config import settings
from pathlib import Path
import easyocr
import os


def load_ocr_model():
    """
    Carga el modelo OCR de forma robusta.
    - Si hay rutas configuradas, las usa
    - Si no, EasyOCR descargará automáticamente los modelos
    """
    if not settings.enable_ocr:
        logger.warning("⚠️ OCR deshabilitado por configuración")
        return None

    logger.info("🔍 Inicializando OCR...")
    
    try:
        # Directorio para modelos OCR
        ocr_dir = settings.base_models_path / "OCR"
        ocr_dir.mkdir(exist_ok=True)
        
        logger.info(f"📁 Directorio OCR: {ocr_dir}")
        
        # Verificar si tenemos rutas configuradas
        has_config = all([
            settings.ocr_detector_path_env,
            settings.ocr_recognizer_path_env,
            settings.ocr_language_path_env
        ])
        
        if has_config:
            logger.info("📋 Usando rutas configuradas en .env")
            
            # Verificar archivos
            paths = [
                ("Detector", settings.ocr_detector_path),
                ("Recognizer", settings.ocr_recognizer_path),
                ("Language", settings.ocr_language_path),
            ]
            
            all_exist = True
            for name, path in paths:
                if path.exists():
                    logger.debug(f"✅ {name}: {path}")
                else:
                    logger.warning(f"⚠️  {name} no encontrado: {path}")
                    all_exist = False
            
            if not all_exist:
                logger.warning("⚠️  Algunos archivos OCR no existen, EasyOCR intentará descargarlos")
        
        # Configuración para EasyOCR
        lang_list = ["es", "en"]
        gpu_available = False  # Cambiar a True si tienes GPU compatible
        
        logger.info(f"🌍 Idiomas: {lang_list}")
        logger.info(f"🖥️  GPU: {'Activada' if gpu_available else 'CPU'}")
        
        # Inicializar EasyOCR
        reader = easyocr.Reader(
            lang_list=lang_list,
            gpu=gpu_available,
            model_storage_directory=str(ocr_dir),
            download_enabled=True,  # ✅ PERMITIR DESCARGA AUTOMÁTICA
            recog_network="english_g2",  # Red para inglés
            detector=True,
            recognizer=True,
            verbose=False
        )
        
        logger.success("✅ EasyOCR inicializado correctamente")
        
        # Probar que funciona
        logger.debug("🧪 Probando inicialización OCR...")
        # Nota: No procesamos imagen real, solo verificamos que se cargó
        
        return reader
        
    except Exception as e:
        logger.error(f"❌ Error inicializando OCR: {type(e).__name__}: {e}")
        logger.warning("⚠️  Deshabilitando funcionalidad OCR")
        
        # Desactivar OCR en configuración para evitar reintentos
        # (Esto es opcional, el loader ya maneja el error)
        return None