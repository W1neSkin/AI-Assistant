import pytest
from unittest.mock import AsyncMock, patch
from app.services.cache_service import CacheService

@pytest.mark.asyncio
async def test_initialize():
    service = CacheService()
    fake_redis = AsyncMock()
    fake_redis.ping.return_value = True
    # Patch the Redis constructor so that CacheService.initialize() returns our fake redis client.
    with patch("app.services.cache_service.Redis", return_value=fake_redis):
        await service.initialize()
        # Verify that _redis was set and ping was called.
        fake_redis.ping.assert_awaited()
        assert service._redis == fake_redis

@pytest.mark.asyncio
async def test_close():
    service = CacheService()
    fake_redis = AsyncMock()
    fake_redis.close.return_value = None
    service._redis = fake_redis
    await service.close()
    fake_redis.close.assert_awaited()
    # After closing, _redis should be set to None.
    assert service._redis is None

@pytest.mark.asyncio
async def test_get():
    service = CacheService()
    fake_redis = AsyncMock()
    fake_redis.get.return_value = "cached_value"
    # Patch Redis so that the first call to get() initializes _redis.
    with patch("app.services.cache_service.Redis", return_value=fake_redis):
        value = await service.get("key1")
        fake_redis.get.assert_awaited_with("key1")
        assert value == "cached_value"

@pytest.mark.asyncio
async def test_set():
    service = CacheService()
    fake_redis = AsyncMock()
    # Simulate a successful set operation.
    fake_redis.set.return_value = None
    with patch("app.services.cache_service.Redis", return_value=fake_redis):
        result = await service.set("key1", "value1")
        fake_redis.set.assert_awaited_with("key1", "value1", ex=None)
        assert result is True

@pytest.mark.asyncio
async def test_delete():
    service = CacheService()
    fake_redis = AsyncMock()
    fake_redis.delete.return_value = None
    with patch("app.services.cache_service.Redis", return_value=fake_redis):
        result = await service.delete("key1")
        fake_redis.delete.assert_awaited_with("key1")
        assert result is True

@pytest.mark.asyncio
async def test_clear():
    service = CacheService()
    fake_redis = AsyncMock()
    fake_redis.flushdb.return_value = None
    with patch("app.services.cache_service.Redis", return_value=fake_redis):
        result = await service.clear()
        fake_redis.flushdb.assert_awaited()
        assert result is True 