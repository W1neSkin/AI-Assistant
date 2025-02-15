from openai import AsyncOpenAI
from app.core.config import settings
from app.utils.logger import setup_logger
from app.llm.base_llm import BaseLLM

logger = setup_logger(__name__)

class CloudLLM(BaseLLM):
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = settings.LLM_MODEL

    async def initialize(self):
        """Initialize cloud LLM client"""
        try:
            logger.info(f"Initializing cloud LLM with model: {settings.LLM_MODEL}")
            # Test connection by listing models
            # await self.client.models.list()
            logger.info("Cloud LLM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Cloud LLM: {str(e)}")
            raise

    async def close(self):
        """Close cloud LLM client"""
        if self.client:
            await self.client.close()
            self.client = None

    async def generate_answer(self, prompt: str) -> str:
        """Generate answer using Cloud API."""
        try:
            logger.info(f"Generating answer with cloud model: {self.model}")
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
                
                if not response or not response.choices:
                    logger.error("Empty response from Cloud API")
                    raise ValueError("Empty response from API")
                    
                return response.choices[0].message.content.strip()
            except Exception as api_error:
                logger.error(f"Cloud API error: {str(api_error)}")
                raise
            
        except Exception as e:
            logger.error(f"Error generating answer with Cloud: {str(e)}")
            raise 