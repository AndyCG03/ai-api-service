from app.config import settings
from loguru import logger

class ModelLoader:
    def __init__(self):
        self.llm_model = None
        self.whisper_model = None
        self.embedding_model = None
    
    def load_llm(self):
        if not settings.enable_llm:
            return
        
        logger.info("Cargando modelo LLM...")
        # TODO: Implementar carga del modelo
        # from transformers import AutoModelForCausalLM, AutoTokenizer
        # self.llm_model = AutoModelForCausalLM.from_pretrained(...)
        logger.info("✅ Modelo LLM cargado")
    
    def load_whisper(self):
        if not settings.enable_whisper:
            return
        
        logger.info("Cargando modelo Whisper...")
        # TODO: Implementar carga del modelo
        # import whisper
        # self.whisper_model = whisper.load_model(settings.whisper_model_size)
        logger.info("✅ Modelo Whisper cargado")
    
    def load_embeddings(self):
        if not settings.enable_embeddings:
            return
        
        logger.info("Cargando modelo de embeddings...")
        # TODO: Implementar carga del modelo
        # from sentence_transformers import SentenceTransformer
        # self.embedding_model = SentenceTransformer(settings.embedding_model)
        logger.info("✅ Modelo de embeddings cargado")
    
    def load_all(self):
        self.load_llm()
        self.load_whisper()
        self.load_embeddings()

model_loader = ModelLoader()
