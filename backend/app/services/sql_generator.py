from typing import Optional, List, Dict, Any
from app.utils.exceptions import SQLGenerationError
from app.utils.cache import QueryCache
from app.utils.query_optimizer import QueryOptimizer
from app.utils.logger import setup_logger
import hashlib
import re

logger = setup_logger(__name__)

class SQLGenerator:
    def __init__(self, schema: str, llm_service=None):
        self.schema = schema
        self.cache = QueryCache()
        self.cache_ttl = 3600  # 1 hour
        self.optimizer = QueryOptimizer()
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

    def _get_query_examples(self, features: List[str]) -> str:
        examples = []
        
        if 'aggregation' in features:
            examples.append("""
            -- Aggregation example
            SELECT 
                c.customer_group,
                COUNT(DISTINCT c.customer_id) as customer_count,
                AVG(COALESCE(sc.charge_amount, 0)) as avg_charge
            FROM clients c
            LEFT JOIN subscriptions s ON c.customer_id = s.customer_id
            LEFT JOIN subscription_charges sc ON s.subscription_id = sc.subscription_id
            GROUP BY c.customer_group;
            """)
            
        if 'joins' in features:
            examples.append("""
            -- Complex join example
            SELECT 
                c.customer_id,
                c.first_name || ' ' || c.last_name as full_name,
                a.city,
                s.rateplan,
                sc.charge_amount
            FROM clients c
            JOIN addresses a ON c.customer_id = a.customer_id
            LEFT JOIN subscriptions s ON c.customer_id = s.customer_id
            LEFT JOIN subscription_charges sc ON s.subscription_id = sc.subscription_id;
            """)
            
        if 'date_range' in features:
            examples.append("""
            -- Date range example
            SELECT 
                DATE_TRUNC('month', sc.charge_datetime) as month,
                SUM(sc.charge_amount) as total_charges
            FROM subscription_charges sc
            WHERE sc.charge_datetime BETWEEN 
                CURRENT_DATE - INTERVAL '1 year' AND CURRENT_DATE
            GROUP BY DATE_TRUNC('month', sc.charge_datetime)
            ORDER BY month;
            """)
            
        if 'ranking' in features:
            examples.append("""
            -- Ranking example
            WITH ranked_customers AS (
                SELECT 
                    c.customer_id,
                    c.first_name || ' ' || c.last_name as full_name,
                    SUM(sc.charge_amount) as total_spent,
                    RANK() OVER (ORDER BY SUM(sc.charge_amount) DESC) as rank
                FROM clients c
                JOIN subscriptions s ON c.customer_id = s.customer_id
                JOIN subscription_charges sc ON s.subscription_id = sc.subscription_id
                GROUP BY c.customer_id, c.first_name, c.last_name
            )
            SELECT * FROM ranked_customers WHERE rank <= 10;
            """)
            
        if 'subquery' in features:
            examples.append("""
            -- Subquery examples
            
            -- Correlated subquery
            SELECT 
                c.customer_id,
                c.first_name || ' ' || c.last_name as full_name,
                (
                    SELECT COUNT(*)
                    FROM subscriptions s
                    WHERE s.customer_id = c.customer_id
                ) as subscription_count,
                (
                    SELECT COALESCE(SUM(sc.charge_amount), 0)
                    FROM subscription_charges sc
                    JOIN subscriptions s ON s.subscription_id = sc.subscription_id
                    WHERE s.customer_id = c.customer_id
                ) as total_charges
            FROM clients c
            WHERE c.customer_type = 'premium';
            
            -- Derived table
            SELECT 
                a.city,
                customer_stats.customer_count,
                customer_stats.avg_charges
            FROM (
                SELECT 
                    c.customer_id,
                    MAX(a.city) as city,
                    COUNT(*) as customer_count,
                    AVG(sc.charge_amount) as avg_charges
                FROM clients c
                JOIN addresses a ON c.customer_id = a.customer_id
                JOIN subscriptions s ON c.customer_id = s.customer_id
                JOIN subscription_charges sc ON s.subscription_id = sc.subscription_id
                GROUP BY c.customer_id
            ) customer_stats
            JOIN addresses a ON a.customer_id = customer_stats.customer_id
            GROUP BY a.city;
            """)

        return "\n".join(examples) if examples else "-- No specific examples needed for this query type"

    async def generate_query(self, question: str) -> Dict[str, Any]:
        """Generate SQL query from natural language question with caching"""
        try:
            if not self.llm_service:
                await self.initialize()

            cache_key = self._generate_cache_key(question)
            
            # Check cache first
            cached_query = await self.cache.get(cache_key)
            if cached_query:
                return cached_query

            # Log schema size
            logger.debug(f"Schema size (chars): {len(self.schema)}")
            logger.debug(f"Schema: {self.schema}")

            # Generate SQL query
            prompt = f"""
            Given the following database schema:
            {self.schema}
            
            Generate a SQL query for this question:
            {question}
            
            Rules: Use proper PostgreSQL syntax, only schema tables/columns, 
            single quotes for strings, LIMIT 1000, handle NULLs with COALESCE.
            
            SQL Query:
            """
            
            # Log prompt details
            logger.debug(f"Question: {question}")
            logger.debug(f"Total prompt size (chars): {len(prompt)}")
            logger.debug(f"Prompt: {prompt}")

            response = await self.llm_service.generate_answer(prompt)
            sql_query = response["answer"] if isinstance(response, dict) else response
            logger.info(f"Generated SQL query: {sql_query}")
            
            # Cache the result
            await self.cache.set(cache_key, sql_query)
            
            return sql_query

        except Exception as e:
            logger.error(f"Error generating SQL query for question '{question}': {str(e)}")
            raise SQLGenerationError(f"Failed to generate SQL: {str(e)}") 