from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List
from app.auth.api_key import verify_api_key
from app.auth.rate_limit import limiter
from fastapi import Request

router = APIRouter(prefix="/embeddings", tags=["Embeddings"])

class EmbeddingRequest(BaseModel):
    texts: List[str] = Field(..., max_items=100)

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    model: str

@router.post("/", response_model=EmbeddingResponse)
@limiter.limit("20/minute")
async def create_embeddings(
    request: Request,
    data: EmbeddingRequest,
    api_key: str = Depends(verify_api_key)
):
    # TODO: Implementar generación de embeddings
    fake_embeddings = [[0.1] * 384 for _ in data.texts]
    
    return EmbeddingResponse(
        embeddings=fake_embeddings,
        model="all-MiniLM-L6-v2"
    )
