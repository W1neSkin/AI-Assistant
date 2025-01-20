from typing import Dict, Any, Optional, Literal
from app.llm.factory import create_llm
from app.core.config import settings
import logging
from app.llm.local_llm import LocalLLM

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self._local_llm = None
        self._openai_llm = None
        self._current_provider: Literal["local", "openai"] = settings.LLM_PROVIDER

    async def initialize(self):
        """Initialize both LLM models"""
        if not self._local_llm:
            self._local_llm = await create_llm("local")
            await self._local_llm.initialize()
            
        if not self._openai_llm and settings.OPENAI_API_KEY:
            self._openai_llm = await create_llm("openai")
            await self._openai_llm.initialize()

    @property
    def current_provider(self) -> str:
        """Get current LLM provider"""
        return self._current_provider

    async def switch_provider(self, provider: Literal["local", "openai"]) -> bool:
        """Switch between LLM providers"""
        try:
            if provider == "openai" and not self._openai_llm:
                raise ValueError("OpenAI model not initialized - missing API key")
            
            self._current_provider = provider
            logger.info(f"Switched to {provider} model")
            return True
        except Exception as e:
            logger.error(f"Error switching provider: {str(e)}")
            return False

    async def is_db_question(self, question: str) -> bool:
        """Use current LLM to determine if question needs database access"""
        prompt = f"""
        Determine if this question requires database access:
        Question: {question}
        Return only 'true' or 'false'.
        """
        model = self._get_current_model()
        response = await model.generate_answer(prompt)
        return response.strip().lower() == "true"

    async def generate_sql(self, question: str, schema: str) -> str:
        """Generate SQL query using LLM"""
        try:
            if not self._local_llm and not self._openai_llm:
                await self.initialize()
            prompt = f"""
            Given this database schema:
            {schema}
            
            Generate a SQL query for this question:
            {question}
            """
            model = self._get_current_model()
            return await model.generate_answer(prompt)
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            raise

    async def generate_answer(self, prompt: str) -> Dict[str, Any]:
        """Generate answer using current model"""
        try:
            # Log prompt size
            logger.debug(f"Generating answer for prompt of size {len(prompt)} chars")
            # Rough token estimate (words * 1.3)
            estimated_tokens = len(prompt.split()) * 1.3
            logger.debug(f"Estimated tokens: {estimated_tokens}")

            model = self._get_current_model()
            response = await model.generate_answer(
                prompt,
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS
            )
            
            return {
                "answer": response.strip(),
                "model": self.current_provider
            }

        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            raise

    def _get_current_model(self):
        """Get current LLM model instance"""
        if self._current_provider == "openai":
            if not self._openai_llm:
                raise ValueError("OpenAI model not initialized")
            return self._openai_llm
        return self._local_llm 