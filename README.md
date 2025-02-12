# AI Assistant API

A powerful AI assistant API that combines document search, database querying, and natural language processing capabilities.

## Features

- **Dual LLM Support**: 
  - Local LLM (default: deepseek-r1:7b via Ollama)
  - Cloud LLM (via OpenRouter API)
  - Dynamic switching between providers

- **OpenRouter Integration**:
  - Access to multiple LLM providers through a single API
  - Supported models:
    - Google Gemini Pro
    - Anthropic Claude
    - Meta Llama
    - Mistral
  - Cost-effective API usage
  - Automatic fallback handling

- **Document Processing**:
  - Supports PDF, DOCX, TXT, and HTML files
  - Maximum file size: 10MB
  - Vector storage using Weaviate
  - Semantic search with hybrid mode support
  - Document chunking with overlap
  - Document status management (active/inactive)
  - Multi-user document access
  - Document sharing capabilities
  - Metadata-based filtering

- **Database Integration**:
  - PostgreSQL database support
  - Natural language to SQL conversion
  - Schema-aware query generation
  - Automatic database initialization

- **URL Processing**:
  - Automatic URL content extraction
  - Content caching with Redis
  - 5MB max URL content size
  - 10-second fetch timeout

## Technical Stack

- **Backend Framework**: FastAPI
- **Vector Store**: Weaviate
- **Cache**: Redis
- **Database**: PostgreSQL
- **Embedding Model**: BAAI/bge-small-en
- **Authentication**: JWT
- **Local LLM**: Ollama
- **Cloud LLM**: OpenRouter API

## Configuration

Key settings (configurable via environment variables):
```env
# LLM Settings
LLM_API_KEY=[your-openrouter-api-key]  # Get from https://openrouter.ai/keys
LLM_MODEL=google/gemini-2.0-flash-001  # OpenRouter model identifier
LLM_LOCAL_MODEL=deepseek-r1:7b  # Ollama model name
LLM_PROVIDER=local  # 'local' for Ollama or 'cloud' for OpenRouter
TEMPERATURE=0.7

# Infrastructure
DOCKER_BUILDKIT=1
COMPOSE_DOCKER_CLI_BUILD=1

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=[your-database-name]
POSTGRES_USER=[your-username]
POSTGRES_PASSWORD=[your-password]

# Vector Store
WEAVIATE_URL=http://weaviate:8080
```

## API Endpoints

- `/api/chat`: Main chat endpoint
- `/api/documents`: Document management
  - `POST /api/documents/upload`: Upload new document
  - `GET /api/documents/list`: List user's documents
  - `DELETE /api/documents/{doc_id}`: Delete document
  - `PATCH /api/documents/{doc_id}`: Update document status
  - `DELETE /api/documents/clear`: Clear all user documents
- `/api/system`: System settings and model switching
  - `GET /api/system/models`: List available models
  - `POST /api/system/switch-provider`: Switch between local/cloud
- `/api/auth`: Authentication endpoints

## Security

- JWT-based authentication
- File type validation
- MIME type checking
- Request rate limiting
- Input sanitization

## Development

1. Clone the repository
2. Install dependencies: 
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-test.txt  # Install test dependencies
   ```
3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your OpenRouter API key
4. Run services:
   ```bash
   docker-compose up -d
   ```

## Testing

The project includes comprehensive test suites:
- Unit tests
- Integration tests
- Vector store tests

### Running Tests

Use the test runner script:

```bash
# Run all tests
python run_tests.py

# Run unit tests with coverage
python run_tests.py --type unit --coverage

# Run integration tests verbosely
python run_tests.py --type integration --verbose

# Clean and run all tests with coverage
python run_tests.py --clean --coverage
```

### Test Options

- `--type`: Choose test type (`all`, `unit`, `integration`)
- `--coverage`: Generate coverage report
- `--verbose`: Show detailed output
- `--clean`: Clean test artifacts before running

### Test Structure

```
backend/tests/
├── unit/               # Unit tests
├── integration/        # Integration tests
├── mocks/             # Mock objects
└── test_files/        # Test data files
```

## Production Considerations

- Change default admin password
- Set proper JWT secret key
- Configure appropriate rate limits
- Adjust token limits based on usage
- Monitor vector store performance
- Set up proper logging
- Configure CORS settings
- Secure your OpenRouter API key
- Monitor OpenRouter API usage and costs

## License

[Your License Here]

## Vector Store Schema
```json
{
  "Documents": {
    "properties": [
      {"name": "text", "dataType": "text"},
      {"name": "filename", "dataType": "text"},
      {"name": "doc_id", "dataType": "text"},
      {"name": "chunk_id", "dataType": "int"},
      {"name": "active", "dataType": "text"},
      {"name": "users", "dataType": "text[]"},
      {"name": "file_size", "dataType": "int"},
      {"name": "total_chunks", "dataType": "int"}
    ]
  }
}
```
