# app/routers/generate.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from app.auth.api_keys import verify_api_key
from app.auth.rate_limit import limiter
from app.models.loader import model_loader
from fastapi import Request

router = APIRouter(prefix="/generate", tags=["Generate"])


# ======================
# Models
# ======================
class Message(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str

class GenerateRequest(BaseModel):
    messages: List[Message]
    max_tokens: int = Field(default=512, ge=1, le=2048)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    stream: bool = Field(default=False)
    stop: Optional[List[str]] = None

class GenerateResponse(BaseModel):
    text: str
    tokens_used: int
    finish_reason: str

class ChatResponse(BaseModel):
    role: str
    content: str
    tokens_used: int


# ======================
# Endpoints
# ======================
@router.post("/completion", response_model=GenerateResponse)
@limiter.limit("10/minute")
async def generate_completion(
    request: Request,
    data: GenerateRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Genera texto a partir de un prompt.
    """
    if not model_loader.llm_model:
        raise HTTPException(status_code=503, detail="LLM no disponible")
    
    try:
        # Formatear mensajes para el modelo
        prompt = ""
        for msg in data.messages:
            prompt += f"{msg.role}: {msg.content}\n"
        
        # Generar respuesta
        response = model_loader.llm_model(
            prompt,
            max_tokens=data.max_tokens,
            temperature=data.temperature,
            top_p=data.top_p,
            stop=data.stop,
            echo=False
        )
        
        text = response['choices'][0]['text']
        tokens_used = len(response['choices'][0]['text'])
        
        return GenerateResponse(
            text=text,
            tokens_used=tokens_used,
            finish_reason=response['choices'][0].get('finish_reason', 'stop')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando texto: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def generate_chat(
    request: Request,
    data: GenerateRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Genera una respuesta de chat en formato conversacional.
    """
    if not model_loader.llm_model:
        raise HTTPException(status_code=503, detail="LLM no disponible")
    
    try:
        # Crear formato de chat para el modelo
        messages = []
        for msg in data.messages:
            messages.append({"role": msg.role, "content": msg.content})
        
        # Usar create_chat_completion para modelos que lo soportan
        response = model_loader.llm_model.create_chat_completion(
            messages=messages,
            max_tokens=data.max_tokens,
            temperature=data.temperature,
            top_p=data.top_p,
            stop=data.stop,
            stream=data.stream
        )
        
        if data.stream:
            # Para streaming, necesitarías implementar Server-Sent Events
            raise HTTPException(status_code=501, detail="Streaming no implementado aún")
        
        message = response['choices'][0]['message']
        tokens_used = response.get('usage', {}).get('total_tokens', 0)
        
        return ChatResponse(
            role=message['role'],
            content=message['content'],
            tokens_used=tokens_used
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en chat: {str(e)}")


@router.get("/model-info")
@limiter.limit("30/minute")
async def get_model_info(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """
    Obtiene información sobre el modelo LLM cargado.
    """
    if not model_loader.llm_model:
        raise HTTPException(status_code=503, detail="LLM no disponible")
    
    try:
        return {
            "model_name": "Llama 3.2 1B Instruct",
            "context_size": model_loader.llm_model.n_ctx(),
            "vocab_size": model_loader.llm_model.n_vocab(),
            "architecture": "llama",
            "loaded": True,
            "parameters": "1.24B"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo info: {str(e)}")