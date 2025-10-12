# Contributing to Assera

Thank you for your interest in contributing to Assera! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Pull Requests](#submitting-pull-requests)
- [Release Process](#release-process)

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/codelibs/assera.git
   cd assera
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/codelibs/assera.git
   ```

## Development Setup

### Prerequisites

- Docker 24+ and Docker Compose v2+
- Python 3.11+ (for local API development)
- Node.js 20+ (for local UI development)
- Git

### Quick Start

1. **Create environment file**:
   ```bash
   make env
   # Edit .env and set ASSERA_API_TOKEN to a secure random value
   ```

2. **Initialize data directories** (Linux only):
   ```bash
   make init-dirs
   # This sets correct permissions for OpenSearch and Ollama volumes
   # macOS/Windows users can skip this step
   ```

3. **Start development environment**:
   ```bash
   make dev
   ```

4. **Pull LLM model** (first time only):
   ```bash
   make pull-model
   ```

5. **Check health**:
   ```bash
   make health
   ```

### Local Development (without Docker)

#### API Development

```bash
cd assera-api

# Install dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run linters
ruff check app/
mypy app/

# Format code
black app/
ruff check --fix app/

# Start API server
uvicorn app.main:app --reload
```

## Making Changes

### Branch Strategy

- `main` - stable, deployable code
- `feat/<scope>-<description>` - new features
- `fix/<scope>-<description>` - bug fixes
- `docs/<scope>` - documentation changes
- `chore/<scope>` - maintenance tasks

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

**Examples**:
```
feat(api): add /assist/feedback endpoint

Implement user feedback collection for quality monitoring.
Stores feedback in logs for initial version.

Fixes #123
```

## Coding Standards

### Python (API)

- **Formatter**: `black` (line length: 100)
- **Linter**: `ruff`
- **Type checker**: `mypy` (strict mode)
- **Style**: PEP 8 compliant
- **Docstrings**: Google style

### TypeScript (UI)

- **Formatter**: `prettier`
- **Linter**: `eslint` with `@typescript-eslint`
- **Style**: Airbnb/Standard compatible
- **Type safety**: Strict mode enabled

### General Guidelines

- Write clear, self-documenting code
- Add comments for complex logic
- Keep functions small and focused
- Follow SOLID principles
- Write tests for new features
- Update documentation as needed

## Testing

### API Tests

```bash
cd assera-api

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_assist.py
```

### Test Structure

- **Unit tests**: `tests/unit/` - Test individual components
- **Integration tests**: `tests/integration/` - Test component interactions
- **E2E tests**: Use Playwright for UI flows

### Coverage Requirements

- Minimum 80% code coverage
- All public APIs must be tested
- Critical paths must have integration tests

## Submitting Pull Requests

### Before Submitting

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

### PR Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Commit messages follow conventional format
- [ ] Documentation updated (if applicable)
- [ ] No breaking changes (or documented in PR)
- [ ] Screenshots included (for UI changes)
- [ ] Security considerations addressed

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How have you tested this?

## Screenshots (if applicable)
Add screenshots here

## Checklist
- [ ] Tests pass
- [ ] Lint pass
- [ ] Documentation updated
```

### Review Process

1. Maintainers will review your PR
2. Address feedback and requested changes
3. Once approved, PR will be merged with "Squash and Merge"

## Release Process

### Versioning

Assera follows [Semantic Versioning](https://semver.org/):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### Release Checklist

1. Update `CHANGELOG.md`
2. Update version in `pyproject.toml` and `package.json`
3. Create git tag: `git tag vX.Y.Z`
4. Push tag: `git push --tags`
5. Create GitHub Release with changelog
6. Build and publish Docker images (if applicable)

## Getting Help

- **Issues**: Open an issue in the GitHub repository
- **Discussions**: Use GitHub Discussions for questions and ideas

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
