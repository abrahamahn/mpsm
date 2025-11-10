# Makefile for MPSM development tasks
#
# Usage: make <target>
# Example: make test

.PHONY: help install install-dev test test-cov test-unit test-integration format lint type-check clean docs run-scan

# Default target
help:
	@echo "MPSM Development Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make install        - Install package in editable mode"
	@echo "  make install-dev    - Install with development dependencies"
	@echo "  make test           - Run all tests"
	@echo "  make test-cov       - Run tests with coverage report"
	@echo "  make test-unit      - Run only unit tests"
	@echo "  make test-integration - Run only integration tests"
	@echo "  make format         - Format code with black and isort"
	@echo "  make lint           - Run linting (flake8, pylint)"
	@echo "  make type-check     - Run type checking with mypy"
	@echo "  make pre-commit     - Run all pre-commit hooks"
	@echo "  make clean          - Clean build artifacts and cache"
	@echo "  make docs           - Build documentation"
	@echo "  make run-scan       - Run a test scan (requires admin)"
	@echo ""

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e .[dev]
	pre-commit install

# Testing targets
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-watch:
	pytest-watch tests/ -v

# Code quality targets
format:
	@echo "Formatting code with black..."
	black src/ tests/ mpsm.py
	@echo "Sorting imports with isort..."
	isort src/ tests/ mpsm.py

format-check:
	black --check --diff src/ tests/ mpsm.py
	isort --check-only src/ tests/ mpsm.py

lint:
	@echo "Running flake8..."
	flake8 src/ tests/ mpsm.py
	@echo "Running pylint..."
	pylint src/ || true

type-check:
	mypy src/ --ignore-missing-imports

pre-commit:
	pre-commit run --all-files

# Security checks
security:
	@echo "Running bandit security check..."
	bandit -r src/ -c pyproject.toml
	@echo "Checking dependencies..."
	safety check

# Cleaning targets
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .eggs/
	@echo "Cleaning Python cache..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	@echo "Cleaning test cache..."
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	@echo "Clean complete!"

clean-all: clean
	@echo "Removing virtual environment..."
	rm -rf venv/
	@echo "All clean!"

# Documentation targets
docs:
	@echo "Documentation is in docs/ directory"
	@echo "Open docs/INSTALLATION.md for setup guide"

docs-serve:
	@echo "Use 'python -m http.server' in docs/ to serve documentation"

# Development targets
run-scan:
	@echo "Running test scan (requires admin privileges)..."
	python mpsm.py scan --verbose

run-init:
	python mpsm.py init --auto-detect

# Version and release targets
version:
	@python -c "import mpsm; print(mpsm.__version__)" 2>/dev/null || echo "Version not available"

# Quick development cycle
dev: format lint type-check test
	@echo "Development cycle complete!"

# CI simulation (what CI runs)
ci: format-check lint type-check test-cov
	@echo "CI checks complete!"

# Install git hooks
hooks:
	pre-commit install
	@echo "Git hooks installed!"

# Show project stats
stats:
	@echo "Project Statistics:"
	@echo "==================="
	@find src -name '*.py' -not -path "*/__pycache__/*" | xargs wc -l | tail -1
	@echo "Test files:"
	@find tests -name '*.py' | xargs wc -l | tail -1
	@echo "Total Python files:"
	@find . -name '*.py' -not -path "*/venv/*" -not -path "*/__pycache__/*" | wc -l

# Dependency management
deps-update:
	pip list --outdated

deps-install:
	pip install -r requirements.txt

# Quick test for specific file
test-file:
	@read -p "Enter test file path: " filepath; \
	pytest $$filepath -v
