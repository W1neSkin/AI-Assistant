from llama_index.llms.openrouter import OpenRouter
from llama_index.core.llms import ChatMessage

from openai import AsyncOpenAI, OpenAI
from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class OpenAILLM:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = settings.DEEPSEEK_MODEL

    async def initialize(self):
        """Initialize OpenAI client"""
        try:
            logger.info(f"Initializing OpenAI LLM with model: {settings.DEEPSEEK_MODEL}")
            # Test connection by listing models
            # await self.client.models.list()
            logger.info("OpenAI LLM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI LLM: {str(e)}")
            raise

    async def generate_answer(self, prompt: str) -> str:
        """Generate answer using OpenAI API."""
        try:
            logger.info(f"Generating answer with OpenAI model: {self.model}")
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS,
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating answer with OpenAI: {str(e)}")
            raise 