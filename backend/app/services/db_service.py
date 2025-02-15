import hashlib
import asyncpg
import re
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.utils.cache import QueryCache
from app.utils.logger import setup_logger
from app.core.config import settings


logger = setup_logger(__name__)

class DatabaseService:
    DANGEROUS_KEYWORDS = {
        'alter', 'drop', 'delete', 'truncate', 'update', 'insert', 
        'grant', 'revoke', 'create', 'exec', 'execute'
    }

    def __init__(self):
        self.engine = create_async_engine(
            f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}",
            echo=False
        )
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.cache = QueryCache()
        self.schema_cache_key = "db_schema"
        self.schema_cache_ttl = 3600  # 1 hour
        self._pool = None
        self._schema = None

    async def initialize(self):
        """Initialize database connection pool"""
        try:
            if not self._pool:
                self._pool = await asyncpg.create_pool(
                    user=settings.POSTGRES_USER,
                    password=settings.POSTGRES_PASSWORD,
                    database=settings.POSTGRES_DB,
                    host=settings.POSTGRES_HOST,
                    port=settings.POSTGRES_PORT
                )
                logger.info("Database connection pool initialized")
                
                # Cache the schema on initialization
                self._schema = await self.get_schema()
        except Exception as e:
            logger.error(f"Error initializing database service: {str(e)}")
            raise

    async def close(self):
        """Close database connection pool"""
        if self._pool:
            await self._pool.close()
            logger.info("Database connection pool closed")

    async def get_schema(self) -> str:
        """Get database schema"""
        try:
            if self._schema:
                return self._schema

            async with self._pool.acquire() as conn:
                # Get tables
                tables = await conn.fetch("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                
                schema_parts = []
                for table in tables:
                    table_name = table['table_name']
                    # Get columns for each table
                    columns = await conn.fetch("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_name = $1
                    """, table_name)
                    
                    schema_parts.append(f"Table: {table_name}")
                    for col in columns:
                        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                        schema_parts.append(
                            f"  {col['column_name']}: {col['data_type']} {nullable}"
                        )
                    schema_parts.append("")  # Empty line between tables
                
                self._schema = "\n".join(schema_parts)
                return self._schema

        except Exception as e:
            logger.error(f"Error getting schema: {str(e)}")
            raise

    def _generate_cache_key(self, query: str) -> str:
        """Generate cache key for query"""
        return f"query:{hashlib.md5(query.encode()).hexdigest()}"

    async def execute_query(self, query: str) -> Any:
        """Execute a SQL query with safety checks"""
        # Convert to lowercase for case-insensitive check
        query_lower = query.lower()
        
        # Check for dangerous keywords
        for keyword in self.DANGEROUS_KEYWORDS:
            # Use word boundaries to match only whole words
            if re.search(rf'\b{keyword}\b', query_lower):
                raise ValueError(f"Dangerous SQL keyword detected: {keyword}")

        # Only allow SELECT queries
        if not query_lower.strip().startswith('select'):
            raise ValueError("Only SELECT queries are allowed")

        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(text(query))
                return result.fetchall()
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            raise 