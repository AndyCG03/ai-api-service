# app/routers/embeddings.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List
from app.auth.api_keys import verify_api_key
from app.auth.rate_limit import limiter
from app.models.loader import model_loader
from fastapi import Request

router = APIRouter(prefix="/embeddings", tags=["Embeddings"])


# ======================
# Models
# ======================
class EmbeddingRequest(BaseModel):
    texts: List[str] = Field(..., max_items=100, description="Lista de textos a convertir")
    normalize: bool = Field(default=True, description="Normalizar embeddings a longitud 1")

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    model: str
    dimensions: int
    tokens_used: int


# ======================
# Endpoints
# ======================
@router.post("/", response_model=EmbeddingResponse)
@limiter.limit("20/minute")
async def create_embeddings(
    request: Request,
    data: EmbeddingRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Genera embeddings para una lista de textos.
    """
    if not model_loader.embedding_model:
        raise HTTPException(status_code=503, detail="Embeddings no disponible")
    
    try:
        # Generar embeddings
        embeddings = model_loader.embedding_model.encode(
            data.texts,
            normalize_embeddings=data.normalize,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        # Convertir a lista si es numpy array
        if hasattr(embeddings, 'tolist'):
            embeddings = embeddings.tolist()
        
        return EmbeddingResponse(
            embeddings=embeddings,
            model="all-MiniLM-L12-v2",
            dimensions=len(embeddings[0]) if embeddings else 0,
            tokens_used=sum(len(text.split()) for text in data.texts)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando embeddings: {str(e)}")


@router.post("/similarity")
@limiter.limit("15/minute")
async def calculate_similarity(
    request: Request,
    data: dict,
    api_key: str = Depends(verify_api_key)
):
    """
    Calcula similitud entre dos textos o embeddings.
    
    Body:
    ```json
    {
        "texts": ["texto1", "texto2"],
        "or"
        "embeddings": [[0.1, ...], [0.2, ...]]
    }
    ```
    """
    if not model_loader.embedding_model:
        raise HTTPException(status_code=503, detail="Embeddings no disponible")
    
    try:
        texts = data.get("texts")
        embeddings = data.get("embeddings")
        
        if texts and len(texts) == 2:
            # Calcular similitud entre textos
            emb1 = model_loader.embedding_model.encode(texts[0])
            emb2 = model_loader.embedding_model.encode(texts[1])
            similarity = float(emb1 @ emb2.T)  # Producto punto para cosine similarity
        elif embeddings and len(embeddings) == 2:
            # Calcular similitud entre embeddings existentes
            import numpy as np
            emb1 = np.array(embeddings[0])
            emb2 = np.array(embeddings[1])
            similarity = float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))
        else:
            raise HTTPException(status_code=400, detail="Se requieren 2 textos o 2 embeddings")
        
        return {
            "similarity": similarity,
            "similarity_percentage": round(similarity * 100, 2),
            "interpretation": "1.0 = idénticos, 0.0 = no relacionados, -1.0 = opuestos"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculando similitud: {str(e)}")


@router.get("/model-info")
@limiter.limit("30/minute")
async def get_embedding_model_info(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """
    Obtiene información sobre el modelo de embeddings.
    """
    if not model_loader.embedding_model:
        raise HTTPException(status_code=503, detail="Embeddings no disponible")
    
    try:
        dims = model_loader.embedding_model.get_sentence_embedding_dimension()
        
        return {
            "model_name": "all-MiniLM-L12-v2",
            "dimensions": dims,
            "max_sequence_length": 256,
            "loaded": True,
            "normalized": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo info: {str(e)}")