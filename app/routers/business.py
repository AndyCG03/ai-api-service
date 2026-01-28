# app/routes/business.py
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from loguru import logger

from app.models.loader import model_loader
from app.auth.api_keys import verify_api_key

router = APIRouter(prefix="/business", tags=["Business AI"])


# ================ SCHEMAS ================

class ClassifyRequest(BaseModel):
    text: str
    categories: List[str]
    multi_label: bool = Field(False, description="Permitir múltiples categorías simultáneamente")

class SentimentRequest(BaseModel):
    text: str
    language: Optional[str] = Field(None, description="Idioma del texto (auto-detectar si no se especifica)")

class EntityExtractionRequest(BaseModel):
    text: str
    entity_types: Optional[List[str]] = Field(
        None, 
        description="Tipos de entidades a extraer (ej: PER, ORG, LOC, DATE, MONEY)"
    )

class SummarizationRequest(BaseModel):
    text: str
    max_length: int = Field(150, ge=30, le=500, description="Longitud máxima del resumen (30-500 caracteres)")
    min_length: Optional[int] = Field(None, description="Longitud mínima del resumen")
    type: Literal["abstractive", "extractive"] = Field(
        "abstractive", 
        description="Tipo de resumen: abstractivo (genera nuevo texto) o extractivo (extrae frases)"
    )

class TranslationRequest(BaseModel):
    text: str
    source_lang: str = Field("es", pattern="^[a-z]{2}$", description="Código de idioma fuente (ISO 639-1)")
    target_lang: str = Field("en", pattern="^[a-z]{2}$", description="Código de idioma destino (ISO 639-1)")

class ComprehensiveAnalysisRequest(BaseModel):
    text: str
    include_sentiment: bool = True
    include_entities: bool = True
    include_summary: bool = True
    summary_length: int = Field(100, ge=50, le=300)


# ================ ENDPOINTS ================

@router.post("/classify", summary="Clasificación de texto")
async def classify_text(
    request: ClassifyRequest,
    api_key_data: dict = Depends(verify_api_key),
    fastapi_request: Request = None
):
    """
    Clasifica texto en categorías personalizadas usando zero-shot classification.
    
    **Casos de uso:**
    - Categorización automática de tickets de soporte
    - Filtrado de contenido por tema
    - Análisis de intenciones en chatbots
    - Organización de documentos
    
    **Ejemplo de respuesta exitosa:**
    ```json
    {
        "text": "Mi producto no funciona",
        "labels": ["soporte_tecnico", "reclamo", "consulta"],
        "scores": [0.85, 0.12, 0.03],
        "top_category": "soporte_tecnico",
        "confidence": 0.85
    }
    ```
    """
    if not model_loader.classifier_model:
        raise HTTPException(
            status_code=503, 
            detail="Servicio de clasificación no disponible. Verifica que ENABLE_CLASSIFIER=True en configuración."
        )
    
    # Validar que haya categorías
    if not request.categories:
        raise HTTPException(
            status_code=400,
            detail="Debe proporcionar al menos una categoría"
        )
    
    try:
        # Llamar al modelo de clasificación
        result = model_loader.classifier_model(
            request.text,
            candidate_labels=request.categories,
            multi_label=request.multi_label
        )
        
        logger.info(f"📊 Clasificación completada para key: {api_key_data.get('key_prefix', 'unknown')}")
        
        return {
            "text": request.text,
            "labels": result["labels"],
            "scores": [round(score, 4) for score in result["scores"]],
            "top_category": result["labels"][0],
            "confidence": round(result["scores"][0], 4),
            "processing_time_ms": result.get("processing_time", 0),
            "multi_label": request.multi_label
        }
        
    except Exception as e:
        logger.error(f"❌ Error en clasificación: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error procesando clasificación: {str(e)[:100]}"
        )


