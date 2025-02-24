import pytest
from unittest.mock import patch, AsyncMock
from app.services.db_service import DatabaseService
from contextlib import asynccontextmanager

# Test for initialize: We patch asyncpg.create_pool and get_schema.
@pytest.mark.asyncio
async def test_initialize():
    fake_pool = AsyncMock()
    # Create a dummy async context manager for pool.acquire()
    dummy_cm = AsyncMock()
    dummy_cm.__aenter__.return_value = AsyncMock()
    fake_pool.acquire.return_value = dummy_cm
    fake_pool.close = AsyncMock()

    # Patch get_schema to return a fake schema string.
    with patch('app.services.db_service.asyncpg.create_pool', new=AsyncMock(return_value=fake_pool)), \
         patch.object(DatabaseService, 'get_schema', new=AsyncMock(return_value="fake schema")):
        service = DatabaseService()
        await service.initialize()
        # Verify that the pool and schema are set correctly.
        assert service._pool == fake_pool
        assert service._schema == "fake schema"

# Test for close: Ensure that _pool.close() is awaited.
@pytest.mark.asyncio
async def test_close():
    service = DatabaseService()
    service._pool = AsyncMock()
    service._pool.close = AsyncMock()
    await service.close()
    service._pool.close.assert_awaited_once()

# Test for get_schema: Simulate a connection with one table and two columns.
@pytest.mark.asyncio
async def test_get_schema():
    service = DatabaseService()
    fake_pool = AsyncMock()
    fake_conn = AsyncMock()
    fake_conn.fetch.side_effect = [
        [{'table_name': 'users'}],  # First fetch returns table list.
        [                           # Second fetch returns columns for 'users'.
            {'column_name': 'id', 'data_type': 'integer', 'is_nullable': 'NO'},
            {'column_name': 'email', 'data_type': 'varchar', 'is_nullable': 'YES'},
        ]
    ]

    # Define an async context manager for fake_pool.acquire()
    @asynccontextmanager
    async def fake_acquire():
        yield fake_conn

    # Instead of setting .return_value on a coroutine mock,
    # override the acquire method to return our async context manager.
    fake_pool.acquire = lambda: fake_acquire()
    service._pool = fake_pool
    service._schema = None  # Ensure schema is not cached.
    
    schema = await service.get_schema()
    # Verify that the generated schema string contains expected substrings.
    assert "Table: users" in schema
    assert "id: integer NOT NULL" in schema
    assert "email: varchar NULL" in schema

# Test for execute_query with a valid SELECT query.
@pytest.mark.asyncio
async def test_execute_query_select():
    service = DatabaseService()
    # Create a fake engine and connection.
    fake_engine = AsyncMock()
    fake_conn = AsyncMock()
    fake_result = AsyncMock()
    fake_result.fetchall = lambda: [('user1', 'email1')]
    fake_conn.execute.return_value = fake_result

    # Define an async context manager for fake_engine.connect()
    @asynccontextmanager
    async def fake_connect():
        yield fake_conn

    # Override the engine.connect method to return our async context manager.
    fake_engine.connect = lambda: fake_connect()
    service.engine = fake_engine

    query = "SELECT * FROM users"
    result = await service.execute_query(query)
    assert result == [('user1', 'email1')]

# Test for execute_query to ensure that non-SELECT queries or queries with dangerous keywords raise ValueError.
@pytest.mark.asyncio
async def test_execute_query_invalid():
    service = DatabaseService()
    invalid_queries = [
        "DROP TABLE users",  # Does not start with SELECT & is dangerous.
        "DELETE FROM users", 
        "INSERT INTO users VALUES (1)",
        "UPDATE users SET name='test'",
    ]
    for query in invalid_queries:
        with pytest.raises(ValueError):
            await service.execute_query(query)

# Test for execute_query with dangerous keywords in a SELECT query.
@pytest.mark.asyncio
async def test_execute_query_dangerous_keywords():
    service = DatabaseService()
    query = "SELECT * FROM users; DROP TABLE users;"
    with pytest.raises(ValueError, match="Dangerous SQL keyword detected"):
        await service.execute_query(query) 