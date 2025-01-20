import logging
import json
from typing import Optional, Any
from redis.asyncio import Redis
from app.core.config import settings

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        self._redis = None
        self.ttl = settings.CACHE_TTL

    async def initialize(self):
        """Initialize Redis connection if not already initialized"""
        if not self._redis:
            try:
                self._redis = Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    decode_responses=True
                )
                # Test connection
                await self._redis.ping()
            except Exception as e:
                logger.error(f"Error initializing Redis connection: {str(e)}")
                raise

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        try:
            if not self._redis:
                await self.initialize()
            
            value = await self._redis.get(key)
            if value:
                logger.debug(f"Cache hit for key: {key}")
                return value
            
            logger.debug(f"Cache miss for key: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting from cache: {str(e)}")
            return None

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL"""
        try:
            if not self._redis:
                await self.initialize()
            
            ttl = ttl or self.ttl
            await self._redis.set(key, value, ex=ttl)
            logger.debug(f"Cached value for key: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            if not self._redis:
                await self.initialize()
            
            await self._redis.delete(key)
            logger.debug(f"Deleted cache for key: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
            return False

    async def clear(self) -> bool:
        """Clear all cached values"""
        try:
            if not self._redis:
                await self.initialize()
            
            await self._redis.flushdb()
            logger.info("Cleared all cache")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False

    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            self._redis = None 