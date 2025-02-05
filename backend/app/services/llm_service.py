from typing import Dict, Any, Optional, Literal
from app.llm.factory import create_llm
from app.llm.openai_llm import OpenAILLM
from app.llm.local_llm import LocalLLM
from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

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
            
        if not self._openai_llm and settings.DEEPSEEK_API_KEY:
            self._openai_llm = await create_llm("openai")
            await self._openai_llm.initialize()

    @property
    def current_provider(self) -> str:
        """Get current LLM provider"""
        return self._current_provider

    async def switch_provider(self, provider: Literal["local", "openai"]) -> bool:
        """Switch between LLM providers"""
        try:
            logger.info(f"Attempting to switch to {provider} provider")
            if provider == "openai" and not self._openai_llm:
                logger.info("OpenAI model not initialized, creating new instance")
                self._openai_llm = await create_llm("openai")
                await self._openai_llm.initialize()
                
            self._current_provider = provider
            logger.info(f"Successfully switched to {provider} model")
            return True
        except Exception as e:
            logger.error(f"Error switching provider: {str(e)}")
            return False

    async def is_db_question(self, question: str) -> bool:
        """Use current LLM to determine if question needs database access"""
        prompt = f"""Analyze if this question requires database access.
        Return ONLY 'true' or 'false' without explanation.
        
        Guidelines:
        - Database is needed for questions about specific records, statistics, or data analysis
        - Database is NOT needed for general questions or document-based queries
        - Consider keywords like: show, find, count, list, how many, average, total
        
        Examples:
        - "Show me all clients from New York" -> true (requires database)
        - "What is machine learning?" -> false (general knowledge)
        - "How many orders were placed last month?" -> true (requires database)
        - "Explain the company's privacy policy" -> false (document-based)
        
        Question: {question}
        
        Think step by step:
        1. Identify key action words
        2. Check if question asks for specific data
        3. Determine if answer requires stored records
        """
        
        logger.info(f"Checking if question needs DB: '{question}'")
        model = self._get_current_model()
        try:
            logger.info(f"Generating answer for DB determination: {prompt}")
            response = await model.generate_answer(prompt)
            logger.info(f"Generated response: {response}")
            needs_db = "true" in response.strip().lower()
            logger.info(f"DB access determination: {needs_db}")
            return needs_db
        except Exception as e:
            logger.error(f"Error determining DB need: {str(e)}")
            # Default to not using DB on error
            return False

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

    async def generate_answer(self, prompt: str) -> str:
        """Generate answer using current model"""
        try:
            model = self._get_current_model()
            logger.info(f"Using model: {self._current_provider}")
            response = await model.generate_answer(prompt)
            return response
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