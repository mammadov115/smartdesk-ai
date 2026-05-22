# ==============================================================================
# Variables
# ==============================================================================

DC        := docker compose -f docker/docker-compose.local.yml
DC_CI     := $(DC) exec -T web
MANAGE    := uv run --env-file .envs/.local/.env python manage.py 
MANAGE_CI := $(DC_CI) python manage.py

# ==============================================================================
# Help
# ==============================================================================

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

# ==============================================================================
# Docker
# ==============================================================================

.PHONY: docker-build docker-up docker-down docker-stop docker-start docker-restart

docker-build: ## Build docker containers
	$(DC) build

docker-up: ## Start docker containers (detached) and run server
	$(DC) up -d
	$(MANAGE) runserver --settings=config.settings.local

docker-down: ## Stop and remove docker containers
	$(DC) down

docker-stop: ## Stop docker containers (keeps them created)
	$(DC) stop

docker-start: ## Start existing docker containers (ultra fast)
	$(DC) start

docker-restart: ## Restart docker containers
	$(DC) restart

# ==============================================================================
# Logs
# ==============================================================================

.PHONY: logs logs-web logs-db logs-celery

logs: ## View all docker logs (follows)
	$(DC) logs -f

logs-web: ## View last 50 lines of web container logs (follows)
	$(DC) logs -f -n 50 web

logs-db: ## View last 50 lines of db container logs (follows)
	$(DC) logs -f -n 50 db

logs-celery: ## View last 50 lines of celery worker logs (follows)
	$(DC) logs -f -n 50 celery_worker

# ==============================================================================
# Django
# ==============================================================================

.PHONY: django-shell django-migrate django-migrations django-check-migrations django-seed django-initadmin django-runserver

django-shell: ## Open Django shell
	$(MANAGE) shell

django-migrate: ## Run migrations
	$(MANAGE) migrate --settings=config.settings.local

django-makemigrations: ## Create new migrations
	$(MANAGE) makemigrations --settings=config.settings.local

django-check-migrations: ## Check for missing migrations
	$(MANAGE) makemigrations --settings=config.settings.local --check --dry-run

django-check-migrations-ci: ## Check for missing migrations (CI mode)
	$(MANAGE_CI) makemigrations --check --dry-run

django-seed: ## Seed database for local development
	$(MANAGE) seed --users 50 --questions 50 --categories 5

django-initadmin: ## Create superuser with default credentials (local only)
	$(MANAGE) createsuperuser --settings=config.settings.local


django-runserver: ## Run server
	$(MANAGE) runserver

# ==============================================================================
# Code Quality
# ==============================================================================

.PHONY: lint lint-fix format scan scan-ci

lint: ## Run ruff linter
	$(DC) exec web ruff check .

lint-fix: ## Run ruff linter with --fix to auto-fix issues
	$(DC) exec web ruff check . --fix

format: ## Run ruff formatter
	$(DC) exec web ruff format .

scan: ## Run security scanning tools (bandit, safety)
	$(DC) exec web bandit -r apps/ config/
	$(DC) exec web safety check

scan-ci: ## Run security scanning tools (CI mode)
	$(DC_CI) bandit -r apps/ config/
	$(DC_CI) safety check

# ==============================================================================
# Testing
# ==============================================================================

.PHONY: test test-ci

test: ## Run tests
	$(DC) exec web pytest

test-ci: ## Run tests (CI mode)
	$(DC_CI) pytest

# ==============================================================================
# Environment Specific
# ==============================================================================

.PHONY: docker-up-dev docker-up-prod

docker-up-dev: ## Start dev environment
	docker compose -f docker/docker-compose.dev.yml up -d

docker-up-prod: ## Start prod environment
	docker compose -f docker/docker-compose.prod.yml up -d

# ==============================================================================
# Aggregate
# ==============================================================================

.PHONY: check

check: format lint scan test django-check-migrations ## Run all checks (format, lint, scan, test, migrations)

# ==============================================================================
# Flower
# ==============================================================================

.PHONY: flower flower-stop

flower: ## Open Flower UI in browser (http://localhost:5555)
	$(DC) up -d flower

flower-stop: ## Stop Flower service
	$(DC) stop flower


# ==============================================================================
# Github Actions
# ==============================================================================
.PHONY: git-merge-all

git-merge-all: 
	git switch develop
	git push
	git switch dev
	git merge develop
	git push
	git switch master
	git merge dev
	git push
	git switch develop
	echo "All branches merged successfully!"

git-merge-dev:
	git switch develop
	git push
	git switch dev
	git merge develop
	git push
	git switch develop
	echo "develop merged into dev successfully!"


# ==============================================================================
# Celery
# ==============================================================================
.PHONY: celery-run

celery-run: ## Run Celery worker
	uv run --env-file .envs/.local/.env celery -A config.celery_app worker --loglevel=info
