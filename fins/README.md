# FINS: Financial Insights and Notation System

A powerful terminal-based tool for filtering, sorting, and analyzing financial baskets through an intuitive command syntax.

## Installation

FINS uses Poetry for dependency management. To install:

```bash
# Clone the repository
git clone https://github.com/yourusername/fins.git
cd fins

# Install dependencies with Poetry
poetry install

# Activate the virtual environment
poetry shell
```

## Usage

FINS provides a command-line interface for financial analysis:

```bash
# Basic usage
fins "AAPL MSFT -> sort mcap desc"

# Create a basket and store it
fins "AAPL MSFT GOOGL -> /MyTechBasket"

# Use set operations
fins "$MyTechBasket -> + NFLX -> - MSFT"

# Add analysis columns
fins "$MyTechBasket -> cagr 10y -> sort cagr desc"
```

## Development

To run tests:

```bash
# Run all tests
poetry run python -m unittest discover

# Run specific test modules
poetry run python -m unittest fins.tests.test_parser
poetry run python -m unittest fins.tests.test_elementary_actions
poetry run python -m unittest fins.tests.test_terminal_io
poetry run python -m unittest fins.tests.test_integration

# Run tests with coverage
poetry run pytest
```

Or from within the Poetry shell:

```bash
python -m unittest discover
```

You can also use the Makefile for common development tasks:

```bash
# Run all tests
make test

# Run specific test levels
make test-parser
make test-elementary
make test-terminal
make test-integration

# Run tests with coverage
make test-cov

# Format code
make format

# Run linting
make lint
```

### Test Structure

The FINS test suite is organized into three levels:

1. **Parser Tests** (`test_parser.py`): Tests for the FINS parser, ensuring it correctly interprets and executes various command structures.

2. **Elementary Action Tests** (`test_elementary_actions.py`): Tests for basic interactions with the Financial Modeling Prep API, verifying the ability to query symbols, get stock data, and perform other elementary actions.

3. **Terminal Input/Output Tests** (`test_terminal_io.py`): Tests for the terminal interface, validating that command inputs produce the expected outputs.

4. **Integration Tests** (`test_integration.py`): Tests that combine all three levels to verify that the entire system works together correctly.

This layered approach ensures comprehensive test coverage for the FINS system.

## Project Roadmap

FINS is being developed in phases:

1. **Phase 1 (Current)**: Core functionality and unit tests
   - Implement the FINS parser and grammar
   - Create comprehensive unit tests
   - Establish the data structures and operations

2. **Phase 2**: Command-line interface
   - Develop a simple CLI terminal
   - Support for interactive mode and file execution
   - Basic error handling and user feedback

3. **Phase 3**: Web interface
   - Create a browser-based terminal
   - Implement websocket connection to FINS server
   - Enhance visualization capabilities

4. **Phase 4**: AI integration
   - Add natural language processing capabilities
   - Support direct FINS commands, AI-assisted commands, and conversational interface
   - Implement context-aware suggestions and analysis

## License

[MIT](LICENSE)