# TextSQL Makefile
.PHONY: help install dev test clean docker-up docker-down migrate db-upgrade db-downgrade

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install Python dependencies
	cd backend && pip install -r requirements.txt

dev: ## Run development server
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run tests
	cd backend && pytest -v

test-cov: ## Run tests with coverage
	cd backend && pytest --cov=app --cov-report=html --cov-report=term

docker-up: ## Start Docker services (PostgreSQL & Redis)
	docker compose up -d postgres redis

docker-up-full: ## Start all services including API
	docker-compose --profile full up -d

docker-down: ## Stop Docker services
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

db-upgrade: ## Run database migrations (upgrade)
	cd backend && alembic upgrade head

db-downgrade: ## Rollback database migrations
	cd backend && alembic downgrade -1

db-revision: ## Create a new migration
	@read -p "Enter migration message: " msg; \
	cd backend && alembic revision --autogenerate -m "$$msg"

db-reset: ## Reset database (drop all tables and re-run migrations)
	cd backend && alembic downgrade base && alembic upgrade head

clean: ## Clean up temporary files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +

format: ## Format code with black
	cd backend && black app tests

lint: ## Lint code with flake8
	cd backend && flake8 app tests

typecheck: ## Type check with mypy
	cd backend && mypy app

check: format lint typecheck test ## Run all checks (format, lint, typecheck, test)

git-init: ## Initialize git repository with initial commit
	git init
	git add .
	git commit -m "Initial commit: Phase 1 foundation setup"

env: ## Copy .env.example to .env
	cp backend/.env.example backend/.env
	@echo "Created backend/.env - Please update with your API keys"
