from llama_cpp import Llama
from app.utils.logger import setup_logger
from app.core.config import settings
import requests
from typing import Optional

logger = setup_logger(__name__)

class LocalLLM:
    def __init__(self, base_url: str = "http://ollama:11434"):
        self.base_url = base_url
        self.model_name = "deepseek-r1:7b"
    
    async def generate_answer(self, prompt: str, max_tokens: int = 4096) -> str:
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "max_tokens": max_tokens,
                        "num_gpu": 1  # Utilize GPU
                    }
                }
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            logger.error(f"Ollama API error: {str(e)}")
            raise

    def estimate_tokens(self, text: str) -> int:
        return int(len(text.encode('utf-8')) / 3)

    def truncate_context(self, context: str, max_tokens: int) -> str:
        sentences = context.split('. ')
        truncated = []
        current_tokens = 0
        
        for sentence in sentences:
            tokens = self.estimate_tokens(sentence)
            if current_tokens + tokens > max_tokens:
                break
            truncated.append(sentence)
            current_tokens += tokens
        
        return '. '.join(truncated) 