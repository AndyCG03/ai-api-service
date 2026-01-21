from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API Configuration
    environment: str = "development"
    api_version: str = "v1"
    debug: bool = True
    
    # Security
    api_keys: str = "demo_key_123"
    secret_key: str = "your-secret-key"
    
    # Rate Limiting
    rate_limit_per_minute: int = 10
    max_concurrent_requests: int = 5
    
    # Models
    models_path: str = "./data/models"
    enable_llm: bool = True
    enable_whisper: bool = True
    enable_embeddings: bool = True
    
    # LLM Settings
    llm_model_name: str = "llama-3.2-1b"
    llm_max_tokens: int = 512
    llm_temperature: float = 0.7
    
    # Whisper Settings
    whisper_model_size: str = "base"
    whisper_language: str = "es"
    
    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    
    @property
    def api_keys_list(self) -> List[str]:
        return [key.strip() for key in self.api_keys.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
