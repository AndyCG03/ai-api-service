# app/config.py
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from typing import List, Optional
from pathlib import Path


class Settings(BaseSettings):
    # ======================
    # API Configuration
    # ======================
    environment: str = Field("development", env="ENVIRONMENT")
    api_version: str = Field("v1", env="API_VERSION")
    debug: bool = Field(True, env="DEBUG")

    # ======================
    # Security
    # ======================
    api_keys: str = Field("demo_key_123", env="API_KEYS")
    secret_key: str = Field("your-secret-key", env="SECRET_KEY")

    # ======================
    # Rate Limiting
    # ======================
    rate_limit_per_minute: int = Field(10, env="RATE_LIMIT_PER_MINUTE")
    max_concurrent_requests: int = Field(5, env="MAX_CONCURRENT_REQUESTS")

    # ======================
    # Models Base Path
    # ======================
    models_path: str = Field("./data/models", env="MODELS_PATH")

    enable_llm: bool = Field(True, env="ENABLE_LLM")
    enable_whisper: bool = Field(True, env="ENABLE_WHISPER")
    enable_embeddings: bool = Field(True, env="ENABLE_EMBEDDINGS")
    enable_ocr: bool = Field(True, env="ENABLE_OCR")
    enable_classifier: bool = Field(True, env="ENABLE_CLASSIFIER")
    enable_sentiment: bool = Field(True, env="ENABLE_SENTIMENT")
    enable_ner: bool = Field(True, env="ENABLE_NER")
    enable_summarizer: bool = Field(True, env="ENABLE_SUMMARIZER")
    enable_translator: bool = Field(True, env="ENABLE_TRANSLATOR")

    # ======================
    # LLM Settings
    # ======================
    llm_model_name: str = Field(..., env="LLM_MODEL_NAME")
    llm_model_path_env: Optional[str] = Field(None, env="LLM_MODEL_PATH")
    llm_max_tokens: int = Field(512, env="LLM_MAX_TOKENS")
    llm_temperature: float = Field(0.7, env="LLM_TEMPERATURE")

    # ======================
    # Whisper Settings
    # ======================
    whisper_model_size: str = Field("base", env="WHISPER_MODEL_SIZE")
    whisper_model_name: str = Field("tiny.pt", env="WHISPER_MODEL_NAME")
    whisper_model_path_env: Optional[str] = Field(None, env="WHISPER_MODEL_PATH")
    whisper_language: str = Field("es", env="WHISPER_LANGUAGE")

    # ======================
    # Embeddings
    # ======================
    embedding_model_name: str = Field(..., env="EMBEDDING_MODEL_NAME")
    embedding_model_path_env: Optional[str] = Field(None, env="EMBEDDING_MODEL_PATH")

    # ======================
    # OCR Settings (CORREGIDO: usar _env como los demás)
    # ======================
    ocr_detector_path_env: Optional[str] = Field(None, env="OCR_DETECTOR_PATH")
    ocr_recognizer_path_env: Optional[str] = Field(None, env="OCR_RECOGNIZER_PATH")
    ocr_language_path_env: Optional[str] = Field(None, env="OCR_LANGUAGE_PATH")


    # TODO Rectificar luego la estructura del config para consistencia
    # ======================
    # Nuevos Modelos Configuración
    # ======================
    classifier_model_name: str = Field(
        "distilbert-base-uncased-finetuned-sst-2-english", 
        env="CLASSIFIER_MODEL_NAME"
    )
    sentiment_model_name: str = Field(
        "finiteautomata/beto-sentiment-analysis", 
        env="SENTIMENT_MODEL_NAME"
    )
    ner_model_name: str = Field(
        "mrm8488/bert-spanish-cased-finetuned-ner", 
        env="NER_MODEL_NAME"
    )
    summarizer_model_name: str = Field(
        "google/pegasus-cnn_dailymail", 
        env="SUMMARIZER_MODEL_NAME"
    )
    translator_model_name: str = Field(
        "Helsinki-NLP/opus-mt-es-en", 
        env="TRANSLATOR_MODEL_NAME"
    )
    
    # ======================
    # Configuraciones de nuevos modelos
    # ======================
    classifier_max_length: int = Field(512, env="CLASSIFIER_MAX_LENGTH")
    sentiment_max_length: int = Field(256, env="SENTIMENT_MAX_LENGTH")
    ner_max_length: int = Field(384, env="NER_MAX_LENGTH")
    summarizer_max_length: int = Field(150, env="SUMMARIZER_MAX_LENGTH")
    translator_max_length: int = Field(200, env="TRANSLATOR_MAX_LENGTH")




    # ======================
    # Server
    # ======================
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    workers: int = Field(1, env="WORKERS")

    # =====================================================
    # 🔹 PATH RESOLUTION
    # =====================================================
    @property
    def base_models_path(self) -> Path:
        """Ruta ABSOLUTA desde la raíz del proyecto"""
        project_root = Path(__file__).parent.parent
        return (project_root / self.models_path).resolve()
    
    @property
    def llm_model_path(self) -> Path:
        if self.llm_model_path_env:
            return Path(self.llm_model_path_env).resolve()
        return self.base_models_path / self.llm_model_name
    
    @property
    def whisper_model_path(self) -> Path:
        if self.whisper_model_path_env:
            return Path(self.whisper_model_path_env).resolve()
        return self.base_models_path / self.whisper_model_name
    
    @property
    def embedding_model_path(self) -> Path:
        if self.embedding_model_path_env:
            return Path(self.embedding_model_path_env).resolve()
        return self.base_models_path / self.embedding_model_name
    
    @property
    def ocr_detector_path(self) -> Path:
        """Ruta completa al detector OCR"""
        if not self.ocr_detector_path_env:
            raise ValueError("OCR_DETECTOR_PATH no configurado en .env")
        
        path = Path(self.ocr_detector_path_env)
        if path.is_absolute():
            return path.resolve()
        return self.base_models_path / path
    
    @property
    def ocr_recognizer_path(self) -> Path:
        """Ruta completa al reconocedor OCR"""
        if not self.ocr_recognizer_path_env:
            raise ValueError("OCR_RECOGNIZER_PATH no configurado en .env")
        
        path = Path(self.ocr_recognizer_path_env)
        if path.is_absolute():
            return path.resolve()
        return self.base_models_path / path
    
    @property
    def ocr_language_path(self) -> Path:
        """Ruta completa al modelo de idioma OCR"""
        if not self.ocr_language_path_env:
            raise ValueError("OCR_LANGUAGE_PATH no configurado en .env")
        
        path = Path(self.ocr_language_path_env)
        if path.is_absolute():
            return path.resolve()
        return self.base_models_path / path
    
    @property
    def transformer_models_path(self) -> Path:
        """Ruta para modelos Transformers (descargados automáticamente)"""
        return self.base_models_path / "transformers"
    
    @property
    def classifier_model_path(self) -> Path:
        """Ruta para el modelo de clasificación"""
        model_dir = self.transformer_models_path / "classifier"
        model_name_safe = self.classifier_model_name.replace("/", "_")
        return model_dir / model_name_safe
    
    @property
    def sentiment_model_path(self) -> Path:
        """Ruta para el modelo de sentimiento"""
        model_dir = self.transformer_models_path / "sentiment"
        model_name_safe = self.sentiment_model_name.replace("/", "_")
        return model_dir / model_name_safe
    
    @property
    def ner_model_path(self) -> Path:
        """Ruta para el modelo NER"""
        model_dir = self.transformer_models_path / "ner"
        model_name_safe = self.ner_model_name.replace("/", "_")
        return model_dir / model_name_safe
    
    @property
    def summarizer_model_path(self) -> Path:
        """Ruta para el modelo de resumen"""
        model_dir = self.transformer_models_path / "summarizer"
        model_name_safe = self.summarizer_model_name.replace("/", "_")
        return model_dir / model_name_safe
    
    @property
    def translator_model_path(self) -> Path:
        """Ruta para el modelo de traducción"""
        model_dir = self.transformer_models_path / "translator"
        model_name_safe = self.translator_model_name.replace("/", "_")
        return model_dir / model_name_safe
    
    # ======================
    # Helpers
    # ======================
    @property
    def api_keys_list(self) -> List[str]:
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]

    # Configuración Pydantic v2
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()