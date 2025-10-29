# Intaste API

Intaste API is a FastAPI-based backend service that provides LLM-enhanced search capabilities by combining Fess search engine with language models (Ollama).

## Features

- **Assisted Search**: Natural language query processing with Intent → Search → Compose flow
- **Provider Abstractions**: Extensible architecture for search providers and LLM clients
- **Fallback Strategies**: Graceful degradation when LLM or search services are unavailable
- **Security First**: API token authentication, CORS, non-root containers
- **Observability**: Request ID tracking, structured logging, performance metrics

## Architecture

```
User Query → Intent Extraction (LLM) → Search (Fess) → Answer Composition (LLM) → Response
              ↓ (fallback)              ↓ (fallback)    ↓ (fallback)
          Use original query         Return error     Generic guidance
```

### Timeout Budget Allocation

- **Total**: 5000ms (configurable)
  - Intent: 40% (2000ms)
  - Search: 40% (2000ms)
  - Compose: 20% (1000ms)

## API Endpoints

### Public Endpoints

- `GET /api/v1/health` - Health check (no authentication)
- `GET /` - API information

### Authenticated Endpoints

All require `X-Intaste-Token` header.

- `POST /api/v1/assist/query` - Execute assisted search
- `POST /api/v1/assist/feedback` - Submit feedback
- `GET /api/v1/models` - List available models
- `POST /api/v1/models/select` - Select model

## Quick Start

### Using Docker Compose (Recommended)

```bash
# From repository root
cd ..
make up
make pull-model
make health
```

### Local Development

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Create .env file
cp ../.env.example .env
# Edit .env and set required variables

# Run server
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest

# Lint and format
uv run ruff check app/
uv run black app/
uv run mypy app/
```

## Configuration

Environment variables (see `.env.example` for details):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `INTASTE_API_TOKEN` | **Yes** | - | API authentication token (32+ chars) |
| `INTASTE_DEFAULT_MODEL` | No | `gpt-oss` | Default LLM model |
| `FESS_BASE_URL` | No | `http://fess:8080` | Fess search engine URL |
| `OLLAMA_BASE_URL` | No | `http://ollama:11434` | Ollama LLM service URL |
| `REQ_TIMEOUT_MS` | No | `5000` | Total request timeout |
| `LOG_LEVEL` | No | `INFO` | Logging level |

## Project Structure

```
intaste-api/
├── app/
│   ├── core/
│   │   ├── config.py              # Configuration management
│   │   ├── llm/                   # LLM client abstractions
│   │   ├── search_provider/       # Search provider abstractions
│   │   └── security/              # Authentication and middleware
│   ├── routers/                   # API endpoints
│   ├── schemas/                   # Pydantic models
│   ├── services/                  # Business logic
│   └── main.py                    # FastAPI application
├── tests/                         # Unit and integration tests
├── Dockerfile                     # Container image
└── pyproject.toml                # Dependencies and config
```

## Development

### Code Style

- **Formatter**: black (line length: 100)
- **Linter**: ruff
- **Type checker**: mypy (strict mode)
- **Docstrings**: Google style

### Adding a New Search Provider

1. Create provider class implementing `SearchProvider` protocol
2. Implement `search()` and `health()` methods
3. Add normalization logic for provider-specific responses
4. Register in configuration

```python
from app.core.search_provider.base import SearchProvider, SearchQuery, SearchResult

class MySearchProvider(SearchProvider):
    async def search(self, query: SearchQuery) -> SearchResult:
        # Implementation
        pass

    async def health(self) -> tuple[bool, dict[str, Any]]:
        # Implementation
        pass
```

### Adding a New LLM Provider

1. Create client class implementing `LLMClient` protocol
2. Implement `intent()`, `compose()`, and `health()` methods
3. Handle JSON output validation and fallbacks
4. Register in configuration

## Testing

### Quick Start

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test
uv run pytest tests/unit/test_assist_service.py -v

# Run unit tests only
uv run pytest tests/unit/ -m unit

# Run integration tests only
uv run pytest tests/integration/ -m integration
```

### Test Structure

- `tests/unit/` - Unit tests for individual components
  - `test_ollama_client.py` - LLM client tests
  - `test_fess_provider.py` - Search provider tests
  - `test_assist_service.py` - Service orchestration tests
- `tests/integration/` - API endpoint integration tests
  - `test_api_endpoints.py` - End-to-end API tests
- `conftest.py` - Shared fixtures and test configuration

### Coverage

View HTML coverage report:
```bash
uv run pytest --cov=app --cov-report=html
open htmlcov/index.html
```

For more details, see [../TESTING.md](../TESTING.md)

## Deployment

### Docker

```bash
# Build image
docker build -t intaste-api:latest .

# Run container
docker run -d \
  --name intaste-api \
  -p 8000:8000 \
  -e INTASTE_API_TOKEN=your-token \
  -e FESS_BASE_URL=http://fess:8080 \
  -e OLLAMA_BASE_URL=http://ollama:11434 \
  intaste-api:latest
```

### Production Considerations

- Use external configuration management (e.g., Vault)
- Enable persistent session storage (Redis)
- Configure proper logging aggregation
- Set up monitoring and alerting
- Use HTTPS with reverse proxy
- Implement rate limiting at infrastructure level

## Security

- ✅ API token authentication
- ✅ Non-root container user (UID 1001)
- ✅ CORS properly configured
- ✅ Request ID tracking
- ✅ Input validation with Pydantic
- ✅ Security headers and best practices

## License

Copyright (c) 2025 CodeLibs

Licensed under the Apache License, Version 2.0. See [LICENSE](../LICENSE) file for details.

## Contributing

See [DEVELOPMENT.md](../DEVELOPMENT.md) for development guidelines.

## Support

- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Ask questions and share ideas via GitHub Discussions
