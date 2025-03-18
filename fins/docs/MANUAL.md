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
# Simple baskets (equal weights = 1.0)
AAPL MSFT GOOGL                  # Create a basket with three symbols
AAPL MSFT GOOGL -> $tech_basket  # Create a basket and store it in a variable

# Weighted baskets
2 AAPL 1 MSFT 3 GOOGL           # Integer weights (2:1:3 ratio)
0.5 AAPL 1.5 MSFT 0.8 GOOGL     # Decimal weights
2x AAPL 0.5x MSFT 3x GOOGL      # Alternative 'x' syntax, works with decimals too
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
# Pipeline syntax
$tech_basket -> + NFLX           # Add one symbol (weight=1)
$tech_basket -> + 2.5 NFLX       # Add with weight=2.5
$tech_basket -> + 0.5x NFLX      # Same as 0.5 NFLX
$tech_basket -> - MSFT           # Remove symbol

# Shorthand syntax (same effect)
$tech_basket + NFLX              # Add one symbol (weight=1)
$tech_basket + 2.5 NFLX          # Add with weight=2.5
$tech_basket + 0.5x NFLX         # Same as 0.5 NFLX
$tech_basket - MSFT              # Remove symbol

# Multiple symbols with weights
$tech_basket + 0.785 MSFT 17.8 NFLX    # Precise decimal weights
$tech_basket + 2x AAPL 0.5x MSFT       # Mix integers and decimals
```

### Set Operations

Perform set operations between baskets:

```
# Pipeline syntax
$tech_basket -> + $finance_basket  # Union (combine baskets)
$tech_basket -> & $sp500_basket    # Intersection (common symbols)
$tech_basket -> - $exclude_basket  # Subtraction (remove symbols)

# Shorthand syntax (same effect)
$tech_basket + $finance_basket     # Union
$tech_basket & $sp500_basket      # Intersection
$tech_basket - $exclude_basket    # Subtraction

# Mix and match with symbols
$tech_basket + AAPL MSFT $finance_basket  # Add multiple symbols and another basket
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
- `- $other_basket` - Subtraction (remove symbols from first basket that appear in second basket)
- `& $other_basket` - Intersection with another basket

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
- `COLUMN_TYPE as COLUMN_NAME`