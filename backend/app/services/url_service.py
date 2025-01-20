import logging
import re
import aiohttp
from typing import Dict, Any, Optional, Tuple, List
from bs4 import BeautifulSoup
from app.utils.cache import QueryCache
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class URLService:
    def __init__(self):
        self.cache = QueryCache()
        # Common URL patterns
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )

    async def extract_and_process_urls(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract and process URLs from text"""
        try:
            urls = self.extract_urls(text)
            if not urls:
                return None

            contents = []
            errors = []

            for url in urls:
                content, error = await self.fetch_url_content(url)
                if content:
                    contents.append(content)
                if error:
                    errors.append(error)

            return {
                "urls": urls,
                "contents": contents,
                "errors": errors
            }
        except Exception as e:
            logger.error(f"Error processing URLs: {str(e)}")
            return None

    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        try:
            return self.url_pattern.findall(text)
        except Exception as e:
            logger.error(f"Error extracting URLs: {str(e)}")
            return []

    async def fetch_url_content(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Fetch content from URL with caching"""
        try:
            # Check cache first
            cached_content = await self.cache.get(url)
            if cached_content:
                return cached_content, None

            # Validate URL
            if not self._is_valid_url(url):
                return None, f"Invalid URL: {url}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        return None, f"Failed to fetch {url}: Status {response.status}"

                    # Get content type
                    content_type = response.headers.get('content-type', '').lower()
                    
                    if 'text/html' in content_type:
                        html = await response.text()
                        content = self._extract_text_from_html(html)
                    else:
                        content = await response.text()

                    # Cache the result
                    await self.cache.set(url, content)
                    return content, None

        except aiohttp.ClientError as e:
            error_msg = f"Network error fetching {url}: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Error processing {url}: {str(e)}"
            logger.error(error_msg)
            return None, error_msg

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