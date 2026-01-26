# app/routers/transcribe.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from app.auth.api_keys import verify_api_key
from app.auth.rate_limit import limiter
from app.models.loader import model_loader
from fastapi import Request
import tempfile
import os

router = APIRouter(prefix="/transcribe", tags=["Transcribe"])


# ======================
# Models
# ======================
class TranscribeResponse(BaseModel):
    text: str
    language: str
    duration: float
    segments: Optional[List[dict]] = None
    confidence: float = Field(..., ge=0.0, le=1.0)

class TranslateRequest(BaseModel):
    target_language: str = Field(default="en", description="Idioma de destino")


# ======================
# Endpoints
# ======================
@router.post("/", response_model=TranscribeResponse)
@limiter.limit("5/minute")
async def transcribe_audio(
    request: Request,
    file: UploadFile = File(...),
    language: Optional[str] = None,
    timestamp: bool = False,
    api_key: str = Depends(verify_api_key)
):
    """
    Transcribe audio a texto.
    
    Args:
        file: Archivo de audio (mp3, wav, m4a, etc.)
        language: Código de idioma (ej: "es", "en"). Si es None, se detecta automáticamente.
        timestamp: Si True, incluye segmentos con timestamps.
    """
    if not model_loader.whisper_model:
        raise HTTPException(status_code=503, detail="Whisper no disponible")
    
    # Validar tipo de archivo
    allowed_types = [
        "audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp4",
        "audio/x-m4a", "audio/ogg", "audio/webm", "audio/flac"
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Formato de audio no soportado. Use: {', '.join(allowed_types)}"
        )
    
    # Limitar tamaño (25MB)
    contents = await file.read(25 * 1024 * 1024)
    
    try:
        # Guardar temporalmente para Whisper
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        try:
            # Transcribir con Whisper
            result = model_loader.whisper_model.transcribe(
                tmp_path,
                language=language,
                task="transcribe",
                verbose=False,
                fp16=False  # CPU mode
            )
            
            # Preparar respuesta
            segments = []
            if timestamp and "segments" in result:
                for seg in result["segments"]:
                    segments.append({
                        "start": seg["start"],
                        "end": seg["end"],
                        "text": seg["text"],
                        "confidence": seg.get("confidence", 0.0)
                    })
            
            return TranscribeResponse(
                text=result["text"],
                language=result.get("language", "unknown"),
                duration=result.get("duration", 0.0),
                segments=segments if segments else None,
                confidence=result.get("confidence", 0.0)
            )
            
        finally:
            # Limpiar archivo temporal
            os.unlink(tmp_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transcribiendo audio: {str(e)}")


@router.post("/translate", response_model=TranscribeResponse)
@limiter.limit("3/minute")
async def translate_audio(
    request: Request,
    file: UploadFile = File(...),
    target_language: str = "en",
    api_key: str = Depends(verify_api_key)
):
    """
    Transcribe y traduce audio a otro idioma.
    """
    if not model_loader.whisper_model:
        raise HTTPException(status_code=503, detail="Whisper no disponible")
    
    contents = await file.read(25 * 1024 * 1024)
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        try:
            # Traducir con Whisper
            result = model_loader.whisper_model.transcribe(
                tmp_path,
                task="translate",
                language=target_language,
                verbose=False,
                fp16=False
            )
            
            return TranscribeResponse(
                text=result["text"],
                language=target_language,
                duration=result.get("duration", 0.0),
                confidence=result.get("confidence", 0.0)
            )
            
        finally:
            os.unlink(tmp_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error traduciendo audio: {str(e)}")


@router.get("/supported-formats")
@limiter.limit("30/minute")
async def get_supported_formats(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """
    Retorna los formatos de audio soportados.
    """
    return {
        "supported_formats": [
            "mp3", "wav", "m4a", "ogg", "webm", "flac", "mp4",
            "aac", "wma", "aiff", "opus", "amr", "alaw", "mulaw"
        ],
        "max_size_mb": 25,
        "max_duration_seconds": 300
    }


@router.get("/supported-languages")
@limiter.limit("30/minute")
async def get_supported_languages(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """
    Retorna los idiomas soportados por Whisper.
    """
    languages = [
        {"code": "es", "name": "Spanish"},
        {"code": "en", "name": "English"},
        {"code": "fr", "name": "French"},
        {"code": "de", "name": "German"},
        {"code": "it", "name": "Italian"},
        {"code": "pt", "name": "Portuguese"},
        {"code": "ru", "name": "Russian"},
        {"code": "zh", "name": "Chinese"},
        {"code": "ja", "name": "Japanese"},
        {"code": "ko", "name": "Korean"},
        {"code": "ar", "name": "Arabic"},
        {"code": "hi", "name": "Hindi"},
        # ... más idiomas
    ]
    
    return {
        "languages": languages,
        "total": len(languages),
        "auto_detect": True
    }