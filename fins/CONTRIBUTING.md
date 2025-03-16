# Contributing to FINS

Thank you for your interest in contributing to the Financial Insights and Notation System (FINS)! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. We aim to foster an inclusive and welcoming community.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment (see [INSTALL.md](INSTALL.md))
4. Create a new branch for your feature or bug fix
5. Make your changes
6. Run tests to ensure your changes don't break existing functionality
7. Submit a pull request

## Development Environment

We use Poetry for dependency management. To set up your development environment:

```bash
# Install dependencies including development dependencies
poetry install

# Activate the virtual environment
poetry shell

# Run tests
python -m unittest discover
```

## Coding Standards

We follow PEP 8 style guidelines for Python code. Please ensure your code adheres to these standards.

- Use 4 spaces for indentation (not tabs)
- Use meaningful variable and function names
- Write docstrings for all functions, classes, and modules
- Keep line length to a maximum of 88 characters
- Add type hints where appropriate

## Testing

All new features should include appropriate tests. We use the standard `unittest` framework for testing.

To run tests:

```bash
python -m unittest discover
```

## Pull Request Process

1. Update the README.md or documentation with details of changes if appropriate
2. Update the tests to cover your changes
3. Ensure all tests pass before submitting your pull request
4. The pull request will be reviewed by maintainers
5. Once approved, your changes will be merged

## Feature Requests and Bug Reports

Please use the GitHub issue tracker to submit feature requests and bug reports. When reporting bugs, please include:

- A clear description of the issue
- Steps to reproduce the problem
- Expected behavior
- Actual behavior
- Any relevant logs or error messages

## Code Structure

The FINS project is organized as follows:

- `fins/`: Main package directory
  - `__init__.py`: Package initialization
  - `parser.py`: FINS command parser
  - `parser.lark`: Lark grammar for the FINS language
  - `cli.py`: Command-line interface
  - `examples/`: Example scripts
  - `tests/`: Test files

## License

By contributing to FINS, you agree that your contributions will be licensed under the same license as the project (see LICENSE file). 