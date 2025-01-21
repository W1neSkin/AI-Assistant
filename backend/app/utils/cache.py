import redis.asyncio as redis
from typing import Optional, Any, Dict
import json
import hashlib
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class QueryCache:
    def __init__(self, host: str = "redis", port: int = 6379, ttl: int = 3600):
        """Initialize Redis cache with default TTL of 1 hour"""
        self.redis = redis.from_url(f"redis://{host}:{port}", decode_responses=True)
        self.ttl = ttl
    
    def _generate_key(self, question: str) -> str:
        """Generate a unique cache key for the query"""
        key_data = f"query:{question}"
        return f"query:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    async def get(
        self, 
        question: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached response if it exists"""
        try:
            key = self._generate_key(question)
            cached = await self.redis.get(key)
            if cached:
                logger.info(f"Cache hit for query: {question}")
                return json.loads(cached)
            logger.info(f"Cache miss for query: {question}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
            return None
    
    async def set(
        self, 
        question: str, 
        response: Dict[str, Any]
    ) -> None:
        """Cache the query response"""
        try:
            key = self._generate_key(question)
            await self.redis.setex(
                key,
                self.ttl,
                json.dumps(response)
            )
            logger.info(f"Cached response for query: {question}")
        except Exception as e:
            logger.error(f"Error caching response: {str(e)}") 