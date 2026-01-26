# app/routers/ocr.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from app.auth.api_keys import verify_api_key
from app.auth.rate_limit import limiter
from app.models.loader import model_loader
from fastapi import Request
import base64
import io
from PIL import Image
import numpy as np

router = APIRouter(prefix="/ocr", tags=["OCR"])


# ======================
# Models
# ======================
class OCRTextResult(BaseModel):
    """Resultado individual de texto detectado"""
    text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: List[List[float]]  # [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    page: Optional[int] = None


class OCRResponse(BaseModel):
    """Respuesta completa de OCR"""
    texts: List[OCRTextResult]
    image_size: Optional[dict] = None
    language: str
    processing_time: float


class OCRBatchRequest(BaseModel):
    """Para procesar múltiples imágenes en un solo request"""
    images: List[str] = Field(..., description="Lista de imágenes en base64")
    languages: Optional[List[str]] = Field(["es", "en"], description="Idiomas para reconocer")


class OCRDetectLanguagesResponse(BaseModel):
    """Respuesta de detección de idiomas"""
    detected_languages: List[str]
    confidence: List[float]


# ======================
# Endpoints
# ======================
@router.post("/recognize", response_model=OCRResponse)
@limiter.limit("10/minute")
async def recognize_text(
    request: Request,
    file: UploadFile = File(...),
    languages: Optional[str] = "es,en",
    detail: bool = True,
    api_key: str = Depends(verify_api_key)
):
    """
    Reconoce texto en una imagen.
    
    Args:
        file: Imagen en formato JPEG, PNG, etc.
        languages: Idiomas separados por coma (ej: "es,en,fr")
        detail: Si True, retorna información detallada (bounding boxes)
    """
    if not model_loader.ocr_model:
        raise HTTPException(status_code=503, detail="OCR no disponible")
    
    # Validar tipo de archivo
    allowed_types = ["image/jpeg", "image/png", "image/bmp", "image/tiff", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Formato no soportado. Use: {', '.join(allowed_types)}")
    
    # Limitar tamaño (5MB)
    contents = await file.read(5 * 1024 * 1024)
    
    # Convertir a lista de idiomas
    lang_list = [lang.strip() for lang in languages.split(",")]
    
    try:
        # Procesar con OCR
        result = model_loader.ocr_model.readtext(
            contents,
            detail=detail,
            paragraph=True,  # Agrupar en párrafos
            decoder='beamsearch',  # Mejor precisión
            beamWidth=5,
            batch_size=1,
            workers=0,
            allowlist=None,
            blocklist=None,
            contrast_ths=0.1,
            adjust_contrast=0.5,
            filter_ths=0.003,
            text_threshold=0.7,
            low_text=0.4,
            link_threshold=0.4,
            canvas_size=2560,
            mag_ratio=1.0,
            slope_ths=0.1,
            ycenter_ths=0.5,
            height_ths=0.5,
            width_ths=0.5,
            add_margin=0.1,
            x_ths=1.0,
            y_ths=0.5,
            reformat=True,
        )
        
        # Formatear respuesta
        texts = []
        if detail:
            for item in result:
                bbox, text, confidence = item
                texts.append(OCRTextResult(
                    text=text,
                    confidence=confidence,
                    bbox=bbox.tolist() if hasattr(bbox, 'tolist') else bbox
                ))
        else:
            for text in result:
                texts.append(OCRTextResult(
                    text=text,
                    confidence=1.0,
                    bbox=[[0, 0], [0, 0], [0, 0], [0, 0]]
                ))
        
        return OCRResponse(
            texts=texts,
            language=",".join(lang_list),
            processing_time=0.0  # Podrías medir el tiempo real
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando imagen: {str(e)}")


@router.post("/recognize-base64", response_model=OCRResponse)
@limiter.limit("10/minute")
async def recognize_text_base64(
    request: Request,
    data: dict,
    api_key: str = Depends(verify_api_key)
):
    """
    Reconoce texto en una imagen enviada en base64.
    
    Body:
    ```json
    {
        "image": "base64_string",
        "languages": ["es", "en"]
    }
    ```
    """
    if not model_loader.ocr_model:
        raise HTTPException(status_code=503, detail="OCR no disponible")
    
    try:
        image_b64 = data.get("image", "")
        languages = data.get("languages", ["es", "en"])
        
        if not image_b64:
            raise HTTPException(status_code=400, detail="Se requiere campo 'image' en base64")
        
        # Decodificar base64
        image_data = base64.b64decode(image_b64)
        
        # Procesar con OCR
        result = model_loader.ocr_model.readtext(image_data, detail=True)
        
        # Formatear respuesta
        texts = []
        for item in result:
            bbox, text, confidence = item
            texts.append(OCRTextResult(
                text=text,
                confidence=confidence,
                bbox=bbox.tolist() if hasattr(bbox, 'tolist') else bbox
            ))
        
        return OCRResponse(
            texts=texts,
            language=",".join(languages),
            processing_time=0.0
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando imagen: {str(e)}")


@router.post("/batch", response_model=List[OCRResponse])
@limiter.limit("5/minute")
async def recognize_batch(
    request: Request,
    data: OCRBatchRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Procesa múltiples imágenes en un solo request.
    """
    if not model_loader.ocr_model:
        raise HTTPException(status_code=503, detail="OCR no disponible")
    
    if len(data.images) > 10:
        raise HTTPException(status_code=400, detail="Máximo 10 imágenes por batch")
    
    responses = []
    
    for i, image_b64 in enumerate(data.images):
        try:
            # Decodificar base64
            image_data = base64.b64decode(image_b64)
            
            # Procesar con OCR
            result = model_loader.ocr_model.readtext(
                image_data,
                detail=True,
                paragraph=True,
                batch_size=1
            )
            
            # Formatear respuesta
            texts = []
            for item in result:
                bbox, text, confidence = item
                texts.append(OCRTextResult(
                    text=text,
                    confidence=confidence,
                    bbox=bbox.tolist() if hasattr(bbox, 'tolist') else bbox,
                    page=i
                ))
            
            responses.append(OCRResponse(
                texts=texts,
                language=",".join(data.languages),
                processing_time=0.0
            ))
            
        except Exception as e:
            responses.append(OCRResponse(
                texts=[],
                language=",".join(data.languages),
                processing_time=0.0
            ))
    
    return responses


@router.get("/detect-languages", response_model=OCRDetectLanguagesResponse)
@limiter.limit("20/minute")
async def detect_languages(
    request: Request,
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """
    Detecta los idiomas presentes en una imagen.
    """
    if not model_loader.ocr_model:
        raise HTTPException(status_code=503, detail="OCR no disponible")
    
    try:
        contents = await file.read(5 * 1024 * 1024)
        
        # Primero extraemos el texto
        result = model_loader.ocr_model.readtext(contents, detail=False)
        
        # Aquí podrías integrar un detector de idiomas
        # Por ahora retornamos los idiomas configurados
        # (EasyOCR detecta automáticamente entre los idiomas configurados)
        
        # Este es un placeholder - en producción usarías un detector real
        detected = ["es", "en"]
        confidences = [0.8, 0.7]
        
        return OCRDetectLanguagesResponse(
            detected_languages=detected,
            confidence=confidences
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detectando idiomas: {str(e)}")


@router.get("/supported-languages")
@limiter.limit("30/minute")
async def get_supported_languages(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """
    Retorna la lista de idiomas soportados por el OCR.
    """
    if not model_loader.ocr_model:
        raise HTTPException(status_code=503, detail="OCR no disponible")
    
    # EasyOCR soporta muchos idiomas
    supported_langs = [
        "es", "en", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko",
        "ar", "hi", "bn", "tr", "vi", "th", "nl", "pl", "sv", "da",
        "no", "fi", "el", "he", "id", "ms", "cs", "ro", "hu", "sk",
        "uk", "hr", "ca", "fa", "sr", "ml", "ta", "te", "kn", "mr",
        "gu", "pa", "ne", "si", "my", "km", "lo", "bo", "ti", "am",
        "af", "az", "bs", "bg", "ceb", "co", "eo", "et", "eu", "fy",
        "ga", "gd", "gl", "ha", "haw", "hmn", "ig", "is", "jw", "ka",
        "kk", "ku", "ky", "la", "lb", "lt", "lv", "mg", "mi", "mk",
        "mn", "mt", "ny", "ps", "sd", "sl", "sm", "sn", "so", "sq",
        "st", "su", "sw", "tg", "tk", "tl", "tt", "ug", "ur", "uz",
        "xh", "yi", "yo", "zu"
    ]
    
    # Idiomas actualmente cargados en el modelo
    loaded_langs = model_loader.ocr_model.lang_list
    
    return {
        "supported_languages": supported_langs,
        "currently_loaded": loaded_langs,
        "total_supported": len(supported_langs)
    }


@router.get("/health")
async def ocr_health():
    """
    Health check específico para OCR.
    """
    return {
        "status": "active" if model_loader.ocr_model else "inactive",
        "model_loaded": model_loader.ocr_model is not None,
        "languages_loaded": model_loader.ocr_model.lang_list if model_loader.ocr_model else [],
        "gpu_available": False  # EasyOCR detecta automáticamente
    }


# ======================
# Utilitarios avanzados
# ======================
@router.post("/extract-tables")
@limiter.limit("5/minute")
async def extract_tables(
    request: Request,
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """
    Intenta extraer tablas de una imagen.
    (Requeriría lógica adicional para detección de tablas)
    """
    if not model_loader.ocr_model:
        raise HTTPException(status_code=503, detail="OCR no disponible")
    
    # Esta es una implementación básica
    # Para detección de tablas real necesitarías un modelo especializado
    
    try:
        contents = await file.read(5 * 1024 * 1024)
        
        # Extraer todo el texto
        result = model_loader.ocr_model.readtext(contents, detail=True, paragraph=True)
        
        # Simular detección de tablas basada en alineamiento
        tables = []
        current_table = []
        
        for item in result:
            bbox, text, confidence = item
            # Lógica simplificada para detectar filas/columnas
            # En producción usarías un modelo de detección de tablas
            
            current_table.append({
                "text": text,
                "bbox": bbox.tolist() if hasattr(bbox, 'tolist') else bbox,
                "confidence": confidence
            })
        
        if current_table:
            tables.append({
                "rows": len(current_table),
                "cells": current_table
            })
        
        return {
            "tables_found": len(tables),
            "tables": tables,
            "note": "Esta es una extracción básica. Para mejor precisión use un modelo especializado en tablas."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extrayendo tablas: {str(e)}")