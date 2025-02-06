from typing import Dict, Any, Optional, Literal
from app.llm.factory import create_llm
from app.llm.openai_llm import OpenAILLM
from app.llm.local_llm import LocalLLM
from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class LLMService:
    def __init__(self):
        self._current_provider = None  # Backing attribute for current_provider
        self.providers = {}
        self.initialized = False
        
    async def initialize(self):
        """Initialize LLM providers"""
        try:
            # Initialize OpenAI provider
            self.providers["openai"] = OpenAILLM()
            await self.providers["openai"].initialize()
            
            # Initialize local provider
            self.providers["local"] = LocalLLM()
            await self.providers["local"].initialize()
            
            # Set default provider using the backing attribute
            self._current_provider = "local"
            self.initialized = True
            logger.info(f"LLM Service initialized with default provider: {self._current_provider}")
            
        except Exception as e:
            logger.error(f"Error initializing LLM service: {str(e)}")
            raise
            
    async def change_provider(self, provider: str):
        """Change the current LLM provider"""
        logger.info(f"Attempting to change provider from {self.current_provider} to {provider}")

        if provider not in self.providers:
            logger.error(f"Invalid provider requested: {provider}. Available providers: {list(self.providers.keys())}")
            raise ValueError(f"Unknown provider: {provider}")

        self._current_provider = provider
        logger.info(f"Successfully changed provider to {provider}")
        
    async def generate_answer(self, prompt: str) -> str:
        """Generate answer using current provider"""
        if not self.current_provider:
            logger.error("No LLM provider selected")
            raise ValueError("No LLM provider selected")
            
        logger.info(f"Generating answer using provider: {self.current_provider}")
        provider = self.providers[self.current_provider]
        return await provider.generate_answer(prompt)

    @property
    def current_provider(self) -> str:
        """Get current LLM provider"""
        return self._current_provider

    @current_provider.setter
    def current_provider(self, value: str):
        """Set current LLM provider"""
        self._current_provider = value

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
            if not self.current_provider:
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

    def _get_current_model(self):
        """Get current LLM model instance"""
        if self.current_provider == "openai":
            if not self.providers.get("openai"):
                raise ValueError("OpenAI model not initialized")
            return self.providers["openai"]
        return self.providers[self.current_provider] 