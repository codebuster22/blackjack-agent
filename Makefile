# Makefile for blackjack-agent project

.PHONY: help test test-unit test-db test-integration test-all setup teardown clean docker-start docker-stop docker-restart docker-status

# Default target
help:
	@echo "Available commands:"
	@echo "  setup          - Set up test environment"
	@echo "  test           - Run all tests"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-db        - Run database tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  docker-start   - Start test database"
	@echo "  docker-stop    - Stop test database"
	@echo "  docker-restart - Restart test database"
	@echo "  docker-status  - Check database status"
	@echo "  teardown       - Clean up test environment"
	@echo "  clean          - Clean up all test artifacts"

# Test environment setup
setup:
	@echo "Setting up test environment..."
	@source .venv/bin/activate && python scripts/test_setup.py setup
	@source .venv/bin/activate && python scripts/test_setup.py start

# Test environment teardown
teardown:
	@echo "Tearing down test environment..."
	@source .venv/bin/activate && python scripts/test_setup.py cleanup
	@source .venv/bin/activate && python scripts/test_setup.py stop

# Run all tests
test: setup
	@echo "Running all tests..."
	@source .venv/bin/activate && python -m pytest -v
	@$(MAKE) teardown

# Run unit tests only
test-unit:
	@echo "Running unit tests..."
	@source .venv/bin/activate && python -m pytest -m unit -v

# Run database tests only
test-db: setup
	@echo "Running database tests..."
	@source .venv/bin/activate && python -m pytest -m database -v
	@$(MAKE) teardown

# Run integration tests only
test-integration: setup
	@echo "Running integration tests..."
	@source .venv/bin/activate && python -m pytest -m integration -v
	@$(MAKE) teardown

# Run all tests with coverage
test-cov: setup
	@echo "Running tests with coverage..."
	@source .venv/bin/activate && python -m pytest --cov=services --cov=dealer_agent --cov-report=term-missing --cov-report=html -v
	@$(MAKE) teardown

# Docker management
docker-start:
	@echo "Starting test database..."
	@source .venv/bin/activate && python scripts/test_setup.py start

docker-stop:
	@echo "Stopping test database..."
	@source .venv/bin/activate && python scripts/test_setup.py stop

docker-restart:
	@echo "Restarting test database..."
	@source .venv/bin/activate && python scripts/test_setup.py restart

docker-status:
	@echo "Checking database status..."
	@source .venv/bin/activate && python scripts/test_setup.py check

# Clean up test artifacts
clean:
	@echo "Cleaning up test artifacts..."
	@rm -rf .pytest_cache/
	@rm -rf htmlcov/
	@rm -rf .coverage
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true

# Development helpers
install-dev:
	@echo "Installing development dependencies..."
	@source .venv/bin/activate && pip install -e .

format:
	@echo "Formatting code..."
	@source .venv/bin/activate && black . --line-length 88

lint:
	@echo "Running linter..."
	@source .venv/bin/activate && flake8 . --max-line-length 88

# Quick test commands
quick-test:
	@echo "Running quick tests (unit only)..."
	@source .venv/bin/activate && python -m pytest tests/test_foundation.py::TestFoundationUnit -v

foundation-test:
	@echo "Testing foundation setup..."
	@source .venv/bin/activate && python -m pytest tests/test_foundation.py -v 