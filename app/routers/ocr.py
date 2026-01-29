from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request, Form
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple, Any
from app.auth.api_keys import verify_api_key
from app.auth.rate_limit import limiter
from app.models.loader import model_loader
import base64
import io
from PIL import Image
import numpy as np
import time

router = APIRouter(prefix="/ocr", tags=["OCR"])


# ======================
# Helpers
# ======================
def bytes_to_np_image(image_bytes: bytes) -> np.ndarray:
    """Convierte bytes de imagen a array numpy."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return np.array(image)


def safe_readtext(reader, image_bytes: bytes, detail: bool = True, paragraph: bool = True) -> Any:
    """
    Wrapper seguro para easyocr.readtext que maneja diferentes estructuras de retorno.
    """
    if not reader:
        raise ValueError("OCR reader no disponible")
    
    image_np = bytes_to_np_image(image_bytes)
    
    try:
        if detail:
            # Con detail=True, easyocr devuelve lista de tuplas (bbox, text, confidence)
            result = reader.readtext(
                image_np,
                detail=detail,
                paragraph=paragraph,
                batch_size=1,
                workers=0
            )
            # Verificar estructura
            if result and len(result) > 0:
                if isinstance(result[0], tuple) and len(result[0]) >= 3:
                    return result
                else:
                    # Si no tiene 3 elementos, crear estructura consistente
                    processed_result = []
                    for item in result:
                        if isinstance(item, tuple):
                            if len(item) == 3:
                                processed_result.append(item)
                            elif len(item) == 2:
                                # Asumir que es (text, bbox) o similar
                                bbox, text = item[0], item[1]
                                processed_result.append((bbox, text, 1.0))
                            else:
                                processed_result.append(([], item, 1.0))
                        else:
                            # Si es solo texto
                            processed_result.append(([], str(item), 1.0))
                    return processed_result
        else:
            # Con detail=False, easyocr devuelve solo texto
            result = reader.readtext(
                image_np,
                detail=detail,
                paragraph=paragraph,
                batch_size=1,
                workers=0
            )
            return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en procesamiento OCR: {str(e)}"
        )


def normalize_ocr_result(result: Any, detail: bool) -> List[dict]:
    """
    Normaliza el resultado de OCR a una estructura consistente.
    """
    normalized = []

    if detail:
        # Manejar diferentes estructuras de resultado
        for item in result:
            if isinstance(item, tuple):
                if len(item) == 3:
                    bbox, text, conf = item
                elif len(item) == 2:
                    bbox, text = item
                    conf = 1.0  # Valor por defecto
                else:
                    continue  # Saltar elementos inválidos
            else:
                # Si no es tupla, asumir que es solo texto
                text = str(item)
                bbox = []
                conf = 1.0
            
            # Convertir bbox si es necesario
            if hasattr(bbox, 'tolist'):
                bbox = bbox.tolist()
            elif isinstance(bbox, (list, tuple)):
                bbox = list(bbox)
            
            normalized.append({
                "bbox": bbox,
                "text": text,
                "confidence": float(conf) if conf else 1.0
            })
    else:
        # detail=False: solo texto
        for text in result:
            normalized.append({
                "text": str(text),
                "bbox": [],
                "confidence": 1.0
            })
    
    return normalized


# ======================
# Models
# ======================
class OCRTextResult(BaseModel):
    text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: List[List[float]]
    page: Optional[int] = None


class OCRResponse(BaseModel):
    texts: List[OCRTextResult]
    image_size: Optional[dict] = None
    language: str
    processing_time: float


class OCRBatchRequest(BaseModel):
    images: List[str]
    languages: Optional[List[str]] = ["es", "en"]


class OCRDetectLanguagesResponse(BaseModel):
    detected_languages: List[str]
    confidence: List[float]


# ======================
# Endpoints
# ======================
@router.post("/recognize")
async def recognize_ocr(
    file: UploadFile = File(...),
    detail: bool = Form(True),
    paragraph: bool = Form(True),
    languages: str = Form("es,en")
):
    """
    Endpoint para reconocer texto en una imagen subida.
    """
    if not model_loader.ocr_model:
        raise HTTPException(status_code=503, detail="OCR no disponible")
    
    # Validar tipo de archivo
    allowed_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp']
    file_extension = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    if file_extension not in [ext.lstrip('.') for ext in allowed_extensions]:
        raise HTTPException(
            status_code=400,
            detail=f"Formato de archivo no soportado. Use: {', '.join(allowed_extensions)}"
        )
    
    try:
        start_time = time.time()
        contents = await file.read()
        
        result = safe_readtext(
            model_loader.ocr_model,
            contents,
            detail=detail,
            paragraph=paragraph
        )
        
        processing_time = time.time() - start_time
        
        # Obtener tamaño de imagen
        image = Image.open(io.BytesIO(contents))
        image_size = {"width": image.width, "height": image.height}
        
        normalized_results = normalize_ocr_result(result, detail)
        
        return {
            "engine": "easyocr",
            "detail": detail,
            "paragraph": paragraph,
            "languages": languages.split(','),
            "image_size": image_size,
            "processing_time": round(processing_time, 3),
            "results": normalized_results,
            "total_texts": len(normalized_results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando la imagen: {str(e)}"
        )


@router.post("/recognize-base64", response_model=OCRResponse)
@limiter.limit("10/minute")
async def recognize_text_base64(
    request: Request,
    data: dict,
    api_key: str = Depends(verify_api_key)
):
    """
    Endpoint para reconocer texto en una imagen en base64.
    """
    if not model_loader.ocr_model:
        raise HTTPException(status_code=503, detail="OCR no disponible")
    
    try:
        start_time = time.time()
        
        # Validar datos de entrada
        if "image" not in data:
            raise HTTPException(status_code=400, detail="Se requiere campo 'image'")
        
        image_bytes = base64.b64decode(data["image"])
        image_np = bytes_to_np_image(image_bytes)
        
        # Obtener tamaño de imagen
        image = Image.fromarray(image_np)
        image_size = {"width": image.width, "height": image.height}
        
        # Procesar con OCR
        result = model_loader.ocr_model.readtext(
            image_np,
            detail=True,
            paragraph=data.get("paragraph", True),
            batch_size=1,
            workers=0
        )
        
        processing_time = time.time() - start_time
        
        # Procesar resultados
        texts = []
        for item in result:
            if isinstance(item, tuple) and len(item) >= 2:
                if len(item) == 3:
                    bbox, text, conf = item
                else:  # len == 2
                    bbox, text = item
                    conf = 1.0
                
                # Convertir bbox si es necesario
                if hasattr(bbox, "tolist"):
                    bbox = bbox.tolist()
                
                texts.append(OCRTextResult(
                    text=text,
                    confidence=float(conf),
                    bbox=bbox
                ))
        
        return OCRResponse(
            texts=texts,
            image_size=image_size,
            language=",".join(data.get("languages", ["es", "en"])),
            processing_time=round(processing_time, 3)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando imagen base64: {str(e)}"
        )


@router.post("/batch", response_model=List[OCRResponse])
@limiter.limit("5/minute")
async def recognize_batch(
    request: Request,
    data: OCRBatchRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Endpoint para procesar múltiples imágenes en batch.
    """
    if not model_loader.ocr_model:
        raise HTTPException(status_code=503, detail="OCR no disponible")
    
    responses = []
    
    for i, image_b64 in enumerate(data.images):
        try:
            start_time = time.time()
            image_np = bytes_to_np_image(base64.b64decode(image_b64))
            
            # Obtener tamaño de imagen
            image = Image.fromarray(image_np)
            image_size = {"width": image.width, "height": image.height}
            
            result = model_loader.ocr_model.readtext(
                image_np,
                detail=True,
                paragraph=True,
                batch_size=1,
                workers=0
            )
            
            processing_time = time.time() - start_time
            
            # Procesar resultados
            texts = []
            for item in result:
                if isinstance(item, tuple) and len(item) >= 2:
                    if len(item) == 3:
                        bbox, text, conf = item
                    else:
                        bbox, text = item
                        conf = 1.0
                    
                    # Convertir bbox si es necesario
                    if hasattr(bbox, "tolist"):
                        bbox = bbox.tolist()
                    
                    texts.append(OCRTextResult(
                        text=text,
                        confidence=float(conf),
                        bbox=bbox,
                        page=i
                    ))
            
            responses.append(OCRResponse(
                texts=texts,
                image_size=image_size,
                language=",".join(data.languages),
                processing_time=round(processing_time, 3)
            ))
            
        except Exception as e:
            # Continuar con otras imágenes incluso si una falla
            responses.append(OCRResponse(
                texts=[],
                image_size=None,
                language=",".join(data.languages),
                processing_time=0.0,
                error=f"Error procesando imagen {i}: {str(e)}"
            ))
    
    return responses


