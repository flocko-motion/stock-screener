.PHONY: test test-cov lint format clean install test-parser test-elementary test-terminal test-integration test-basic-flows

# Default target
all: test

# Install dependencies
install:
	poetry install

# Run all tests
test:
	poetry run python -m unittest discover

# Run basic flow tests
test-basic-flows:
	poetry run pytest tests/test_dsl.py -v -k BasicFlowTests

# Run parser tests
test-parser:
	poetry run python -m unittest fins.tests.test_parser

# Run elementary action tests
test-elementary:
	poetry run python -m unittest fins.tests.test_elementary_actions

# Run terminal input/output tests
test-terminal:
	poetry run python -m unittest fins.tests.test_terminal_io

# Run integration tests
test-integration:
	poetry run python -m unittest fins.tests.test_integration

# Run tests with coverage
test-cov:
	poetry run pytest

# Run linting
lint:
	poetry run flake8 fins tests

# Format code
format:
	poetry run black fins tests

# Clean up build artifacts
clean:
	rm -rf .coverage htmlcov/ .pytest_cache/ dist/ build/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run the FINS CLI
run:
	poetry run fins

# Run the FINS CLI in interactive mode
interactive:
	poetry run fins -i 