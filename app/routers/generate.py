from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from app.auth.api_key import verify_api_key
from app.auth.rate_limit import limiter
from fastapi import Request

router = APIRouter(prefix="/generate", tags=["Generate"])

class GenerateRequest(BaseModel):
    prompt: str = Field(..., max_length=2000)
    max_tokens: int = Field(default=100, ge=1, le=512)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

class GenerateResponse(BaseModel):
    text: str
    tokens_used: int

@router.post("/", response_model=GenerateResponse)
@limiter.limit("10/minute")
async def generate_text(
    request: Request,
    data: GenerateRequest,
    api_key: str = Depends(verify_api_key)
):
    # TODO: Implementar generación de texto
    return GenerateResponse(
        text=f"Respuesta generada para: {data.prompt[:50]}...",
        tokens_used=50
    )
