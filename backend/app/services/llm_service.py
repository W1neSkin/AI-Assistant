from app.llm.cloud_llm import CloudLLM
from app.llm.local_llm import LocalLLM
from app.llm.base_llm import BaseLLM
from app.core.config import settings
from app.utils.logger import setup_logger
from app.utils.prompt_generator import PromptGenerator


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

    async def close(self):
        """Close LLM providers"""
        for provider in self.providers.values():
            await provider.close()
            
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
        prompt = PromptGenerator.format_prompt_for_is_question(question)
        
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

    def get_provider(self) -> BaseLLM:
        """Get current LLM provider instance"""
        if self._current_provider == "cloud":
            return self.providers["cloud"]
        return self.providers[self.current_provider] 