from app.utils.logger import setup_logger
from app.core.config import settings
import requests
from app.llm.base_llm import BaseLLM

logger = setup_logger(__name__)

class LocalLLM(BaseLLM):
    def __init__(self, base_url: str = "http://ollama:11434", model_name: str = settings.LLM_LOCAL_MODEL):
        self.base_url = base_url
        self.model_name = model_name
        self.initialized = False
    
    async def initialize(self):
        """Initialize LLM connection"""
        if not self.initialized:
            # Test connection
            try:
                response = requests.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                self.initialized = True
                logger.info(f"LLM initialized with model: {self.model_name}")
            except Exception as e:
                logger.error(f"LLM connection failed: {str(e)}")
                raise

    async def close(self):
        """Close LLM connection"""
        if self.initialized:
            self.initialized = False
            logger.info(f"LLM connection closed for model: {self.model_name}")

    async def generate_answer(self, prompt: str, max_tokens: int = 4096) -> str:
        try:
            logger.info(f"Generating answer with Local LLM model: {self.model_name}")
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": settings.TEMPERATURE,  # Use from settings
                        "max_tokens": max_tokens,
                        "num_gpu": 1
                    }
                }
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            logger.error(f"Ollama API error: {str(e)}")
            raise
