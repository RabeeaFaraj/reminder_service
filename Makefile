# Makefile for running tests and other common tasks

.PHONY: test test-verbose test-coverage install-test-deps clean help

# Default target
help:
	@echo "Available commands:"
	@echo "  test              - Run all tests"
	@echo "  test-verbose      - Run tests with verbose output"
	@echo "  test-coverage     - Run tests with coverage report"
	@echo "  install-test-deps - Install test dependencies"
	@echo "  clean            - Clean test artifacts"
	@echo "  help             - Show this help message"

# Install test dependencies
install-test-deps:
	pip install pytest pytest-asyncio httpx coverage

# Run tests using unittest
test:
	python -m pytest tests/ -v

# Run tests with very verbose output
test-verbose:
	python -m pytest tests/ -v -s

# Run tests with coverage
test-coverage:
	python -m pytest tests/ --cov=. --cov-report=term-missing --cov-report=html:htmlcov --cov-exclude=tests/*

# Alternative: Run tests using the custom runner
test-runner:
	python tests/run_tests.py

# Run specific test file
test-sns:
	python -m pytest tests/test_sns_notifier.py -v

test-api:
	python -m pytest tests/test_api_endpoints.py -v

test-scheduler:
	python -m pytest tests/test_scheduler.py -v

# Clean test artifacts
clean:
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete