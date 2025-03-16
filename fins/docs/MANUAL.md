# FINS: Financial Insights and Notation System

FINS (Financial Insights and Notation System) is a powerful terminal-based tool for filtering, sorting, and analyzing financial baskets through an intuitive command syntax. It provides a comprehensive set of commands for creating baskets, performing set operations, adding analysis columns, and building complex data flows.

## Command Syntax

FINS commands follow a functional programming inspired syntax with a pipeline approach. Commands are chained together using the arrow operator (`->`), creating a _flow_ (= pipeline).

### Basic Syntax

```
COMMAND1 -> COMMAND2 -> COMMAND3 -> ...
```

### Creating Baskets

A basket is a collection of financial symbols (stocks, ETFs, indices) - optionally with weights.

```
AAPL MSFT GOOGL                  # Create a basket with three symbols
AAPL MSFT GOOGL -> $tech_basket  # Create a basket and store it in a variable
```

### Variables

Variables store baskets for later use. There are two types of variables:
- Session variables (prefixed with `$`): Exist only for the current session
- Persistent variables (prefixed with `/`): Stored permanently

```
AAPL MSFT GOOGL -> $tech_basket  # Store in a session variable
AAPL MSFT GOOGL -> /tech_basket  # Store in a persistent variable
AAPL MSFT GOOGL -> /foo/bar      # Store in a persistent variable
$tech_basket                     # Retrieve a session variable
/tech_basket                     # Retrieve a persistent variable
/foo/bar                        # Retrieve a persistent variable
```

### Modifying Baskets

Add or remove symbols from a basket:

```
$tech_basket -> + NFLX           # Add NFLX to the basket
$tech_basket -> - MSFT           # Remove MSFT from the basket
```

### Set Operations

Perform set operations between baskets:

```
$tech_basket -> + $finance_basket  # Union (combine baskets)
$tech_basket -> & $sp500_basket    # Intersection (common symbols)
$tech_basket -> - $exclude_basket  # Difference (remove symbols)
```

### Sorting

Sort a basket by various attributes:

```
$tech_basket -> sort mcap desc     # Sort by market cap in descending order
$tech_basket -> sort pe asc        # Sort by P/E ratio in ascending order
```

### Filtering

Filter a basket based on criteria:

```
$tech_basket -> mcap > 1000B       # Filter by market cap > 1000 billion
$tech_basket -> pe < 20            # Filter by P/E ratio < 20
$tech_basket -> div_yield > 2%     # Filter by dividend yield > 2%
```

### Analysis Columns

Add analysis columns to a basket:

```
$tech_basket -> cagr 5y            # Add 5-year CAGR column
$tech_basket -> pe                 # Add P/E ratio column
$tech_basket -> revenue [2018:2023] # Add revenue column with time range
$tech_basket -> eps quarterly      # Add quarterly EPS column
```

### Complex Flows

Commands can be chained to create complex data flows:

```
AAPL MSFT GOOGL -> + NFLX -> - MSFT -> sort mcap desc -> mcap > 500B -> cagr 5y -> /my_tech_basket
```

This command:
1. Creates a basket with AAPL, MSFT, and GOOGL
2. Adds NFLX to the basket
3. Removes MSFT from the basket
4. Sorts the basket by market cap in descending order
5. Filters to include only symbols with market cap > 500 billion
6. Adds a 5-year CAGR column
7. Stores the result in a persistent variable called "my_tech_basket"

### Function Definitions

Define custom functions for reuse:

```
def high_growth = "mcap > 10B -> cagr 5y > 15%"
$tech_basket -> high_growth        # Apply the function to the basket
```

### Locking Variables

Lock variables to prevent modification:

```
lock $tech_basket                  # Lock a variable
unlock $tech_basket                # Unlock a variable
```

## Command Reference

### Basket Creation
- `SYMBOL1 SYMBOL2 SYMBOL3` - Create a basket with the specified symbols
- `$variable_name` - Retrieve a session variable
- `/variable_name` - Retrieve a persistent variable

### Basket Modification
- `+ SYMBOL` - Add a symbol to the basket
- `- SYMBOL` - Remove a symbol from the basket
- `+ $other_basket` - Union with another basket
- `& $other_basket` - Intersection with another basket
- `- $other_basket` - Difference with another basket

### Sorting
- `sort ATTRIBUTE asc` - Sort by attribute in ascending order
- `sort ATTRIBUTE desc` - Sort by attribute in descending order

### Filtering
- `ATTRIBUTE > VALUE` - Filter where attribute is greater than value
- `ATTRIBUTE < VALUE` - Filter where attribute is less than value
- `ATTRIBUTE >= VALUE` - Filter where attribute is greater than or equal to value
- `ATTRIBUTE <= VALUE` - Filter where attribute is less than or equal to value
- `ATTRIBUTE == VALUE` - Filter where attribute equals value
- `ATTRIBUTE != VALUE` - Filter where attribute does not equal value

### Analysis Columns
- `COLUMN_TYPE` - Add a column of the specified type
- `COLUMN_TYPE [START_YEAR:END_YEAR]` - Add a column with a time range
- `COLUMN_TYPE as COLUMN_NAME` - Add a column with a custom name
- `COLUMN_TYPE quarterly` - Add a column with quarterly data
- `COLUMN_TYPE annual` - Add a column with annual data

### Variable Management
- `lock $variable_name` - Lock a variable to prevent modification
- `unlock $variable_name` - Unlock a variable to allow modification

### Function Management
- `def FUNCTION_NAME = "COMMAND_STRING"` - Define a function
- `FUNCTION_NAME` - Call a function

## Common Attributes

- `mcap` - Market capitalization
- `pe` - Price-to-earnings ratio
- `pb` - Price-to-book ratio
- `ps` - Price-to-sales ratio
- `div_yield` - Dividend yield
- `revenue` - Revenue
- `eps` - Earnings per share
- `debt_to_equity` - Debt-to-equity ratio
- `roe` - Return on equity
- `roa` - Return on assets

## Common Column Types

- `cagr` - Compound annual growth rate
- `pe` - Price-to-earnings ratio
- `pb` - Price-to-book ratio
- `ps` - Price-to-sales ratio
- `div_yield` - Dividend yield
- `revenue` - Revenue
- `eps` - Earnings per share
- `debt_to_equity` - Debt-to-equity ratio
- `roe` - Return on equity
- `roa` - Return on assets

## Examples

### Basic Basket Creation and Filtering

```
# Create a basket of tech stocks
AAPL MSFT GOOGL AMZN META -> $tech_stocks

# Filter to include only those with market cap > 1 trillion
$tech_stocks -> mcap > 1000B -> $trillion_club

# Add a 5-year CAGR column and sort by it
$trillion_club -> cagr 5y -> sort cagr_5y desc
```

### Sector Comparison

```
# Create baskets for different sectors
AAPL MSFT GOOGL AMZN -> $tech
JPM BAC GS MS -> $finance
XOM CVX BP -> $energy

# Add P/E ratio column to each
$tech -> pe -> $tech_pe
$finance -> pe -> $finance_pe
$energy -> pe -> $energy_pe

# Compare average P/E ratios
$tech_pe -> avg pe
$finance_pe -> avg pe
$energy_pe -> avg pe
```

### Complex Analysis

```
# Start with S&P 500 ETF and expand to constituents
SPY -> spread -> $sp500

# Filter to include only dividend aristocrats with yield > 2%
$sp500 -> div_aristocrat == true -> div_yield > 2% -> $dividend_aristocrats

# Add analysis columns
$dividend_aristocrats -> div_growth 10y -> payout_ratio -> $dividend_analysis

# Sort by dividend growth rate
$dividend_analysis -> sort div_growth_10y desc
```

## Advanced Usage

### Combining Multiple Data Sources

```
# Get data from multiple sources
$basket -> add_source fmp -> add_source yahoo -> add_source nasdaq
```

### Custom Calculations

# Command Syntax and Flow

## Basic Command Structure

Commands in FINS follow a consistent structure and can be invoked in two ways:

### Implicit (Pipeline) Syntax
```
[inputs] -> command [arguments]
```

### Explicit Syntax
```
[input] command [arguments]
```

For example:
```
# Implicit syntax
AAPL MSFT GOOGL -> sort mcap desc
$tech_stocks -> pe < 20

# Explicit syntax
$tech_stocks + NFLX
$tech_stocks sort pe
```

## Command Types

FINS supports several command types:

1. **Column Commands**: Add data columns and optionally filter
   - Analysis columns: `basket -> pe` (adds a PE column)
   - Filters: `basket -> pe < 20` (adds PE column and filters)
   - The same command can do both operations

2. **Manipulation Commands**: Transform baskets
   - Sort: `basket -> sort mcap desc`
   - Set operations: `$tech_stocks + NFLX`

## Command Flow

Each command in FINS processes inputs and produces an output that can be used by the next command:

1. **Inputs**: Can come from:
   - Previous command's output (automatically passed)
   - Direct symbol lists (AAPL MSFT GOOGL)
   - Variables ($tech_stocks)
   - Multiple inputs separated by spaces

2. **Arguments**: Follow the command name and can be:
   - Column names (mcap, pe)
   - Sort orders (asc, desc)
   - Numbers (100, 1000B)
   - Comparison operators (>, <, =)
   - Variables ($min_pe)

## Examples

### Analysis Columns and Filters
```
# Add PE column to basket
AAPL MSFT GOOGL -> pe

# Add PE column and filter to PE < 20
AAPL MSFT GOOGL -> pe < 20

# Equivalent explicit syntax
$stocks pe < 20
```

### Symbol Addition
```
# Add NFLX to tech stocks (implicit syntax)
$tech_stocks -> + NFLX

# Equivalent explicit syntax
$tech_stocks + NFLX
```

### Multiple Operations and Storage
```
# Filter by PE, add to variable, then sort by market cap
$all_stocks -> pe < 20 -> $value_stocks -> sort mcap desc
```

## Command Output

Every command produces an output that can be:
- Used as input to the next command
- Stored in a variable
- Displayed in the terminal

The output format depends on:
- The command type (e.g., sort produces a sorted basket)
- Whether JSON output is requested (--json flag)
- Whether the result is being stored (-> $var) 