import aiohttp
import hashlib
from bs4 import BeautifulSoup
from app.core.config import settings
from app.utils.cache import QueryCache
from app.utils.logger import setup_logger
import re
from typing import Optional, Tuple
from urllib.parse import urlparse

logger = setup_logger(__name__)

class URLHandler:
    def __init__(self, cache: QueryCache):
        self.cache = cache
        
    def extract_urls(self, text: str) -> list[str]:
        """Extract URLs from text."""
        # More precise URL regex pattern that avoids suspicious character ranges
        # This pattern uses specific character classes for different parts of a URL
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
        return re.findall(url_pattern, text)
    
    def _generate_cache_key(self, url: str) -> str:
        """Generate cache key for URL content."""
        return f"url:{hashlib.md5(url.encode()).hexdigest()}"
    
    async def fetch_url_content(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Fetch and parse URL content with caching."""
        try:
            # Check cache first
            cache_key = self._generate_cache_key(url)
            cached_content = await self.cache.get(cache_key)
            if cached_content:
                return cached_content.get('content'), None
            
            # Validate URL
            parsed_url = urlparse(url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                return None, f"Invalid URL: {url}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, 
                    timeout=settings.URL_FETCH_TIMEOUT,
                    raise_for_status=True
                ) as response:
                    # Check content type
                    content_type = response.headers.get('content-type', '')
                    if not content_type.startswith('text/html'):
                        return None, f"Unsupported content type: {content_type}"
                    
                    # Check content length
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > settings.MAX_URL_CONTENT_SIZE:
                        return None, f"Content too large: {content_length} bytes"
                    
                    html = await response.text()
                    
                    # Parse HTML
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Remove unwanted elements
                    for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                        element.decompose()
                    
                    # Extract text while preserving some structure
                    content = []
                    for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
                        text = element.get_text(strip=True)
                        if text:
                            content.append(text)
                    
                    text_content = '\n'.join(content)
                    
                    # Cache the content
                    await self.cache.set(
                        cache_key,
                        {'content': text_content}
                    )
                    
                    return text_content, None
                    
        except aiohttp.ClientError as e:
            error_msg = f"Failed to fetch URL {url}: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Error processing URL {url}: {str(e)}"
            logger.error(error_msg)
            return None, error_msg 