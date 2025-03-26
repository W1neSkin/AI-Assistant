# MCP Server for RAG Project

This is an MCP (Model Control Protocol) server implementation that duplicates the functionality of the existing services in the RAG project. It provides a set of tools, resources, and prompts that can be used to interact with the database, vector store, and other services.

## Features

- Database operations (query execution, schema retrieval)
- Document indexing and retrieval
- URL content extraction and processing
- Question answering with context from multiple sources

## Architecture

The MCP server is built using the following components:

- **MCP**: Model Control Protocol for defining tools, resources, and prompts
- **FastMCP**: MCP implementation that provides a standalone server
- **Weaviate**: Vector database for document storage and retrieval
- **PostgreSQL**: Relational database for structured data
- **Sentence Transformers**: For generating embeddings
- **Ollama**: For local LLM inference

## Available Tools

### Server Info Tools

- `server_info`: Get information about the MCP server
- `health_check`: Health check endpoint

### Database Tools

- `initialize_db`: Initialize database connection pool
- `close_db`: Close database connection pool
- `get_db_schema`: Get database schema
- `execute_query`: Execute a SQL query with safety checks

### Index Tools

- `initialize_index`: Initialize the vector store and embedding model
- `close_index`: Close the vector store client
- `index_document`: Index a document with chunking and user tracking
- `query_documents`: Query documents with user filter
- `get_user_documents`: Get list of user's documents
- `delete_document`: Remove document from user's list
- `update_document_status`: Update the active status of a document

### URL Tools

- `extract_urls`: Extract URLs from text
- `fetch_url_content`: Fetch content from a URL
- `summarize_url`: Fetch and summarize content from a URL

### QA Tools

- `is_db_question`: Determine if a question requires database access
- `generate_sql`: Generate SQL for a question
- `get_answer`: Get answer for a question

## Usage

### Running the Server

The server can be run using Docker Compose:

```bash
docker-compose up mcp-server
```

### Connecting to the Server

To connect to the MCP server from a client, you can use the MCP client library:

```python
from mcp import Client

client = Client("http://localhost:8001")
tools = client.list_tools()
print(tools)

# Execute a tool
result = client.execute_tool("get_answer", {
    "question": "What is the capital of France?",
    "user_id": "user123",
    "use_db": True,
    "use_docs": True,
    "handle_urls": True,
    "use_cloud_llm": False
})
print(result)
```

### Example API Calls

You can also interact with the server using HTTP requests:

#### Get Answer to a Question

```bash
curl -X POST http://localhost:8001/tools/get_answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the capital of France?",
    "user_id": "user123",
    "use_db": true,
    "use_docs": true,
    "handle_urls": true,
    "use_cloud_llm": false
  }'
```

#### Query Documents

```bash
curl -X POST http://localhost:8001/tools/query_documents \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Tell me about machine learning",
    "user_id": "user123",
    "max_results": 5
  }'
```

#### Execute SQL Query

```bash
curl -X POST http://localhost:8001/tools/execute_query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT * FROM users LIMIT 10"
  }'
```

## Development

### Adding New Tools

To add a new tool, create a function with the `@mcp_server.tool()` decorator in one of the module files:

```python
from mcp_server import mcp_server

@mcp_server.tool()
async def my_new_tool(param1: str, param2: int) -> Dict[str, Any]:
    """Tool description
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Result description
    """
    # Tool implementation
    return {
        "status": "success",
        "result": "Tool result"
    }
```

Then add the tool to the appropriate tools collection:

```python
my_module_tools = [
    existing_tool1,
    existing_tool2,
    my_new_tool
]
```

### Adding New Prompts

To add a new prompt, create a function with the `@mcp_server.prompt()` decorator:

```python
from mcp_server import mcp_server

@mcp_server.prompt()
def my_new_prompt(param1: str, param2: str) -> str:
    """Prompt description
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Formatted prompt
    """
    return f"""
    This is a prompt with {param1} and {param2}.
    """
```

### Adding New Resources

To add a new resource, create a function with the `@mcp_server.resource()` decorator:

```python
from mcp_server import mcp_server

@mcp_server.resource("/resources/my_resource/{param}")
async def my_resource(param: str) -> Any:
    """Resource description
    
    Args:
        param: Description of param
        
    Returns:
        Resource data
    """
    # Resource implementation
    return {"data": f"Resource data for {param}"}
```

Note: Resource paths must be valid URL paths, typically starting with a forward slash. 