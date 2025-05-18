# FINS: Financial Insights and Notation System

FINS (Financial Insights and Notation System) is a powerful terminal-based tool for filtering, sorting, and analyzing financial baskets through an intuitive command syntax. It provides a comprehensive set of commands for creating baskets, performing set operations, adding analysis columns, and building complex data flows.

## Getting Help

FINS provides an integrated help system accessible with the `?` prefix:

```
?                    # Overview and quick reference
? functions          # List all function categories
? functions.columns  # Column-adding functions (.pe, .div, etc)
? functions.filters  # Filter functions (filter, where, etc)
? functions.sorting  # Sorting functions (asc, desc, etc)
? operators          # Operators (+, &, -, etc)
? variables         # Working with variables
? syntax            # Language syntax guide
? examples          # Usage examples
```

## Command Syntax

FINS commands follow a functional programming inspired syntax with a pipeline approach. Commands are chained together using the arrow operator (`->`), creating a _flow_ (= pipeline).

### Basic Syntax

```
COMMAND1 -> COMMAND2 -> COMMAND3 -> ...
```

### Baskets

A basket is a collection of financial symbols (stocks, ETFs, indices) with optional weights. Baskets can be:
- Temporary (prefixed with `$`): Exist until session ends
- Saved (prefixed with `/`): Stored permanently

```
# Creating baskets
AAPL MSFT GOOGL -> $tech        # Store temporary basket
AAPL MSFT GOOGL -> /tech        # Save basket permanently

# Using baskets
$tech                           # Use temporary basket
/tech                          # Use saved basket
/tech/faang                    # Slashes help organize names

# Managing baskets
baskets()                      # List all baskets
baskets("tech*")              # List baskets matching pattern
baskets("/tech/*")            # List all tech baskets
delete($tech)                 # Delete temporary basket
delete(/tech)                 # Delete saved basket

# Weighted baskets
2 AAPL 1 MSFT 3 GOOGL         # Integer weights (2:1:3 ratio)
0.5 AAPL 1.5 MSFT 0.8 GOOGL   # Decimal weights
2x AAPL 0.5x MSFT 3x GOOGL    # Alternative 'x' syntax

# Combining baskets (implicit union)
$tech MSFT 0.7 NFLX $finance  # Mix baskets and symbols

# Name organization examples
/tech/faang                   # Tech FAANG stocks
/tech/semis                   # Tech semiconductor stocks
/etf/growth                   # Growth ETFs
/watchlist/2024/q1           # Q1 2024 watchlist
```

### Column Functions

Column functions add new data columns to your basket. All column functions:
- Start with a dot (`.pe()`, `.div()`)
- Can be assigned custom names (`.ratio = .pe()`)
- Take named arguments for options

```
# Basic column addition
.pe()                           # Add P/E ratio column
.cagr(years=5)                 # Add 5-year CAGR column
.div()                         # Add dividend yield column

# Custom column names
.ratio = .pe()                 # Name the column .ratio
.growth = .cagr(years=5)       # Name the column .growth

# Combining column creation with filtering
.pe() ->                       # First add P/E column
  filter(.pe, min=5, max=30)   # Then filter by P/E range

.cagr(years=5) ->             # Add 5-year CAGR
  filter(.cagr, min=15)       # Filter for high growth stocks

# Multiple columns and filters
.pe() ->                      # Add P/E column
.div() ->                     # Add dividend yield
filter(.pe, max=30) ->        # Filter reasonable P/E
filter(.div, min=2)          # Filter min dividend yield
```

### Column Operations

Operate on existing columns:

```
# Remove columns
drop(.pe, .cagr)               # Remove multiple columns
drop(.ratio)                   # Remove single column

# Hide/Show columns
hide(.pe, .mcap)              # Hide columns from display
show(.pe)                     # Show hidden columns
```

### Sorting and Filtering

Sort and filter using column references:

```
# Sorting
asc(.pe)                      # Sort by PE ratio ascending
asc(.pe, .mcap)               # Sort by PE ratio, then market cap ascending
desc(.pe)                     # Sort by PE ratio descending
desc(.mcap, nulls=last)       # Sort by market cap, nulls at end

# Multiple columns
sort(.sector, .pe)             # Sort by sector, then PE ascending
sort(.mcap, -.div)             # Sort by market cap ascending, then dividend yield descending

# Special sorting
shuffle()                      # Random order
reverse()                      # Reverse current order

# Filtering
filter(.pe, min=0, max=30)    # Filter by PE range
filter(.mcap, min=1000B)      # Filter by market cap
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
```

### Complex Flows

Commands can be chained to create complex data flows:

```
# Create tech basket with PE analysis
AAPL MSFT GOOGL -> 
  + NFLX ->                    # Add NFLX
  .pe() ->                     # Add PE column
  .cagr(years=5) ->           # Add CAGR column
  sort(.pe) ->                 # Sort by PE
  filter(.cagr, min=15) ->    # Filter high growth
  /my_tech_basket             # Save result
```

## Function Reference

### Column Functions (.pe, .div, etc)
Add data columns to your basket. All start with a dot.

```
.pe()                         # Price/Earnings ratio
.cagr(years=5)               # Compound Annual Growth Rate over 5 years
.div()                       # Dividend yield
.mcap()                      # Market capitalization
```

### Filter Functions
Filter rows based on column values.

```
filter(.column, min=val)           # Values >= val
filter(.column, max=val)           # Values <= val
filter(.column, min=a, max=b)      # Values between a and b
filter(.column, above=val)         # Values > val
filter(.column, below=val)         # Values < val
where(.column, in=[a,b,c])        # Values in list
where(.column, like="pattern")     # Pattern matching
```

### Sorting Functions
Control the order of rows.

```
asc(.column)                       # Sort ascending by column
desc(.column)                      # Sort descending by column
asc(.column, nulls=last)          # Sort ascending, nulls at end
desc(.column, nulls=first)        # Sort descending, nulls at start
asc(.col1, .col2)                # Sort by multiple columns ascending
desc(.col1, .col2)               # Sort by multiple columns descending
shuffle()                        # Random order
reverse()                       # Reverse current order
```

### Column Operations
Manage column visibility.

```
# Notes with metadata
@fact(source="https://www.ibm.com/history") 
IBM wasn't founded as a computer company - it started as 
Computing-Tabulating-Recording Company (CTR) in 1911, making 
scales, time recorders, and punch cards.

@trade(date=2024-01-15, price=180, size=100)
Bought AAPL because of strong iPhone sales in China and 
upcoming AI features in iOS 18.

@idea(basket=/tech/faang, tags=[screening, growth])
Screen for companies with:
- High PE but strong growth
- Market leader in their segment
- Strong moat

# Finding notes
notes()                     # List all notes
notes("semiconductor*")     # Full-text search
notes(type=observation)    # Filter by type
notes(since=2024-01)      # Filter by date
notes(basket=/tech/*)      # Notes about tech baskets
notes(tags=[chips])        # Filter by tags

# Quick search shortcuts
@(semiconductor)           # Search all notes for "semiconductor"
@fact(ibm)                # Search facts for "ibm"
@trade(AAPL)              # Search trades for "AAPL"
@(ai chips)               # Search for both terms
@(*difficulty*)           # Pattern matching
```

## Future Extensions

A notes system for capturing trading insights, observations, and knowledge is planned for a future version. This will likely include:
- Different types of notes (observations, principles, trades, etc.)
- Rich metadata support
- Full-text and semantic search
- Integration with the basket system

For now, the focus is on the basket DSL and its core functionality.