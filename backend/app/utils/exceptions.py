class SQLGenerationError(Exception):
    """Raised when SQL generation fails"""
    pass

class DatabaseQueryError(Exception):
    """Raised when database query fails"""
    pass

class SchemaError(Exception):
    """Raised when schema retrieval fails"""
    pass 