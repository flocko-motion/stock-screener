# FINS: Financial Insights and Notation System

FINS is a powerful terminal-based tool for filtering, sorting, and analyzing financial baskets through an intuitive command syntax. It helps investors efficiently manage and analyze their financial instruments using a functional programming inspired approach.

## Features

- **Intuitive Command Syntax**: Chain commands together using a pipeline approach
- **Basket Operations**: Create, filter, sort, and analyze collections of financial symbols
- **Set Operations**: Perform union, intersection, and difference operations on baskets
- **Analysis Columns**: Add various financial metrics as columns to your baskets
- **Data Sources**: Connect to multiple financial data providers
- **Variable System**: Store and retrieve baskets with session or persistent variables
- **Function Definitions**: Define custom functions for reuse

## Quick Start

```bash
# Install
pip install fins

# Run a command
fins "AAPL MSFT GOOGL -> sort mcap desc"

# Start interactive mode
fins -i
```

## Example

```
# Create a basket of tech stocks
AAPL MSFT GOOGL AMZN META -> $tech_stocks

# Filter to include only those with market cap > 1 trillion
$tech_stocks -> mcap > 1000B -> $trillion_club

# Add a 5-year CAGR column and sort by it
$trillion_club -> cagr 5y -> sort cagr_5y desc
```

## Documentation

For detailed documentation, see the [MANUAL.md](fins/docs/MANUAL.md) file in the docs directory.

## Project Structure

- **fins/**: Main package directory
  - **dsl/**: Domain-specific language parser and interpreter
  - **entities/**: Core domain entities (Symbol, Basket, etc.)
  - **data_sources/**: Connectors to financial data providers
  - **docs/**: Documentation files

## Proprietary Software

This software is proprietary and confidential. All rights reserved.

## /fins

FINS (Financial Insights and Notation System) is a powerful terminal-based tool for filtering, sorting, and analyzing financial baskets through an intuitive command syntax. Located in the `fins/` directory, it provides a comprehensive set of commands for creating baskets, performing set operations, adding analysis columns, and building complex data flows. The system is designed to help investors efficiently manage and analyze their financial instruments using a functional programming inspired approach.

## /api-keys

The `/api-keys` directory contains configuration files for storing API keys used by various financial data providers. These keys are required to access market data and should be kept secure. The directory is included in `.gitignore` to prevent accidentally committing sensitive credentials.

## /lib

The `/lib` directory contains legacy code from previous versions of the project:

- **v1**: Initial implementation focused on static HTML generation with basic JavaScript search functionality for viewing stock charts
- **v2**: Early prototype of the terminal-based approach that evolved into the current FINS implementation

This code is maintained for reference but is no longer actively developed or used in production.

