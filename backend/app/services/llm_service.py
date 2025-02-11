from app.llm.cloud_llm import CloudLLM
from app.llm.local_llm import LocalLLM
from app.llm.base_llm import BaseLLM
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
            # Initialize cloud provider
            self.providers["cloud"] = CloudLLM()
            await self.providers["cloud"].initialize()
            
            # Initialize local provider
            self.providers["local"] = LocalLLM()
            await self.providers["local"].initialize()
            
            # Set default provider using the backing attribute
            self._current_provider = settings.LLM_PROVIDER
            logger.info(f"Using {self._current_provider} as default LLM provider")
            
        except Exception as e:
            logger.error(f"Error initializing LLM service: {str(e)}")
            raise
            
    async def change_provider(self, provider: str):
        """Change LLM provider"""
        if provider not in self.providers:
            raise ValueError(f"Invalid provider: {provider}")
        self._current_provider = provider
        logger.info(f"Switched to {provider} provider")
        
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
        model = self.get_provider()
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
            model = self.get_provider()
            return await model.generate_answer(prompt)
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            raise

    def get_provider(self) -> BaseLLM:
        """Get current LLM provider instance"""
        if self._current_provider == "cloud":
            return self.providers["cloud"]
        return self.providers[self.current_provider] 