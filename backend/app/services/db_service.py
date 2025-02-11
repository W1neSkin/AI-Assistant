from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.utils.exceptions import DatabaseQueryError, SchemaError
from app.utils.cache import QueryCache
from app.utils.sql_sanitizer import SQLSanitizer
from app.utils.logger import setup_logger
from typing import List, Dict, Any, Union
import hashlib
import asyncpg
from app.core.config import settings
import re

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

    async def execute_query(
        self,
        query: Union[str, Dict[str, Any]],
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Execute raw SQL query and return results with caching"""
        try:
            # Handle query input
            if isinstance(query, dict):
                query_text = query['query']
                params = query['params']
            else:
                # For direct string queries (internal use only)
                sanitizer = SQLSanitizer()
                sanitized_query = sanitizer.sanitize_query(query)
                # Extract parameters if any
                query_text, params = sanitizer.extract_params(sanitized_query)
                logger.info(f"Sanitized query: {query_text}")
                logger.info(f"Params: {params}")

            # Check cache first if enabled
            if use_cache:
                cache_key = self._generate_cache_key(f"{query_text}:{str(params)}")
                cached_result = await self.cache.get(cache_key)
                if cached_result:
                    logger.info(f"Cache hit for query: {query_text[:100]}...")
                    return cached_result

            async with self.async_session() as session:
                try:
                    # Convert params to list of dictionaries for SQLAlchemy
                    if params:
                        # Replace $1, $2 style params with :param_0, :param_1 style
                        for i in range(len(params)):
                            query_text = query_text.replace(f"${i+1}", f":param_{i}")
                        param_dict = {f"param_{i}": val for i, val in enumerate(params)}
                        logger.info(f"Executing query with params: {param_dict}")
                        result = await session.execute(text(query_text), param_dict)
                    else:
                        result = await session.execute(text(query_text))
                    
                    data = [dict(row._mapping) for row in result]

                    # Cache the results if enabled
                    if use_cache:
                        await self.cache.set(cache_key, data)

                    return data
                except Exception as e:
                    logger.error(
                        f"Query execution error: {str(e)}\n"
                        f"Query: {query_text}\n"
                        f"Params: {params}"
                    )
                    raise DatabaseQueryError(f"Failed to execute query: {str(e)}")

        except Exception as e:
            logger.error(f"Database service error: {str(e)}")
            raise DatabaseQueryError(str(e))

    async def get_table_schema(self) -> str:
        """Get database schema for context with caching"""
        try:
            # Check cache first
            cached_schema = await self.cache.get(self.schema_cache_key)
            if cached_schema:
                return cached_schema

            schema_query = """
            SELECT 
                table_name,
                string_agg(
                    column_name || ' ' || data_type || 
                    CASE 
                        WHEN is_nullable = 'YES' THEN ' NULL'
                        ELSE ' NOT NULL'
                    END,
                    ', '
                ) as columns,
                obj_description(
                    (table_schema || '.' || table_name)::regclass, 'pg_class'
                ) as table_description
            FROM information_schema.columns
            WHERE table_schema = 'public'
            GROUP BY table_name;
            """
            
            tables = await self.execute_query(schema_query, use_cache=False)
            
            schema_text = "\n\n".join([
                f"Table: {t['table_name']}\n" +
                (f"Description: {t['table_description']}\n" if t['table_description'] else "") +
                f"Columns: {t['columns']}"
                for t in tables
            ])

            # Cache the schema
            await self.cache.set(self.schema_cache_key, schema_text, self.schema_cache_ttl)
            
            return schema_text

        except Exception as e:
            logger.error(f"Schema retrieval error: {str(e)}")
            raise SchemaError(f"Failed to retrieve database schema: {str(e)}")

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