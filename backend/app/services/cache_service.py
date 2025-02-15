from redis.asyncio import Redis

from app.utils.logger import setup_logger


logger = setup_logger(__name__)

class CacheService:
    def __init__(self):
        self._redis = None
        self.host = 'redis'
        self.port = 6379

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self._redis = Redis(
                host=self.host,
                port=self.port,
                decode_responses=True
            )
            # Test connection
            await self._redis.ping()
            logger.info("Redis connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {str(e)}")
            raise
        
    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def get(self, key: str) -> str:
        """Get value from Redis"""
        try:
            if not self._redis:
                await self.initialize()
            return await self._redis.get(key)
        except Exception as e:
            logger.error(f"Redis get error: {str(e)}")
            return None

    async def set(self, key: str, value: str, expire: int = None) -> bool:
        """Set value in Redis"""
        try:
            if not self._redis:
                await self.initialize()
            await self._redis.set(key, value, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {str(e)}")
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