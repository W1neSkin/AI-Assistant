from typing import Optional, List

from app.utils.url_handler import URLHandler
from app.utils.logger import setup_logger


logger = setup_logger(__name__)

class URLService:
    def __init__(self, cache_service):
        self.url_handler = URLHandler(cache_service)

    async def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        return self.url_handler.extract_urls(text)

    async def fetch_url_content(self, url: str) -> Optional[str]:
        """Fetch and cache URL content"""
        content, error = await self.url_handler.fetch_url_content(url)
        if error:
            logger.error(error)
        return content 