@router.get("/info")
async def ocr_info():
    """
    Endpoint para obtener información sobre el motor OCR.
    """
    reader = model_loader.ocr_model

    if not reader:
        raise HTTPException(status_code=503, detail="OCR no cargado")

    try:
        return {
            "engine": "easyocr",
            "version": "1.7.1",
            "languages": reader.lang_list,
            "gpu": reader.gpu,
            "model_storage_directory": str(reader.model_storage_directory),
            "detector": "craft_mlt_25k",
            "recognizer": "english_g2",
            "batch_size": 1,
            "workers": 0,
            "status": "ready",
            "available_languages": [
                "abq", "ady", "af", "ang", "ar", "as", "ava", "az", "be", "bg",
                "bh", "bho", "bn", "bs", "ch_sim", "ch_tra", "che", "cs", "cy",
                "da", "dar", "de", "en", "es", "et", "fa", "fr", "ga", "gom",
                "hi", "hr", "hu", "id", "inh", "is", "it", "ja", "kbd", "kn",
                "ko", "ku", "la", "lbe", "lez", "lt", "lv", "mah", "mai", "mi",
                "mn", "mr", "ms", "mt", "ne", "new", "nl", "no", "oc", "pi",
                "pl", "pt", "ro", "ru", "sk", "sl", "sq", "sv", "sw", "ta",
                "tab", "te", "th", "tjk", "tl", "tr", "ug", "uk", "ur", "uz",
                "vi"
            ]
        }
    except Exception as e:
        return {
            "engine": "easyocr",
            "status": "error",
            "error": str(e)
        }


