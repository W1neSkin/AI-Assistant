from typing import Optional, Dict, Any, List
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class MockIndexService:
    async def initialize(self):
        pass
        
    async def query(self, question: str, max_results: int = 5) -> List[Dict]:
        return [{
            "text": "This is a test document content",
            "filename": "test.pdf",
            "similarity_score": 0.95
        }]

class MockURLService:
    async def extract_urls(self, text: str) -> list:
        if "http" in text:
            return ["http://test.com"]
        return []

    async def fetch_url_content(self, url: str) -> Optional[str]:
        return "Test URL content"

class MockCacheService:
    async def get(self, key: str) -> Optional[Dict]:
        return None

    async def set(self, key: str, value: Any, expire: int = None) -> bool:
        return True

class MockLanguageService:
    def format_prompt(self, question: str, context: str = "") -> str:
        return f"Question: {question}\nContext: {context}"

class MockSettingsService:
    async def get_settings(self) -> Dict:
        return {
            "use_cloud": False,
            "enable_document_search": True,
            "handle_urls": True,
            "check_db": True
        }

class MockUser:
    def __init__(self):
        self.use_cloud = False
        self.enable_document_search = True
        self.handle_urls = True
        self.check_db = True

class MockLLMService:
    async def initialize(self):
        self.initialized = True
        self.current_provider = "local"
        
    async def generate_answer(self, prompt: str) -> str:
        return "This is a mock LLM response"
        
    async def change_provider(self, provider: str):
        self.current_provider = provider

class MockServiceContainer:
    async def initialize_for_tests(self):
        self.llm_service = MockLLMService()
        self.index_service = MockIndexService()
        await self.llm_service.initialize()
        await self.index_service.initialize() 