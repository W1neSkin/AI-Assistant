from redis import Redis
import json
from typing import Optional, Dict, Any
import hashlib
import logging

logger = logging.getLogger(__name__)

class QueryCache:
    def __init__(self, host: str = "redis", port: int = 6379, ttl: int = 3600):
        """Initialize Redis cache with default TTL of 1 hour"""
        self.redis = Redis(host=host, port=port, decode_responses=True)
        self.ttl = ttl
    
    def _generate_key(self, question: str, max_results: int) -> str:
        """Generate a unique cache key for the query"""
        key_data = f"{question}:{max_results}"
        return f"query:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    async def get_cached_response(
        self, 
        question: str, 
        max_results: int
    ) -> Optional[Dict[str, Any]]:
        """Get cached response if it exists"""
        try:
            key = self._generate_key(question, max_results)
            cached = self.redis.get(key)
            if cached:
                logger.info(f"Cache hit for query: {question}")
                return json.loads(cached)
            logger.info(f"Cache miss for query: {question}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
            return None
    
    async def cache_response(
        self, 
        question: str, 
        max_results: int, 
        response: Dict[str, Any]
    ) -> None:
        """Cache the query response"""
        try:
            key = self._generate_key(question, max_results)
            self.redis.setex(
                key,
                self.ttl,
                json.dumps(response)
            )
            logger.info(f"Cached response for query: {question}")
        except Exception as e:
            logger.error(f"Error caching response: {str(e)}") 