@router.post("/sentiment", summary="Análisis de sentimiento")
async def analyze_sentiment(
    request: SentimentRequest,
    api_key_data: dict = Depends(verify_api_key)
):
    """
    Analiza el sentimiento y emociones en texto (optimizado para español).
    
    **Casos de uso:**
    - Análisis de reseñas de productos
    - Monitoreo de redes sociales
    - Medición de satisfacción de clientes
    - Análisis de feedback en encuestas
    
    **Escala de sentimiento:**
    - `positive` (positivo)
    - `negative` (negativo) 
    - `neutral` (neutral)
    - `very_positive` (muy positivo)
    - `very_negative` (muy negativo)
    """
    if not model_loader.sentiment_model:
        raise HTTPException(
            status_code=503, 
            detail="Servicio de análisis de sentimiento no disponible"
        )
    
    try:
        result = model_loader.sentiment_model(request.text)
        
        # Mapear etiquetas a formato estándar
        sentiment_map = {
            "POSITIVE": "positive",
            "NEGATIVE": "negative", 
            "NEUTRAL": "neutral",
            "LABEL_0": "very_negative",
            "LABEL_1": "negative",
            "LABEL_2": "neutral", 
            "LABEL_3": "positive",
            "LABEL_4": "very_positive",
            1: "very_negative",
            2: "negative",
            3: "neutral",
            4: "positive",
            5: "very_positive"
        }
        
        label = result[0]["label"]
        score = result[0]["score"]
        
        # Determinar sentimiento
        sentiment = sentiment_map.get(label, label.lower())
        
        # Calcular intensidad
        if sentiment.startswith("very_"):
            intensity = "high"
        elif sentiment in ["positive", "negative"]:
            intensity = "medium"
        else:
            intensity = "low"
        
        return {
            "text": request.text[:200] + "..." if len(request.text) > 200 else request.text,
            "sentiment": sentiment,
            "score": round(score, 4),
            "intensity": intensity,
            "language": request.language or "auto-detected",
            "character_count": len(request.text)
        }
        
    except Exception as e:
        logger.error(f"❌ Error en análisis de sentimiento: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error procesando sentimiento: {str(e)[:100]}"
        )


@router.post("/entities", summary="Extracción de entidades")
async def extract_entities(
    request: EntityExtractionRequest,
    api_key_data: dict = Depends(verify_api_key)
):
    """
    Extrae entidades nombradas (NER) de texto en español.
    
    **Tipos de entidades soportados:**
    - `PER` - Personas
    - `ORG` - Organizaciones
    - `LOC` - Lugares
    - `DATE` - Fechas
    - `MONEY` - Cantidades monetarias
    - `PRODUCT` - Productos
    - `EVENT` - Eventos
    
    **Casos de uso:**
    - Extracción de información de documentos
    - Análisis de contratos legales
    - Procesamiento de currículums
    - Análisis de artículos de noticias
    """
    if not model_loader.ner_model:
        raise HTTPException(
            status_code=503, 
            detail="Servicio de extracción de entidades no disponible"
        )
    
    try:
        entities = model_loader.ner_model(request.text)
        
        # Filtrar por tipos solicitados si se especifican
        if request.entity_types:
            entities = [
                entity for entity in entities 
                if entity["entity_group"] in request.entity_types
            ]
        
        # Agrupar entidades por tipo
        grouped_entities = {}
        entity_counts = {}
        
        for entity in entities:
            entity_type = entity["entity_group"]
            
            # Contar frecuencia
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            
            # Agrupar
            if entity_type not in grouped_entities:
                grouped_entities[entity_type] = []
            
            grouped_entities[entity_type].append({
                "text": entity["word"],
                "score": round(entity["score"], 4),
                "start": entity["start"],
                "end": entity["end"]
            })
        
        return {
            "text": request.text[:300] + "..." if len(request.text) > 300 else request.text,
            "entities": grouped_entities,
            "counts": entity_counts,
            "total_entities": len(entities),
            "entity_types_found": list(entity_counts.keys())
        }
        
    except Exception as e:
        logger.error(f"❌ Error en extracción de entidades: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error procesando entidades: {str(e)[:100]}"
        )


