from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel
from app.auth.api_key import verify_api_key
from app.auth.rate_limit import limiter
from fastapi import Request

router = APIRouter(prefix="/transcribe", tags=["Transcribe"])

class TranscribeResponse(BaseModel):
    text: str
    language: str
    duration: float

@router.post("/", response_model=TranscribeResponse)
@limiter.limit("5/minute")
async def transcribe_audio(
    request: Request,
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    # Validar tipo de archivo
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser audio")
    
    # Limitar tamaño (10MB)
    contents = await file.read(10 * 1024 * 1024)
    
    # TODO: Implementar transcripción
    return TranscribeResponse(
        text="Transcripción de ejemplo",
        language="es",
        duration=5.2
    )
