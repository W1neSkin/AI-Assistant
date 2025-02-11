import re
from typing import List, Any, Tuple
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class SQLSanitizer:
    # SQL keywords that might be used in injection attacks
    DANGEROUS_KEYWORDS = {
        'delete', 'drop', 'truncate', 'alter', 'update', 'insert', 'grant', 
        'revoke', 'commit', 'rollback', 'create', 'exec', 'execute',
        'begin', 'declare', '--', 'xp_', 'sp_'
    }

    def sanitize_query(self, query: str) -> str:
        """Sanitize SQL query by removing dangerous patterns"""
        # Clean up the query
        query = query.strip()
        if query.endswith(';'):
            query = query[:-1]  # Remove trailing semicolon
        
        # Convert to lowercase for checking
        query_lower = query.lower()
        
        # Check for dangerous keywords
        for keyword in self.DANGEROUS_KEYWORDS:
            # Use word boundaries to match only whole words
            if re.search(rf'\b{keyword}\b', query_lower):
                raise ValueError(f"Dangerous SQL keyword detected: {keyword}")
        
        # Ensure query starts with SELECT
        if not query_lower.strip().startswith('select'):
            raise ValueError("Only SELECT queries are allowed")
        
        # Add LIMIT if not present
        if 'limit' not in query_lower:
            query = f"{query} LIMIT 1000"
        
        return query

    def extract_params(self, query: str) -> Tuple[str, List[Any]]:
        """Convert string literals to parameters"""
        params = []
        
        def replace_literal(match):
            value = match.group(1)
            # Handle different value types
            try:
                # Try to convert to number if possible
                if value.isdigit():
                    params.append(int(value))
                elif value.replace('.', '').isdigit():
                    params.append(float(value))
                else:
                    params.append(value)
            except ValueError:
                params.append(value)
            return f"${len(params)}"
        
        # Replace string literals with parameters
        parameterized_query = re.sub(
            r"'([^']*)'",  # Match string literals
            replace_literal,
            query
        )
        
        # Convert params list to tuple for asyncpg
        return parameterized_query, tuple(params)

    def validate_complex_query(cls, query: str) -> None:
        """Validate complex query structure"""
        query_lower = query.lower()
        
        # Validate subquery structure
        def validate_subquery_balance(query: str) -> bool:
            """Check if subquery parentheses are properly balanced"""
            stack = []
            in_string = False
            string_char = None
            
            for char in query:
                if char in ["'", '"'] and not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char and in_string:
                    in_string = False
                elif not in_string:
                    if char == '(':
                        stack.append(char)
                    elif char == ')':
                        if not stack:
                            return False
                        stack.pop()
            
            return len(stack) == 0
        
        # Check subquery syntax
        if '(' in query:
            if not validate_subquery_balance(query):
                raise ValueError("Unbalanced parentheses in subquery")
            
            # Check for common subquery patterns
            subquery_patterns = [
                r'\(\s*select\s+.+?\)', # Basic subquery
                r'from\s+\(\s*select\s+.+?\)', # Derived table
                r'in\s+\(\s*select\s+.+?\)', # IN subquery
                r'exists\s*\(\s*select\s+.+?\)', # EXISTS subquery
            ]
            
            has_valid_subquery = any(
                re.search(pattern, query_lower, re.DOTALL)
                for pattern in subquery_patterns
            )
            
            if not has_valid_subquery:
                raise ValueError("Invalid subquery syntax")
        
        # Check for proper WITH clause syntax
        if 'with' in query_lower and not re.match(r'\s*with\s+\w+\s+as\s*\(', query_lower):
            raise ValueError("Invalid WITH clause syntax")
            
        # Validate GROUP BY with aggregates
        if 'group by' in query_lower:
            aggregates = ['count', 'sum', 'avg', 'max', 'min']
            has_aggregate = any(agg in query_lower for agg in aggregates)
            if not has_aggregate:
                raise ValueError("GROUP BY should be used with aggregate functions")
                
        # Validate window functions
        if 'over' in query_lower:
            if not re.search(r'over\s*\([^)]+\)', query_lower):
                raise ValueError("Invalid window function syntax")
                
        # Check for proper date handling
        date_functions = ['date_trunc', 'extract', 'to_char']
        if any(func in query_lower for func in date_functions):
            if not re.search(r"interval '\d+\s+(?:year|month|day|hour|minute|second)'", query_lower):
                logger.warning("Date/time manipulation without proper interval specification")


        """Extract parameters with enhanced handling"""
        params = []
        
        def replace_literal(match):
            value = match.group(1)
            # Handle different value types
            try:
                # Try to convert to number if possible
                if value.isdigit():
                    params.append(int(value))
                elif value.replace('.', '').isdigit():
                    params.append(float(value))
                else:
                    params.append(value)
            except ValueError:
                params.append(value)
            return f"${len(params)}"
        
        # Replace string literals with parameters
        parameterized_query = re.sub(
            r"'([^']*)'",  # Match string literals
            replace_literal,
            query
        )
        
        return parameterized_query, params 