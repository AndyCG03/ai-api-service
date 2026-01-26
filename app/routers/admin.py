from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.auth.api_keys import api_key_manager, verify_admin_key
from loguru import logger

router = APIRouter(
    prefix="/admin/keys",
    tags=["Admin - API Keys Management"],
)


# ===================================================
# Modelos Pydantic para Request/Response
# ===================================================

class CreateKeyRequest(BaseModel):
    """Request para crear una nueva API key."""
    name: str = Field(..., description="Nombre descriptivo de la API key", min_length=3, max_length=100)
    description: Optional[str] = Field("", description="Descripción opcional", max_length=500)
    expires_in_days: Optional[int] = Field(None, description="Días hasta expiración (null = sin expiración)", gt=0)
    rate_limit: int = Field(60, description="Límite de requests por minuto", ge=1, le=1000)
    allowed_endpoints: Optional[List[str]] = Field(
        None, 
        description="Endpoints permitidos (null = todos). Rutas base de cada funcionalidad."
    )
    is_admin: bool = Field(False, description="¿Es una key de administrador?")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "General API Client",
                "description": "Cliente con acceso a funcionalidades base",
                "expires_in_days": 365,
                "rate_limit": 100,
                "allowed_endpoints": [
                    "/generate/chat",           # Funcionalidad base: Chat
                    "/transcribe/",            # Funcionalidad base: Transcripción
                    "/embeddings/",            # Funcionalidad base: Embeddings
                    "/ocr/recognize"           # Funcionalidad base: OCR
                ],
                "is_admin": False
            }
        }


class CreateKeyResponse(BaseModel):
    """Response con la API key generada."""
    success: bool
    message: str
    api_key: str
    key_prefix: str
    expires_at: Optional[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "API Key creada exitosamente",
                "api_key": "ai_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "key_prefix": "ai_xxxxxxxxx",
                "expires_at": "2025-12-31T23:59:59"
            }
        }


class KeyInfoResponse(BaseModel):
    """Información de una API key (sin el hash)."""
    id: int
    key_prefix: str
    name: str
    description: str
    created_at: str
    expires_at: Optional[str]
    is_active: bool
    rate_limit: int
    allowed_endpoints: str
    last_used_at: Optional[str]
    usage_count: int
    is_admin: bool


class ListKeysResponse(BaseModel):
    """Lista de API keys."""
    success: bool
    total: int
    keys: List[KeyInfoResponse]


class RevokeKeyRequest(BaseModel):
    """Request para revocar una key."""
    key_prefix: str = Field(..., description="Prefijo de la key a revocar (ej: ai_xxxxxxxxx)")


class GenericResponse(BaseModel):
    """Response genérica."""
    success: bool
    message: str


class StatsResponse(BaseModel):
    """Estadísticas de uso."""
    success: bool
    data: dict


# ===================================================
# Endpoints del Router
# ===================================================

@router.post("/create", response_model=CreateKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: CreateKeyRequest,
    admin_data: dict = Depends(verify_admin_key)
):
    """
    🔑 Crea una nueva API key.
    
    **Requiere**: API key de administrador
    
    **Importante**: La API key completa solo se mostrará una vez.
    Guárdala de forma segura.
    """
    try:
        api_key = api_key_manager.create_key(
            name=request.name,
            description=request.description,
            expires_in_days=request.expires_in_days,
            rate_limit=request.rate_limit,
            allowed_endpoints=request.allowed_endpoints,
            is_admin=request.is_admin 
        )
        
        key_prefix = api_key[:12]
        
        expires_at = None
        if request.expires_in_days:
            from datetime import datetime, timedelta
            expires_at = (datetime.now() + timedelta(days=request.expires_in_days)).isoformat()
        
        logger.info(f"✅ Admin '{admin_data['name']}' creó API Key: {key_prefix}... para '{request.name}'")
        
        return CreateKeyResponse(
            success=True,
            message="API Key creada exitosamente. Guárdala de forma segura, no podrás volver a verla.",
            api_key=api_key,
            key_prefix=key_prefix,
            expires_at=expires_at
        )
        
    except Exception as e:
        logger.error(f"Error creando API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear API key: {str(e)}"
        )