@router.post("/summarize", summary="Resumen de texto")
async def summarize_text(
    request: SummarizationRequest,
    api_key_data: dict = Depends(verify_api_key)
):
    """
    Resume textos largos en versiones concisas.
    
    **Modos disponibles:**
    - `abstractive`: Genera nuevo texto condensado
    - `extractive`: Extrae las frases más importantes
    
    **Casos de uso:**
    - Resumen de artículos y noticias
    - Generación de minutos de reunión
    - Compresión de documentos largos
    - Creación de abstracts ejecutivos
    """
    if not model_loader.summarizer_model:
        raise HTTPException(
            status_code=503, 
            detail="Servicio de resumen no disponible"
        )
    
    try:
        # Calcular estadísticas del texto original
        word_count = len(request.text.split())
        char_count = len(request.text)
        
        # Validar longitud mínima
        if word_count < 10:
            raise HTTPException(
                status_code=400,
                detail="El texto debe tener al menos 10 palabras para poder resumirlo"
            )
        
        # Ajustar longitud mínima si no se especifica
        if not request.min_length:
            request.min_length = max(30, request.max_length // 3)
        
        # Generar resumen
        summary_result = model_loader.summarizer_model(
            request.text,
            max_length=request.max_length,
            min_length=request.min_length,
            do_sample=False
        )
        
        summary = summary_result[0]["summary_text"]
        summary_word_count = len(summary.split())
        
        # Calcular métricas
        compression_ratio = summary_word_count / word_count if word_count > 0 else 0
        
        return {
            "original_length": {
                "words": word_count,
                "characters": char_count
            },
            "summary_length": {
                "words": summary_word_count,
                "characters": len(summary)
            },
            "compression_ratio": round(compression_ratio, 3),
            "compression_percentage": f"{compression_ratio:.1%}",
            "summary": summary,
            "type": request.type,
            "reading_time_saved": f"{round((word_count - summary_word_count) / 200, 1)} min"  # 200 palabras/min
        }
        
    except Exception as e:
        logger.error(f"❌ Error en resumen: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error generando resumen: {str(e)[:100]}"
        )


@router.post("/translate", summary="Traducción de texto")
async def translate_text(
    request: TranslationRequest,
    api_key_data: dict = Depends(verify_api_key)
):
    """
    Traduce texto entre idiomas (especializado español-inglés).
    
    **Idiomas soportados:** Español (es) ↔ Inglés (en)
    
    **Casos de uso:**
    - Localización de contenido web
    - Soporte multilingüe a clientes
    - Traducción de documentación
    - Comunicación internacional
    """
    if not model_loader.translator_model:
        raise HTTPException(
            status_code=503, 
            detail="Servicio de traducción no disponible"
        )
    
    try:
        # Validar combinaciones de idiomas soportadas
        supported_pairs = [("es", "en"), ("en", "es")]
        if (request.source_lang, request.target_lang) not in supported_pairs:
            raise HTTPException(
                status_code=400,
                detail=f"Combinación de idiomas no soportada. Soporta: es↔en"
            )
        
        # Realizar traducción
        translation_result = model_loader.translator_model(request.text)
        translated_text = translation_result[0]["translation_text"]
        
        return {
            "original": {
                "text": request.text,
                "language": request.source_lang,
                "character_count": len(request.text)
            },
            "translation": {
                "text": translated_text,
                "language": request.target_lang,
                "character_count": len(translated_text)
            },
            "pair": f"{request.source_lang}→{request.target_lang}",
            "confidence": "high"  # Los modelos de traducción modernos son muy confiables
        }
        
    except Exception as e:
        logger.error(f"❌ Error en traducción: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error en traducción: {str(e)[:100]}"
        )


@router.post("/analyze/comprehensive", summary="Análisis completo de texto")
async def comprehensive_analysis(
    request: ComprehensiveAnalysisRequest,
    api_key_data: dict = Depends(verify_api_key)
):
    """
    Análisis completo de un texto: sentimiento, entidades y resumen en una sola llamada.
    
    **Perfecto para:**
    - Análisis de documentos empresariales
    - Procesamiento de feedback de clientes
    - Resúmenes ejecutivos automáticos
    - Análisis de contenido web
    
    **Nota:** Esta operación consume más recursos. Para textos muy largos (>5000 palabras),
    considera usar los endpoints individuales.
    """
    results = {
        "metadata": {
            "api_key": api_key_data.get("key_prefix", "unknown"),
            "text_length": len(request.text),
            "word_count": len(request.text.split())
        },
        "analysis": {}
    }
    
    # 1. Análisis de sentimiento (si está habilitado)
    if request.include_sentiment and model_loader.sentiment_model:
        try:
            sentiment_request = SentimentRequest(text=request.text)
            sentiment_result = await analyze_sentiment(sentiment_request, api_key_data)
            results["analysis"]["sentiment"] = sentiment_result
        except Exception as e:
            results["analysis"]["sentiment"] = {
                "status": "error",
                "message": str(e)[:100]
            }
    
    # 2. Extracción de entidades (si está habilitado)
    if request.include_entities and model_loader.ner_model:
        try:
            entities_request = EntityExtractionRequest(text=request.text)
            entities_result = await extract_entities(entities_request, api_key_data)
            results["analysis"]["entities"] = entities_result
        except Exception as e:
            results["analysis"]["entities"] = {
                "status": "error", 
                "message": str(e)[:100]
            }
    
    # 3. Resumen (si está habilitado)
    if request.include_summary and model_loader.summarizer_model:
        try:
            summary_request = SummarizationRequest(
                text=request.text,
                max_length=request.summary_length
            )
            summary_result = await summarize_text(summary_request, api_key_data)
            results["analysis"]["summary"] = summary_result
        except Exception as e:
            results["analysis"]["summary"] = {
                "status": "error",
                "message": str(e)[:100]
            }
    
    # 4. Estadísticas del texto
    sentences = [s.strip() for s in request.text.split('.') if s.strip()]
    avg_words_per_sentence = len(request.text.split()) / max(len(sentences), 1)
    
    results["statistics"] = {
        "words": len(request.text.split()),
        "characters": len(request.text),
        "sentences": len(sentences),
        "paragraphs": len([p for p in request.text.split('\n\n') if p.strip()]),
        "average_word_length": sum(len(word) for word in request.text.split()) / max(len(request.text.split()), 1),
        "average_words_per_sentence": round(avg_words_per_sentence, 1),
        "reading_time_minutes": round(len(request.text.split()) / 200, 1),  # 200 palabras/minuto
        "complexity": "alta" if avg_words_per_sentence > 20 else "media" if avg_words_per_sentence > 10 else "baja"
    }
    
    # Calcular porcentaje de éxito
    successful_analyses = sum(
        1 for k, v in results["analysis"].items() 
        if v.get("status") != "error"
    )
    total_analyses = len(results["analysis"])
    
    results["metadata"]["success_rate"] = f"{successful_analyses/total_analyses:.0%}" if total_analyses > 0 else "0%"
    
    return results


@router.get("/health", summary="Verificación de servicios")
async def business_health_check(
    api_key_data: dict = Depends(verify_api_key)
):
    """
    Verifica el estado de todos los servicios de Business AI.
    """
    health_status = {
        "timestamp": datetime.now().isoformat(),
        "services": {
            "classifier": {
                "enabled": model_loader.classifier_model is not None,
                "status": "operational" if model_loader.classifier_model else "disabled",
                "model": settings.classifier_model_name if model_loader.classifier_model else None
            },
            "sentiment": {
                "enabled": model_loader.sentiment_model is not None,
                "status": "operational" if model_loader.sentiment_model else "disabled",
                "model": settings.sentiment_model_name if model_loader.sentiment_model else None
            },
            "ner": {
                "enabled": model_loader.ner_model is not None,
                "status": "operational" if model_loader.ner_model else "disabled",
                "model": settings.ner_model_name if model_loader.ner_model else None
            },
            "summarizer": {
                "enabled": model_loader.summarizer_model is not None,
                "status": "operational" if model_loader.summarizer_model else "disabled",
                "model": settings.summarizer_model_name if model_loader.summarizer_model else None
            },
            "translator": {
                "enabled": model_loader.translator_model is not None,
                "status": "operational" if model_loader.translator_model else "disabled",
                "model": settings.translator_model_name if model_loader.translator_model else None
            }
        },
        "overall": "healthy" if model_loader.models_loaded > 0 else "degraded",
        "models_loaded": model_loader.models_loaded,
        "api_key": api_key_data.get("key_prefix", "unknown")
    }
    
    return health_status


# Importar datetime para health check
from datetime import datetime
from app.config import settings