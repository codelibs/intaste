# Copyright (c) 2025 CodeLibs
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

.PHONY: help up down logs ps restart pull-model clean dev test lint format up-gpu dev-gpu gpu-check \
        test-docker test-docker-api test-docker-ui lint-docker-api lint-docker-ui \
        test-docker-build test-docker-clean check-docker init-test-cache \
        lint-api lint-ui format-api format-ui format-docker-api format-docker-ui

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up: ## Start all services (production mode)
	docker compose up -d --build

down: ## Stop and remove all services
	docker compose down

down-v: ## Stop and remove all services including volumes
	docker compose down -v

logs: ## Follow logs for API and UI
	docker compose logs -f assera-api

logs-all: ## Follow logs for all services
	docker compose logs -f

ps: ## Show running containers
	docker compose ps

restart: ## Restart all services
	docker compose restart

pull-model: ## Pull the default LLM model (gpt-oss)
	@echo "Pulling default model: $${ASSERA_DEFAULT_MODEL:-gpt-oss}"
	docker compose exec ollama ollama pull $${ASSERA_DEFAULT_MODEL:-gpt-oss}

clean: ## Remove all containers, volumes, and images
	docker compose down -v --rmi all

dev: ## Start in development mode with hot reload
	docker compose -f compose.yaml -f compose.dev.yaml up -d --build

dev-logs: ## Follow logs in development mode
	docker compose -f compose.yaml -f compose.dev.yaml logs -f assera-api

health: ## Check health of all services
	@echo "Checking health..."
	@curl -fsS http://localhost:8000/api/v1/health && echo "✓ API OK" || echo "✗ API FAILED"
	@curl -fsS http://localhost:8080/api/v1/health >/dev/null 2>&1 && echo "✓ Fess OK" || echo "✗ Fess FAILED"

test: ## Run tests
	cd assera-api && uv pip install --system -e ".[dev]" && pytest

lint-api: ## Run API linters
	cd assera-api && uv run ruff check app/
	cd assera-api && uv run mypy app/

lint-ui: ## Run UI linters
	cd assera-ui && npm run lint
	cd assera-ui && npm run type-check

lint: ## Run all linters (API + UI)
	@$(MAKE) --no-print-directory lint-api
	@$(MAKE) --no-print-directory lint-ui

format-api: ## Format API code
	cd assera-api && uv run black app/
	cd assera-api && uv run ruff check --fix app/

format-ui: ## Format UI code
	cd assera-ui && npm run format

format: ## Format all code (API + UI)
	@$(MAKE) --no-print-directory format-api
	@$(MAKE) --no-print-directory format-ui

env: ## Create .env from example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env created from .env.example"; \
		echo "⚠️  Please update ASSERA_API_TOKEN in .env"; \
	else \
		echo ".env already exists"; \
	fi

init-dirs: ## Initialize data directories with correct permissions (Linux)
	@echo "Creating data directories..."
	@mkdir -p data/opensearch data/dictionary data/ollama
	@echo "Setting permissions (requires sudo)..."
	@sudo chown -R 1000:1000 data/opensearch data/dictionary
	@sudo chown -R $$(id -u):$$(id -g) data/ollama || sudo chown -R 1000:1000 data/ollama
	@echo "✓ Data directories initialized"

init-test-cache: ## Initialize test cache directories with correct permissions
	@echo "Creating test cache directories..."
	@mkdir -p .cache/uv assera-ui/node_modules
	@echo "Setting permissions..."
	@chown -R $$(id -u):$$(id -g) .cache assera-ui/node_modules 2>/dev/null || true
	@echo "✓ Test cache directories initialized"

up-gpu: ## Start all services with explicit GPU support (production mode)
	docker compose -f compose.yaml -f compose.gpu.yaml up -d --build

dev-gpu: ## Start in development mode with explicit GPU support
	docker compose -f compose.yaml -f compose.dev.yaml -f compose.gpu.yaml up -d --build

gpu-check: ## Check if Ollama is using GPU
	@echo "Checking Ollama GPU status..."
	@echo "Looking for 'Nvidia GPU detected' message in logs:"
	@docker logs assera-ollama 2>&1 | grep -i "gpu\|cuda" || echo "No GPU-related messages found (may be using CPU)"

## Docker-based Testing (Isolated Environment)

test-docker: ## Run all tests in Docker (API + UI)
	@echo "=========================================="
	@echo "Running all tests in Docker..."
	@echo "=========================================="
	@UID=$$(id -u) GID=$$(id -g) docker compose -f compose.test.yaml run --rm test-runner
	@echo ""
	@echo "✓ All tests completed"

test-docker-api: ## Run API tests in Docker
	@echo "=========================================="
	@echo "Running API tests in Docker..."
	@echo "=========================================="
	@UID=$$(id -u) GID=$$(id -g) docker compose -f compose.test.yaml run --rm test-api
	@echo ""
	@echo "✓ API tests completed"

test-docker-ui: ## Run UI tests in Docker
	@echo "=========================================="
	@echo "Running UI tests in Docker..."
	@echo "=========================================="
	@UID=$$(id -u) GID=$$(id -g) docker compose -f compose.test.yaml run --rm test-ui
	@echo ""
	@echo "✓ UI tests completed"

lint-docker-api: ## Run API lint checks in Docker
	@echo "=========================================="
	@echo "Running API lint checks in Docker..."
	@echo "=========================================="
	@UID=$$(id -u) GID=$$(id -g) docker compose -f compose.test.yaml run --rm lint-api
	@echo ""
	@echo "✓ API lint completed"

lint-docker-ui: ## Run UI lint checks in Docker
	@echo "=========================================="
	@echo "Running UI lint checks in Docker..."
	@echo "=========================================="
	@UID=$$(id -u) GID=$$(id -g) docker compose -f compose.test.yaml run --rm lint-ui
	@echo ""
	@echo "✓ UI lint completed"

format-docker-api: ## Run API format in Docker
	@echo "=========================================="
	@echo "Running API format in Docker..."
	@echo "=========================================="
	@UID=$$(id -u) GID=$$(id -g) docker compose -f compose.test.yaml run --rm format-api
	@echo ""
	@echo "✓ API format completed"

format-docker-ui: ## Run UI format in Docker
	@echo "=========================================="
	@echo "Running UI format in Docker..."
	@echo "=========================================="
	@UID=$$(id -u) GID=$$(id -g) docker compose -f compose.test.yaml run --rm format-ui
	@echo ""
	@echo "✓ UI format completed"

test-docker-build: ## Build Docker test image
	@echo "Building Docker test image..."
	@UID=$$(id -u) GID=$$(id -g) docker compose -f compose.test.yaml build
	@echo "✓ Build completed"

test-docker-clean: ## Clean up Docker test containers and volumes
	@echo "Cleaning up Docker test environment..."
	@docker compose -f compose.test.yaml down -v
	@docker rmi assera-test-runner 2>/dev/null || true
	@echo "✓ Cleanup completed"

check-docker: ## Run all checks (lint + test) in Docker
	@echo "=========================================="
	@echo "Running all checks in Docker..."
	@echo "=========================================="
	@echo ""
	@echo "=== Step 1/3: API Lint ==="
	@$(MAKE) --no-print-directory lint-docker-api
	@echo ""
	@echo "=== Step 2/3: UI Lint ==="
	@$(MAKE) --no-print-directory lint-docker-ui
	@echo ""
	@echo "=== Step 3/3: All Tests ==="
	@$(MAKE) --no-print-directory test-docker
	@echo ""
	@echo "=========================================="
	@echo "✓ All checks passed successfully!"
	@echo "=========================================="