@router.get("/list", response_model=ListKeysResponse)
async def list_api_keys(
    active_only: bool = False,
    admin_data: dict = Depends(verify_admin_key)
):
    """
    📋 Lista todas las API keys registradas.
    
    **Requiere**: API key de administrador
    
    **Parámetros**:
    - `active_only`: Si es True, solo muestra keys activas
    """
    try:
        keys = api_key_manager.list_keys(active_only=active_only)
        
        keys_response = [
            KeyInfoResponse(
                id=k['id'],
                key_prefix=k['key_prefix'],
                name=k['name'],
                description=k['description'] or "",
                created_at=k['created_at'],
                expires_at=k['expires_at'],
                is_active=bool(k['is_active']),
                rate_limit=k['rate_limit'],
                allowed_endpoints=k['allowed_endpoints'],
                last_used_at=k['last_used_at'],
                usage_count=k['usage_count'],
                is_admin=bool(k['is_admin'])
            )
            for k in keys
        ]
        
        return ListKeysResponse(
            success=True,
            total=len(keys_response),
            keys=keys_response
        )
        
    except Exception as e:
        logger.error(f"Error listando API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar API keys: {str(e)}"
        )


@router.post("/revoke", response_model=GenericResponse)
async def revoke_api_key(
    request: RevokeKeyRequest,
    admin_data: dict = Depends(verify_admin_key)
):
    """
    🔒 Revoca una API key (la desactiva).
    
    **Requiere**: API key de administrador
    
    La key revocada no podrá utilizarse pero se mantiene en el historial.
    """
    try:
        success = api_key_manager.revoke_key(request.key_prefix)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key con prefijo '{request.key_prefix}' no encontrada"
            )
        
        logger.info(f"🔒 Admin '{admin_data['name']}' revocó API Key: {request.key_prefix}")
        
        return GenericResponse(
            success=True,
            message=f"API key {request.key_prefix} revocada exitosamente"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revocando API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al revocar API key: {str(e)}"
        )


@router.post("/activate", response_model=GenericResponse)
async def activate_api_key(
    request: RevokeKeyRequest,
    admin_data: dict = Depends(verify_admin_key)
):
    """
    ✅ Activa una API key previamente revocada.
    
    **Requiere**: API key de administrador
    """
    try:
        success = api_key_manager.activate_key(request.key_prefix)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key con prefijo '{request.key_prefix}' no encontrada"
            )
        
        logger.info(f"✅ Admin '{admin_data['name']}' activó API Key: {request.key_prefix}")
        
        return GenericResponse(
            success=True,
            message=f"API key {request.key_prefix} activada exitosamente"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activando API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al activar API key: {str(e)}"
        )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    key_prefix: Optional[str] = None,
    admin_data: dict = Depends(verify_admin_key)
):
    """
    📊 Obtiene estadísticas de uso.
    
    **Requiere**: API key de administrador
    
    **Parámetros**:
    - `key_prefix`: Si se especifica, muestra stats de esa key específica
    - Si no se especifica, muestra estadísticas globales
    """
    try:
        stats = api_key_manager.get_key_stats(key_prefix)
        
        if key_prefix and stats is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key con prefijo '{key_prefix}' no encontrada"
            )
        
        return StatsResponse(
            success=True,
            data=stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )


@router.get("/info/{key_prefix}", response_model=KeyInfoResponse)
async def get_key_info(
    key_prefix: str,
    admin_data: dict = Depends(verify_admin_key)
):
    """
    ℹ️ Obtiene información detallada de una API key específica.
    
    **Requiere**: API key de administrador
    """
    try:
        keys = api_key_manager.list_keys()
        key_data = next((k for k in keys if k['key_prefix'] == key_prefix), None)
        
        if not key_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key con prefijo '{key_prefix}' no encontrada"
            )
        
        return KeyInfoResponse(
            id=key_data['id'],
            key_prefix=key_data['key_prefix'],
            name=key_data['name'],
            description=key_data['description'] or "",
            created_at=key_data['created_at'],
            expires_at=key_data['expires_at'],
            is_active=bool(key_data['is_active']),
            rate_limit=key_data['rate_limit'],
            allowed_endpoints=key_data['allowed_endpoints'],
            last_used_at=key_data['last_used_at'],
            usage_count=key_data['usage_count'],
            is_admin=bool(key_data['is_admin'])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo info de API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener información: {str(e)}"
        )