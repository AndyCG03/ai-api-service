# app/models/llm.py
from llama_cpp import Llama
from loguru import logger
from app.config import settings
from pathlib import Path
import sys

def load_llm_model():
    """
    Carga el modelo LLM usando llama-cpp-python.
    
    Raises:
        FileNotFoundError: Si el archivo del modelo no existe
        AssertionError: Si el modelo no se carga correctamente
        Exception: Otros errores durante la carga
    
    Returns:
        Llama: Instancia del modelo cargado
    """
    model_path = Path(settings.llm_model_path)

    # Validar que el archivo existe
    if not model_path.exists():
        raise FileNotFoundError(
            f"Archivo de modelo no encontrado: {model_path}\n"
            f"Por favor, descarga el modelo y colócalo en la ruta especificada."
        )
    
    # Validar tamaño del archivo (debe ser mayor a 100MB para un modelo GGUF válido)
    file_size = model_path.stat().st_size
    file_size_mb = file_size / (1024 * 1024)
    
    if file_size_mb < 100:
        logger.warning(f"⚠️  Archivo de modelo sospechosamente pequeño: {file_size_mb:.2f} MB")
        logger.warning("⚠️  El archivo podría estar corrupto o incompleto")

    logger.info(f"📦 Cargando LLM desde {model_path}")
    logger.info(f"📊 Tamaño del archivo: {file_size_mb:.2f} MB")
    logger.info(f"🔧 Configuración: n_ctx={settings.llm_max_tokens}, temp={settings.llm_temperature}")

    try:
        # Intentar cargar el modelo con configuración básica
        llm = Llama(
            model_path=str(model_path),
            n_ctx=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
            n_gpu_layers=0,  # CPU por defecto (cambia a -1 si tienes GPU)
            n_batch=512,  # Tamaño de batch razonable
            verbose=False  # Mostrar detalles para diagnóstico
        )
        
        # Verificar que el modelo se cargó correctamente
        vocab_size = llm.n_vocab()
        logger.info(f"✅ Modelo cargado - Vocabulario: {vocab_size} tokens")
        
        return llm
        
    except AssertionError as e:
        logger.error("❌ AssertionError al cargar el modelo")
        logger.error("💡 Causas posibles:")
        logger.error("   1. Archivo .gguf corrupto o incompleto")
        logger.error("   2. Versión incompatible de llama-cpp-python")
        logger.error("   3. Formato de modelo no soportado")
        logger.error(f"   4. Versión actual de Python: {sys.version}")
        raise
    
    except Exception as e:
        logger.error(f"❌ Error inesperado: {type(e).__name__}")
        raise