from app.core.config import settings
from app.services.local_llm import LocalLLM
from app.services.openai_llm import OpenAILLM

async def create_llm():
    """Factory function to create appropriate LLM instance."""
    if settings.LLM_PROVIDER == "openai":
        return OpenAILLM()
    else:
        return LocalLLM(model_path="./models/mistral.gguf") 