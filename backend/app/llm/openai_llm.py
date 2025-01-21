from openai import AsyncOpenAI
from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class OpenAILLM:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        
    async def initialize(self):
        """Initialize OpenAI client"""
        try:
            logger.info(f"Initializing OpenAI LLM with model: {self.model}")
            # Test connection by listing models
            await self.client.models.list()
            logger.info("OpenAI LLM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI LLM: {str(e)}")
            raise

    async def generate_answer(self, prompt: str) -> str:
        """Generate answer using OpenAI API."""
        try:
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