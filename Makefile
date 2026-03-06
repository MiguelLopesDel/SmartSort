.PHONY: help install install-dev format format-check lint type-check test test-cov clean

help:  ## Show this help message
	@echo "SmartSort - Makefile Commands"
	@echo "=============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -r requirements.txt
	pip install -e .

install-dev:  ## Install development dependencies (CI tools)
	pip install -r requirements-ci.txt
	pip install -e .
	pre-commit install

install-hooks:  ## Install git pre-push hook
	@echo "Installing pre-push hook..."
	@cp scripts/pre-push.sh .git/hooks/pre-push
	@chmod +x .git/hooks/pre-push
	@echo "✅ Pre-push hook installed!"
	@echo "O hook será executado automaticamente antes de cada push."
	@echo "Para pular o hook: git push --no-verify"

format:  ## Auto-format code with black and isort (same as CI)
	black src/ tests/
	isort src/ tests/

format-check:  ## Check formatting without modifying files (same as CI)
	@echo "Checking formatting with Black..."
	black --check src/ tests/
	@echo "Checking import sorting with isort..."
	isort --check-only src/ tests/

lint:  ## Run flake8 linter (same as CI)
	flake8 src/ tests/

type-check:  ## Run mypy type checker (same as CI)
	mypy src/

test:  ## Run tests
	pytest

test-cov:  ## Run tests with coverage
	pytest --cov=src --cov-report=xml --cov-report=term

ci-check:  ## Run all CI checks locally (format, lint, type, test)
	@echo "Running all CI checks..."
	@$(MAKE) format-check
	@$(MAKE) lint
	@$(MAKE) type-check
	@$(MAKE) test

pre-push:  ## Run before pushing (format + all checks)
	@echo "Formatting code..."
	@$(MAKE) format
	@echo "Running all checks..."
	@$(MAKE) ci-check
	@echo "✅ All checks passed! Safe to push."

clean:  ## Clean up cache and build files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .coverage coverage.xml htmlcov/ build/ dist/