@router.post("/detect-languages")
async def detect_languages(
    file: UploadFile = File(...)
):
    """
    Endpoint para detectar idiomas en una imagen.
    """
    if not model_loader.ocr_model:
        raise HTTPException(status_code=503, detail="OCR no disponible")
    
    try:
        contents = await file.read()
        image_np = bytes_to_np_image(contents)
        
        # EasyOCR no tiene detección de idioma incorporada,
        # pero podemos intentar detectar basado en caracteres
        result = model_loader.ocr_model.readtext(
            image_np,
            detail=True,
            paragraph=True,
            batch_size=1,
            workers=0
        )
        
        # Analizar caracteres para detectar idioma
        detected_chars = set()
        for item in result:
            if isinstance(item, tuple) and len(item) >= 2:
                text = item[1] if len(item) >= 2 else str(item[0])
                detected_chars.update(text)
        
        # Detección simple basada en rangos Unicode
        languages = []
        confidences = []
        
        # Verificar caracteres latinos
        if any(ord(c) < 128 for c in detected_chars):
            languages.append("en")
            confidences.append(0.8)
        
        # Verificar caracteres cirílicos
        if any(0x0400 <= ord(c) <= 0x04FF for c in detected_chars):
            languages.append("ru")
            confidences.append(0.7)
        
        # Verificar caracteres árabes
        if any(0x0600 <= ord(c) <= 0x06FF for c in detected_chars):
            languages.append("ar")
            confidences.append(0.7)
        
        if not languages:
            languages = ["en"]
            confidences = [0.5]
        
        return OCRDetectLanguagesResponse(
            detected_languages=languages,
            confidence=confidences
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error detectando idiomas: {str(e)}"
        )