from typing import Dict, Any
import re
import logging

logger = logging.getLogger(__name__)

class QueryOptimizer:
    @classmethod
    def optimize_query(cls, query_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize SQL query for better performance"""
        query = query_dict['query']
        params = query_dict['params']

        optimizations = [
            cls._optimize_exists_vs_in,
            cls._optimize_correlated_subqueries,
            cls._optimize_derived_tables,
            cls._add_indexes_hint,
            cls._optimize_group_by,
            cls._optimize_joins
        ]

        optimized_query = query
        for optimize_func in optimizations:
            optimized_query = optimize_func(optimized_query)

        return {
            'query': optimized_query,
            'params': params,
            'optimization_applied': optimized_query != query
        }

    @classmethod
    def _optimize_exists_vs_in(cls, query: str) -> str:
        """Replace IN with EXISTS for better performance with large datasets"""
        query_lower = query.lower()
        if 'in (select' in query_lower:
            # Convert IN subquery to EXISTS
            pattern = r'in\s*\(\s*select\s+([^)]+)\)'
            replacement = r'EXISTS (SELECT 1 FROM \1 WHERE \0)'
            return re.sub(pattern, replacement, query, flags=re.IGNORECASE)
        return query

    @classmethod
    def _optimize_correlated_subqueries(cls, query: str) -> str:
        """Replace correlated subqueries with JOINs where possible"""
        if re.search(r'\(\s*select.*where.*=\s*\w+\.\w+\)', query, re.IGNORECASE | re.DOTALL):
            # Example transformation for common correlated subquery patterns
            patterns_and_replacements = [
                # Pattern for COUNT subquery
                (
                    r'SELECT\s+COUNT\(\*\)\s+FROM\s+(\w+)\s+WHERE\s+(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)',
                    r'COUNT(\1.*) FROM \1 GROUP BY \2.\3'
                ),
                # Pattern for SUM subquery
                (
                    r'SELECT\s+SUM\((\w+)\)\s+FROM\s+(\w+)\s+WHERE\s+(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)',
                    r'SUM(\2.\1) FROM \2 GROUP BY \3.\4'
                )
            ]
            
            optimized_query = query
            for pattern, replacement in patterns_and_replacements:
                optimized_query = re.sub(pattern, replacement, optimized_query, flags=re.IGNORECASE)
            return optimized_query
        return query

    @classmethod
    def _optimize_derived_tables(cls, query: str) -> str:
        """Optimize derived tables by pushing down predicates"""
        if re.search(r'FROM\s*\(\s*SELECT', query, re.IGNORECASE):
            # Add WHERE conditions before GROUP BY in derived tables
            pattern = r'FROM\s*\(\s*SELECT(.*?)GROUP BY(.*?)\)(.*?)WHERE(.*?)'
            replacement = r'FROM (SELECT\1WHERE\4 GROUP BY\2)\3'
            return re.sub(pattern, replacement, query, flags=re.IGNORECASE | re.DOTALL)
        return query

    @classmethod
    def _add_indexes_hint(cls, query: str) -> str:
        """Add index hints for better query planner decisions"""
        # Common index patterns for our schema
        index_hints = {
            'clients': ['customer_id', 'customer_type'],
            'subscriptions': ['customer_id', 'subscription_id'],
            'subscription_charges': ['subscription_id', 'charge_datetime'],
            'addresses': ['customer_id', 'city']
        }

        optimized_query = query
        for table, columns in index_hints.items():
            if table in query.lower():
                # Add index hints if table is used
                hint = f"/*+ INDEX({table} {' '.join(columns)}) */"
                optimized_query = re.sub(
                    f'FROM\\s+{table}\\b',
                    f'FROM {hint} {table}',
                    optimized_query,
                    flags=re.IGNORECASE
                )

        return optimized_query

    @classmethod
    def _optimize_group_by(cls, query: str) -> str:
        """Optimize GROUP BY operations"""
        if 'group by' in query.lower():
            # Add parallel hint for large group operations
            return f"/*+ PARALLEL(4) */ {query}"
        return query

    @classmethod
    def _optimize_joins(cls, query: str) -> str:
        """Optimize JOIN operations"""
        # Replace implicit joins with explicit INNER JOIN
        pattern = r'FROM\s+(\w+)\s*,\s*(\w+)\s+WHERE\s+(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)'
        replacement = r'FROM \1 INNER JOIN \2 ON \3.\4 = \5.\6'
        
        # Add join hints for large tables
        join_hints = {
            'subscription_charges': 'HASH JOIN',
            'subscriptions': 'MERGE JOIN'
        }
        
        optimized_query = re.sub(pattern, replacement, query, flags=re.IGNORECASE)
        
        for table, hint in join_hints.items():
            if table in query.lower():
                optimized_query = f"/*+ {hint} */ {optimized_query}"
                
        return optimized_query 