from typing import List
from app.utils.exceptions import SQLGenerationError
from app.utils.cache import QueryCache
from app.utils.logger import setup_logger
from app.utils.prompt_generator import PromptGenerator
import hashlib
import re


logger = setup_logger(__name__)

class SQLGenerator:
    def __init__(self, schema: str, llm_service=None):
        self.schema = schema
        self.cache = QueryCache()
        self.cache_ttl = 3600  # 1 hour
        self.llm_service = llm_service

    async def initialize(self):
        """Initialize SQLGenerator"""
        if not self.llm_service:
            # Import here to avoid circular import
            from app.core.service_container import ServiceContainer
            container = ServiceContainer.get_instance()
            self.llm_service = container.llm_service

    def _generate_cache_key(self, question: str) -> str:
        """Generate cache key for question"""
        return f"sql_gen:{hashlib.md5(question.encode()).hexdigest()}"

    def _validate_tables(self, query: str) -> None:
        """Validate that query only uses tables from schema"""
        allowed_tables = {
            line.split(':')[0].strip().lower()
            for line in self.schema.split('\n')
            if line.strip().startswith('Table:')
        }
        
        # Extract table names from query
        tables_in_query = set(
            re.findall(r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)', query.lower()) +
            re.findall(r'join\s+([a-zA-Z_][a-zA-Z0-9_]*)', query.lower())
        )
        
        invalid_tables = tables_in_query - allowed_tables
        if invalid_tables:
            raise SQLGenerationError(f"Query uses unauthorized tables: {invalid_tables}")
 
    async def generate_query(self, question: str) -> str:
        """Generate SQL query from natural language question"""
        logger.info(f"Generating SQL query for question: {question}")
        
        prompt = PromptGenerator.format_prompt_for_sql(question, self.schema)

        response = await self.llm_service.generate_answer(prompt)
        # Remove any markdown code blocks or explanatory text
        query = response.replace('```sql', '').replace('```', '').strip()
        # Remove any "here's the query:" type prefixes
        query = re.sub(r'^.*?SELECT', 'SELECT', query, flags=re.DOTALL)
        
        # Basic validation
        if not query.lower().startswith('select'):
            logger.error(f"Invalid query generated - does not start with SELECT: {query}")
            raise ValueError("Generated query must start with SELECT")
        
        return query 