# Intaste Development Guide

This guide provides comprehensive information for developers contributing to Intaste.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Project Architecture](#project-architecture)
3. [Development Workflow](#development-workflow)
4. [Common Commands](#common-commands)
5. [Coding Standards](#coding-standards)
6. [Testing](#testing)
7. [Internationalization](#internationalization)
8. [Building and Running](#building-and-running)
9. [Contributing](#contributing)
10. [CI/CD](#cicd)
11. [Release Process](#release-process)
12. [Key Implementation Details](#key-implementation-details)
13. [Important Constraints](#important-constraints)
14. [Environment Variables Reference](#environment-variables-reference)
15. [Documentation](#documentation)

## Development Setup

### Prerequisites

- **Docker**: 24+ with Docker Compose v2+
- **Python**: 3.13+ (for local API development)
- **Node.js**: 20+ (for local UI development)
- **Git**: Latest stable version
- **Optional**: NVIDIA GPU with Container Toolkit for faster LLM responses

### Quick Start for Developers

```bash
# 1. Clone and setup
git clone https://github.com/codelibs/intaste.git
cd intaste

# 2. Create environment file
cp .env.example .env
# Edit .env and set INTASTE_API_TOKEN to a secure random value
sed -i.bak "s/INTASTE_API_TOKEN=.*/INTASTE_API_TOKEN=$(openssl rand -hex 24)/" .env

# 3. Initialize data directories (Linux only, requires sudo)
make init-dirs
# macOS/Windows users can skip this step

# 4. Start development environment with hot reload
make dev

# 5. Pull default LLM model (first time only)
make pull-model

# 6. Check service health
make health
```

### GPU Support for Development

For NVIDIA GPU acceleration:

```bash
# Check prerequisites
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)

# Install NVIDIA Container Toolkit (Ubuntu/Debian)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi

# Start dev environment with GPU
make dev-gpu

# Check GPU detection (after services are running)
make gpu-check
```

**Note**: Ollama automatically uses NVIDIA GPU when available and falls back to CPU otherwise.

### Local Development (without Docker)

#### API Development

```bash
cd intaste-api

# Install dependencies (using uv)
uv pip install -e ".[dev]"

# Run tests
uv run pytest
uv run pytest --cov                     # With coverage

# Run linters
uv run ruff check app/
uv run mypy app/

# Format code
uv run black app/
uv run ruff check --fix app/

# Start API server (requires Fess and Ollama running)
uv run uvicorn app.main:app --reload
```

#### UI Development

```bash
cd intaste-ui

# Install dependencies
npm install

# Run tests
npm test                                # Vitest unit tests
npm run test:coverage                   # With coverage
npm run test:e2e                        # Playwright E2E tests
npm run test:e2e:ui                     # E2E with UI

# Run linters
npm run lint                            # ESLint
npm run format                          # Prettier
npm run type-check                      # TypeScript

# Start UI server (requires API running)
npm run dev
```

## Project Architecture

### Overview

- **Architecture**: `intaste-ui` (Next.js) → `intaste-api` (FastAPI) → `fess` (Search) → `opensearch` (Backend) + `ollama` (LLM)
- **Principle**: Intaste **never directly accesses OpenSearch** (only via Fess REST/OpenAPI)
- **Design Philosophy**: Human-centered, evidence-based assistance with transparent citations

### Query Processing Pipeline

Intaste processes queries through a streaming pipeline with automatic quality control:

1. **SearchAgent Execution** (`SearchAgent.search_stream()`)
   - **Intent Extraction**: Converts natural language to optimized Lucene query
   - **Search Execution**: Executes search via Fess OpenAPI
   - **Relevance Evaluation**: LLM evaluates each result's relevance (0.0-1.0 score)
   - **Retry Logic**: If max score < threshold (default 0.3), automatically retries with improved query
   - Returns aggregated, quality-controlled results via streaming events
   - **Fallback**: On intent LLM failure, uses original query as-is

2. **Answer Composition** (`LLMClient.compose_stream()`)
   - Generates concise answer from citations
   - **Language Support**: Responds in user-selected language (en, ja, zh-CN, zh-TW, de, es, fr)
   - Streams response via Server-Sent Events (SSE)
   - **Fallback**: On LLM failure, returns multilingual guidance message

### Abstraction Layers

**SearchAgent** (`intaste-api/app/core/search_agent/`)
- `base.py`: Abstract `SearchAgent` protocol and models
- `fess.py`: `FessSearchAgent` implementation with retry logic
- `factory.py`: Factory for creating search agents
- **Design Goal**: Enable multiple search agent implementations

**Search Provider** (`intaste-api/app/core/search_provider/`)
- `base.py`: Abstract `SearchProvider` protocol with `search()` and `health()` methods
- `fess.py`: `FessSearchProvider` implementation
- `factory.py`: Factory for creating providers based on config
- Normalizes Fess responses to common `SearchResult` model

**LLM Client** (`intaste-api/app/core/llm/`)
- `base.py`: Abstract `LLMClient` protocol with `intent()`, `compose()`, and `relevance()` methods
- `ollama.py`: `OllamaClient` implementation using langchain
- `prompts.py`: Prompt templates for intent, composition, relevance, and retry
- `factory.py`: Factory for creating LLM clients
- Supports streaming mode and multilingual responses

### Directory Structure

```
intaste/
├─ compose.yaml                # Production deployment
├─ compose.dev.yaml            # Development (hot reload)
├─ compose.gpu.yaml            # GPU support configuration
├─ compose.test.yaml           # Docker-based testing
├─ .env.example                # Environment variables sample
├─ Makefile                    # Common commands
├─ README.md                   # User-focused getting started
├─ DEVELOPMENT.md              # This file
├─ TESTING.md                  # Comprehensive testing guide
├─ CLAUDE.md                   # AI assistant instructions
├─ intaste-ui/                 # Next.js frontend
│   ├─ app/                    # Pages (App Router)
│   ├─ src/
│   │   ├─ components/         # UI components
│   │   │   ├─ answer/         # AnswerBubble
│   │   │   ├─ common/         # EmptyState, ErrorBanner, LatencyIndicator
│   │   │   ├─ history/        # QueryHistory
│   │   │   ├─ input/          # QueryInput
│   │   │   └─ sidebar/        # EvidencePanel, EvidenceItem
│   │   ├─ libs/               # Utilities
│   │   │   ├─ apiClient.ts    # API client
│   │   │   ├─ streamingClient.ts  # SSE streaming client
│   │   │   ├─ sanitizer.ts    # DOMPurify wrapper
│   │   │   ├─ uuid.ts         # UUID utilities
│   │   │   └─ utils.ts        # Utility functions
│   │   ├─ store/              # Zustand state management
│   │   │   ├─ assist.store.ts # Search state, API interactions
│   │   │   ├─ session.store.ts# Session management
│   │   │   └─ ui.store.ts     # UI state
│   │   └─ types/              # TypeScript types
│   ├─ tests/                  # Vitest unit tests
│   ├─ e2e/                    # Playwright E2E tests
│   └─ Dockerfile
├─ intaste-api/                # FastAPI backend
│   ├─ app/
│   │   ├─ main.py             # FastAPI app initialization
│   │   ├─ i18n/               # Internationalization (gettext + Babel)
│   │   ├─ core/
│   │   │   ├─ config.py       # Settings (pydantic-settings)
│   │   │   ├─ health.py       # Health check logic
│   │   │   ├─ search_agent/   # Search agent abstraction
│   │   │   ├─ llm/            # LLM abstraction
│   │   │   ├─ search_provider/# Search provider abstraction
│   │   │   └─ security/       # Auth middleware
│   │   ├─ routers/
│   │   │   ├─ assist_stream.py# POST /api/v1/assist/query (SSE)
│   │   │   ├─ health.py       # Health endpoints
│   │   │   └─ models.py       # Model selection
│   │   ├─ services/
│   │   │   └─ assist.py       # AssistService
│   │   └─ schemas/            # Request/response schemas
│   ├─ tests/                  # pytest tests
│   │   ├─ unit/               # Unit tests
│   │   └─ integration/        # Integration tests
│   ├─ locales/                # i18n translations
│   └─ Dockerfile
└─ docs/                       # Design documentation
    ├─ 01_requirements/        # Project overview
    ├─ 02_architecture/        # System architecture, process flows
    ├─ 03_api/                 # API specification
    ├─ 04_ui/                  # UI design
    ├─ 05_deployment/          # Docker Compose, environment
    ├─ 06_security/            # Security design
    ├─ 07_operations/          # Logging, monitoring
    └─ 08_development/         # Development guidelines
```

## Development Workflow

### Branch Strategy

- `main` - Stable, deployable code (protected branch)
- `feat/<scope>-<description>` - New features
- `fix/<scope>-<description>` - Bug fixes
- `docs/<scope>` - Documentation changes
- `chore/<scope>` - Maintenance tasks
- `refactor/<scope>` - Code refactoring
- `test/<scope>` - Test improvements

### Making Changes

1. **Fork and clone**:
   ```bash
   git clone https://github.com/<your-username>/intaste.git
   cd intaste
   git remote add upstream https://github.com/codelibs/intaste.git
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feat/api-new-feature
   ```

3. **Make changes and test**:
   ```bash
   # Make your changes
   make test
   make lint
   ```

4. **Commit with conventional format**:
   ```bash
   git commit -m "feat(api): add /assist/feedback endpoint

   Implement user feedback collection for quality monitoring.
   Stores feedback in logs for initial version.

   Fixes #123"
   ```

5. **Update your fork**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   git push origin feat/api-new-feature
   ```

6. **Create Pull Request** on GitHub

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

**Scopes**: `api`, `ui`, `docs`, `search`, `llm`, `security`, `i18n`, `docker`, `ci`

**Examples**:
```
feat(api): add timeout configuration for LLM calls

Add environment variables for configuring intent_timeout_ms,
search_timeout_ms, and compose_timeout_ms independently.

Fixes #123
```

```
fix(ui): prevent HTML tag bypass attack in sanitizer

Update DOMPurify configuration to block all script tags
and sanitize on server-side before client rendering.

Closes #456
```

## Common Commands

### Development

```bash
make dev                         # Start development mode with hot reload
make dev-gpu                     # Start dev mode with GPU support
make dev-logs                    # Follow dev environment logs
make pull-model                  # Pull default LLM model (gpt-oss)
```

### Testing

```bash
# API tests (run from intaste-api/)
cd intaste-api
uv run pytest                           # Run all tests
uv run pytest --cov                     # Run with coverage
uv run pytest tests/unit/test_assist.py # Run specific test file

# UI tests (run from intaste-ui/)
cd intaste-ui
npm test                         # Run Vitest tests
npm run test:coverage           # With coverage
npm run test:e2e                # Run Playwright E2E tests
npm run test:e2e:ui             # E2E tests with UI

# Run tests from root
make test                        # API tests only

# Docker-based testing (isolated environment)
make test-docker                 # Run all tests in Docker
make test-docker-api             # Run API tests in Docker
make test-docker-ui              # Run UI tests in Docker
make check-docker                # Run all checks (lint + test) in Docker
```

### Code Quality

```bash
# API linting and formatting (from intaste-api/)
cd intaste-api
uv run ruff check app/                  # Lint
uv run mypy app/                        # Type check
uv run black app/                       # Format
uv run ruff check --fix app/            # Auto-fix issues

# From root
make lint                        # Run linters
make format                      # Format code
make lint-docker-api             # Lint API in Docker
make format-docker-api           # Format API in Docker

# UI linting (from intaste-ui/)
cd intaste-ui
npm run lint                     # ESLint
npm run format                   # Prettier
npm run type-check              # TypeScript check
```

### Docker Management

```bash
make up                          # Start production mode
make down                        # Stop services
make down-v                      # Stop and remove volumes
make logs                        # Follow API logs
make logs-all                    # Follow all service logs
make ps                          # Show running containers
make restart                     # Restart all services
make clean                       # Remove everything including images
```

### Health Checks

```bash
make health                      # Check all services
make gpu-check                   # Check GPU detection (after services start)
```

## Coding Standards

### Python (API)

- **Line length**: 100 characters
- **Formatter**: `black` (configured in `pyproject.toml`)
- **Linter**: `ruff` (configured in `pyproject.toml`)
- **Type checker**: `mypy` (strict mode)
- **Style**: PEP 8 compliant
- **Docstrings**: Google style for public APIs
- **Async**: Use `async/await` consistently, not callbacks
- **Error handling**: Use custom exceptions or standard HTTP exceptions

**Example**:
```python
async def search_with_retry(query: str, max_retries: int = 2) -> SearchResult:
    """Execute search with automatic retry on low relevance.

    Args:
        query: User's natural language query
        max_retries: Maximum number of retry attempts

    Returns:
        SearchResult with citations and relevance scores

    Raises:
        SearchError: If search fails after all retries
    """
    pass
```

### TypeScript (UI)

- **Strict mode**: Enabled in `tsconfig.json`
- **No `any`**: Use proper types or `unknown`
- **Formatter**: `prettier` (configured in `.prettierrc`)
- **Linter**: `eslint` with `@typescript-eslint`
- **React**: Functional components with hooks, no class components
- **State**: Zustand for global state, local state for component-specific
- **Async**: Use `async/await`, not `.then()`

**Example**:
```typescript
interface SearchState {
  query: string;
  isLoading: boolean;
  answer: Answer | null;
  citations: Citation[];
}

const useSearchStore = create<SearchState>((set) => ({
  query: '',
  isLoading: false,
  answer: null,
  citations: [],
}));
```

### General Guidelines

- Write clear, self-documenting code
- Add comments for complex logic only
- Keep functions small and focused (<50 lines)
- Follow SOLID principles
- Write tests for new features
- Update documentation as needed
- Never bypass search provider abstraction to access OpenSearch directly

## Testing

### Overview

See [TESTING.md](TESTING.md) for comprehensive testing guide.

### API Tests (`intaste-api/tests/`)

- **Unit tests** (`unit/`): Test individual components with mocked dependencies
  - `test_fess_search_agent.py` - SearchAgent logic
  - `test_assist_service.py` - AssistService
  - `test_fess_provider.py` - FessSearchProvider
  - `test_ollama_client.py` - OllamaClient
  - `test_health.py` - Health check logic
  - `test_i18n.py` - Internationalization

- **Integration tests** (`integration/`): Test component interactions
  - `test_api_endpoints.py` - Full API endpoint tests
  - `test_streaming_endpoint.py` - SSE streaming tests
  - `test_health_endpoints.py` - Health endpoint tests

Use `pytest` with `respx` for HTTP mocking and `pytest-asyncio` for async tests.

### UI Tests

- **Unit tests** (`intaste-ui/tests/`): Vitest with React Testing Library
  - `components/` - Component tests
  - `libs/` - Utility function tests
  - `stores/` - Zustand store tests

- **E2E tests** (`intaste-ui/e2e/`): Playwright
  - `search-flow.spec.ts` - Full search flow
  - `streaming.spec.ts` - SSE streaming
  - `citation-interaction.spec.ts` - Citation clicks
  - `accessibility.spec.ts` - A11y checks
  - `security.spec.ts` - Security validations

### Coverage Requirements

- **Minimum**: 80% code coverage
- **Public APIs**: Must be tested
- **Critical paths**: Must have integration tests
- **Security features**: Must have dedicated tests

## Internationalization

The API supports multiple languages using GNU gettext + Babel:

### Workflow

```bash
# 1. Add translatable messages in code (from intaste-api/)
# Use the _() function from app.i18n module:
from app.i18n import _
message = _("Your message here", language="en")

# 2. Extract messages from source code to .pot template
make i18n-extract                # Creates/updates locales/messages.pot

# 3. Update .po files with new messages from template
make i18n-update                 # Updates all language .po files

# 4. Edit .po files in locales/{lang}/LC_MESSAGES/messages.po
# Add your translations

# 5. Compile .po files to .mo binary files for runtime
make i18n-compile                # Required after editing translations

# 6. Test translations
cd intaste-api
uv run pytest tests/unit/test_i18n.py
```

### Supported Languages

- `en` - English
- `ja` - Japanese
- `zh_CN` - Chinese (Simplified)
- `zh_TW` - Chinese (Traditional)
- `de` - German
- `es` - Spanish
- `fr` - French

### Translation Files

- **Template**: `intaste-api/locales/messages.pot`
- **Translations**: `intaste-api/locales/{language}/LC_MESSAGES/messages.po`
- **Compiled**: `intaste-api/locales/{language}/LC_MESSAGES/messages.mo`

### Implementation

The `_()` translation function is provided by `intaste-api/app/i18n/__init__.py`.

## Building and Running

### Production Mode

```bash
# Start all services
docker compose up -d --build

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Development Mode (Hot Reload)

```bash
# Start with hot reload
docker compose -f compose.yaml -f compose.dev.yaml up -d --build

# Or use make
make dev

# Follow logs
docker compose logs -f intaste-api intaste-ui
```

### Docker-based Testing

```bash
# Run all tests in isolated environment
make test-docker

# Run specific tests
make test-docker-api             # API tests only
make test-docker-ui              # UI tests only

# Run all checks (lint + test)
make check-docker
```

## Contributing

### Before You Submit

1. **Update your fork**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests and linters**:
   ```bash
   make test
   make lint
   ```

3. **Update documentation** if needed

4. **Add/update tests** for your changes

### Pull Request Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines (black, ruff, prettier, eslint)
- [ ] Commit messages follow conventional format
- [ ] Documentation updated (if applicable)
- [ ] No breaking changes (or documented in PR description)
- [ ] Screenshots included (for UI changes)
- [ ] Security considerations addressed
- [ ] i18n messages added for user-facing text

### PR Template

When creating a PR, include:

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
Describe how you tested this. Include:
- Test coverage (unit/integration/e2e)
- Manual testing steps
- Edge cases considered

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Tests pass (`make test`)
- [ ] Linters pass (`make lint`)
- [ ] Documentation updated
- [ ] Conventional commit format
- [ ] No breaking changes or documented
```

### Review Process

1. Maintainers will review your PR within 1-3 business days
2. Address feedback and requested changes
3. Re-request review after making changes
4. Once approved, PR will be merged with "Squash and Merge"

## CI/CD

### GitHub Actions Workflows

Intaste uses GitHub Actions for continuous integration:

1. **CI Workflow** (`.github/workflows/ci.yml`)
   - Runs on every push and PR
   - Executes tests, linters, and type checks
   - Generates coverage reports

2. **Security Scanning**
   - Dependency vulnerability scanning
   - Code security analysis

3. **Docker Publishing**
   - Builds and publishes Docker images on release
   - Tags: `latest`, `vX.Y.Z`

4. **Release Automation**
   - Automated changelog generation
   - Version bumping
   - GitHub Release creation

See [docs/08_development/development-guidelines.md](docs/08_development/development-guidelines.md) for detailed CI/CD configuration.

## Release Process

### Versioning

Intaste follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Breaking changes
- **MINOR** (0.X.0): New features (backward compatible)
- **PATCH** (0.0.X): Bug fixes

### Release Checklist

1. **Prepare release**:
   ```bash
   # Update version in files
   # - intaste-api/pyproject.toml
   # - intaste-ui/package.json

   # Update CHANGELOG.md
   # Add release notes under new version heading
   ```

2. **Test thoroughly**:
   ```bash
   make test-docker
   make check-docker
   ```

3. **Create tag**:
   ```bash
   git tag -a v0.2.0 -m "Release v0.2.0"
   git push --tags
   ```

4. **Create GitHub Release**:
   - Go to GitHub > Releases > New Release
   - Select tag
   - Add release notes from CHANGELOG.md
   - Publish release

5. **Build and publish Docker images** (automated via CI)

## Key Implementation Details

### Authentication

- **API Auth**: All API requests require `X-Intaste-Token` header matching `INTASTE_API_TOKEN` env var
- **Security Middleware**: `intaste-api/app/core/security/middleware.py` validates token
- **Public Endpoints**: `/api/v1/health`, `/api/v1/health/live` are exempt from auth

### Session Management

- `AssistService` maintains in-memory session state
- Tracks session ID (UUID), turn count, query history
- Future: Persistence via Redis/database for conversation context

### Error Handling & Fallbacks

The system is designed to degrade gracefully:

- **Intent LLM fails**: Continue with original query, set notice flag
- **Search fails**: Return error (search is critical)
- **Compose LLM fails**: Return generic message, set notice flag
- **0 search results**: Skip answer generation, suggest query refinement

### HTML Sanitization

- Citations may contain HTML snippets from Fess
- **Critical**: UI must sanitize with DOMPurify before rendering
- Implementation: `intaste-ui/src/libs/sanitizer.ts`
- **Server-side**: API also sanitizes before sending to UI

### Search Query Optimization

The system uses **Lucene query syntax** for optimized search precision:

- **Proper Noun Preservation**: Product names, technical terms preserved exactly
  - Example: `"Fess"` → `title:"Fess"^2 OR "Fess"`
- **Title Boosting**: Short queries (1-3 words) boost title field matches with `^2` multiplier
  - Example: `"security policy"` → `title:"security policy"^2 OR "security policy"`
- **Phrase Search**: Multi-word phrases use quotation marks for exact matching
- **Boolean Operators**: Complex queries use AND/OR/NOT operators
- **Query Refinement**: Retry mechanism uses alternative Lucene syntax and synonyms

Implementation: `intaste-api/app/core/llm/prompts.py`

### Timeout Budget

Total timeout budget is configurable via `REQ_TIMEOUT_MS` environment variable (default: 180000ms / 3 minutes):

- Intent extraction: 20% of budget (36 seconds)
- Search execution: 15% of budget (27 seconds)
- Relevance evaluation: 20% of budget (36 seconds)
- Retry search: 25% of budget (45 seconds, includes re-intent + search + relevance)
- Answer composition: 10% of budget (18 seconds)

Additional configuration:
- `INTASTE_RELEVANCE_THRESHOLD`: Minimum relevance score to accept results (default: 0.3)
- `INTASTE_MAX_RETRY_COUNT`: Maximum retry attempts (default: 2)

### Streaming Response (SSE)

The API endpoint (`/api/v1/assist/query`) uses Server-Sent Events (SSE):

- `event: start` - Processing begins
- `event: status` - Current processing phase
- `event: intent` - Intent extraction complete
- `event: citations` - Search results available (may appear multiple times during retries)
- `event: relevance` - Relevance evaluation complete
- `event: retry` - Retry search starting (with reason and previous max score)
- `event: chunk` - Answer text increments
- `event: complete` - Final response with full answer and timings
- `event: error` - Error occurred

UI uses `streamingClient.ts` to consume SSE and update state incrementally.

## Important Constraints

### Security Boundaries

- Only `intaste-ui:3000` should be externally exposed
- Keep `intaste-api`, `fess`, `opensearch`, and `ollama` on internal network
- Never log full URLs/titles in production (hash with sha256 first 12 chars)

### Search Provider Rule

**Never bypass Fess to access OpenSearch directly**. This is a core architectural principle. All search operations must go through the `SearchProvider` abstraction layer (`intaste-api/app/core/search_provider/`).

### Dependencies

- **API**: Python 3.13+, FastAPI, langchain, httpx, pydantic-settings, Babel
- **UI**: Node.js 20+, Next.js 15+, React 19, Zustand, DOMPurify
- **LLM**: Ollama (default model: `gpt-oss`)
- **Search**: Fess 14.x via REST API
- **Backend**: OpenSearch 2.x (for Fess)

## Environment Variables Reference

See `.env.example` for complete list. Key variables:

| Variable | Default | Description |
|---|---|---|
| `INTASTE_API_TOKEN` | — | **Required**: UI→API authentication key |
| `INTASTE_DEFAULT_MODEL` | `gpt-oss` | Default Ollama model |
| `INTASTE_SEARCH_PROVIDER` | `fess` | Search provider type |
| `INTASTE_LLM_PROVIDER` | `ollama` | LLM provider type |
| `FESS_BASE_URL` | `http://intaste-fess:8080` | Fess service URL |
| `FESS_TIMEOUT_MS` | `2000` | Fess timeout |
| `OLLAMA_BASE_URL` | `http://intaste-ollama:11434` | Ollama service URL |
| `INTASTE_LLM_TIMEOUT_MS` | `3000` | LLM timeout |
| `INTASTE_LLM_TEMPERATURE` | `0.2` | LLM temperature |
| `INTASTE_LLM_TOP_P` | `0.9` | LLM top_p parameter |
| `INTASTE_LLM_WARMUP_ENABLED` | `true` | Enable LLM warmup on startup |
| `INTASTE_LLM_WARMUP_TIMEOUT_MS` | `30000` | LLM warmup timeout |
| `NEXT_PUBLIC_API_BASE` | `/api/v1` | API base path for UI |
| `REQ_TIMEOUT_MS` | `180000` | Total request timeout budget (3 minutes) |
| `INTASTE_RELEVANCE_THRESHOLD` | `0.3` | Minimum relevance score threshold (0.0-1.0) |
| `INTASTE_MAX_RETRY_COUNT` | `2` | Maximum retry attempts (0-5) |
| `INTASTE_MAX_SEARCH_RESULTS` | `100` | Maximum search results from Fess (1-500) |
| `INTASTE_RELEVANCE_EVALUATION_COUNT` | `10` | Number of top results to evaluate (1-100) |
| `INTASTE_SELECTED_RELEVANCE_THRESHOLD` | `0.8` | Min score for "Selected" tab (0.0-1.0) |
| `INTASTE_UID` / `INTASTE_GID` | `1000` | Docker user/group IDs |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_PII_MASKING` | `true` | Enable PII masking in logs |
| `DEBUG` | `false` | Enable debug mode |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins |

## Documentation

### Documentation Structure

- **Root Level**:
  - `README.md` - User-focused getting started guide
  - `DEVELOPMENT.md` - This file (developer guide)
  - `TESTING.md` - Comprehensive testing guide
  - `CLAUDE.md` - AI assistant instructions

- **docs/ Directory**:
  - `docs/01_requirements/` - Project overview, implementation status
  - `docs/02_architecture/` - System architecture, process flows, streaming
  - `docs/03_api/` - API specification
  - `docs/04_ui/` - UI design specification
  - `docs/05_deployment/` - Docker Compose design, environment config
  - `docs/06_security/` - Security design
  - `docs/07_operations/` - Operations, monitoring, logging
  - `docs/08_development/` - Development guidelines, CI/CD

### Writing Documentation

- Use Markdown for all documentation
- Follow existing structure and style
- Include code examples where appropriate
- Update `docs/01_requirements/implementation-status.md` for major features
- Keep documentation synchronized with code changes

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/codelibs/intaste/issues) for bugs and feature requests
- **Discussions**: [GitHub Discussions](https://github.com/codelibs/intaste/discussions) for questions and ideas
- **Documentation**: Check [docs/](docs/) for architecture details
- **Testing**: See [TESTING.md](TESTING.md) for testing questions

## Appendix

### Health Check Endpoints

#### Basic Health Check

```bash
curl http://localhost:8000/api/v1/health
# Returns: {"status":"ok"}
```

#### Liveness Probe (Kubernetes)

```bash
curl http://localhost:8000/api/v1/health/live
# Returns: {"status":"ok"}
```

- Use for Kubernetes `livenessProbe`
- Checks if the process is alive
- Does NOT check dependencies

#### Readiness Probe (Kubernetes)

```bash
curl http://localhost:8000/api/v1/health/ready
# Returns: {"status":"ready"} or {"status":"not_ready"}
```

- Use for Kubernetes `readinessProbe`
- Checks if service is ready to accept traffic
- Verifies Fess and Ollama are healthy
- Returns HTTP 503 if not ready

#### Detailed Health Check

```bash
curl http://localhost:8000/api/v1/health/detailed | jq .
```

Example response:

```json
{
  "status": "healthy",
  "timestamp": "2025-01-10T12:34:56.789Z",
  "version": "0.1.0",
  "dependencies": {
    "fess": {
      "status": "healthy",
      "response_time_ms": 45,
      "error": null
    },
    "ollama": {
      "status": "healthy",
      "response_time_ms": 123,
      "error": null
    }
  }
}
```

**Status values**:
- `healthy` - All dependencies are healthy
- `degraded` - Some dependencies are degraded but service still operational
- `unhealthy` - Critical dependencies are down

See [intaste-api/kubernetes-example.yaml](intaste-api/kubernetes-example.yaml) for Kubernetes deployment configuration.

---

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

```
Apache License 2.0
Copyright (c) 2025 CodeLibs Project
```
