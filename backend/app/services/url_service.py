import re
import aiohttp
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class URLService:
    def __init__(self, cache_service):
        self.cache_service = cache_service
        # Common URL patterns
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )

    async def extract_and_process_urls(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract and process URLs from text"""
        try:
            urls = await self.extract_urls(text)
            if not urls:
                return None

            contents = []
            errors = []

            for url in urls:
                content = await self.fetch_url_content(url)
                if content:
                    contents.append(content)
                else:
                    errors.append(f"Failed to fetch {url}")

            return {
                "urls": urls,
                "contents": contents,
                "errors": errors
            }
        except Exception as e:
            logger.error(f"Error processing URLs: {str(e)}")
            return None

    async def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        try:
            return self.url_pattern.findall(text)
        except Exception as e:
            logger.error(f"Error extracting URLs: {str(e)}")
            return []

    async def fetch_url_content(self, url: str) -> Optional[str]:
        """Fetch and cache URL content"""
        try:
            # Check cache first
            cached = await self.cache_service.get(url)
            if cached:
                return cached

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    content = await response.text()
                    # Cache the result
                    await self.cache_service.set(url, content)
                    return content
        except Exception as e:
            logger.error(f"Error fetching URL {url}: {str(e)}")
            return None

    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format and scheme"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except Exception:
            return False

    def _extract_text_from_html(self, html: str) -> str:
        """Extract meaningful text from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'header', 'footer', 'nav']):
                element.decompose()

            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            logger.error(f"Error extracting text from HTML: {str(e)}")
            return "" 