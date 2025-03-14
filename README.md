# Stock Screener Terminal Manual

Welcome to the **Stock Screener Terminal** manual. This guide provides comprehensive instructions on using the terminal's syntax to create, manipulate, and analyze stock portfolios efficiently. Whether you're building simple portfolios or complex pipelines, this manual will help you leverage the terminal's full capabilities.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Syntax Overview](#2-syntax-overview)
    - [2.1. Symbols and Variables](#21-symbols-and-variables)
    - [2.2. Operators](#22-operators)
    - [2.3. Command Structure](#23-command-structure)
3. [Basic Commands](#3-basic-commands)
    - [3.1. Getting Information on Symbols](#31-getting-information-on-symbols)
    - [3.2. Creating Portfolios](#32-creating-portfolios)
4. [Modifying Portfolios](#4-modifying-portfolios)
    - [4.1. Adding Symbols](#41-adding-symbols)
    - [4.2. Removing Symbols](#42-removing-symbols)
    - [4.3. Set Operations](#43-set-operations)
5. [Transformations and Filters](#5-transformations-and-filters)
    - [5.1. Sorting](#51-sorting)
    - [5.2. Filtering](#52-filtering)
    - [5.3. Time Range Selectors](#53-time-range-selectors)
6. [Adding Columns](#6-adding-columns)
7. [Defining and Using Functions](#7-defining-and-using-functions)
    - [7.1. Defining Functions](#71-defining-functions)
    - [7.2. Using Functions](#72-using-functions)
8. [Variable Management](#8-variable-management)
    - [8.1. Locking Variables](#81-locking-variables)
    - [8.2. Unlocking Variables](#82-unlocking-variables)
9. [Examples](#9-examples)
    - [Example 1: Creating a Simple Portfolio](#example-1-creating-a-simple-portfolio)
    - [Example 2: Adding Symbols to a Portfolio](#example-2-adding-symbols-to-a-portfolio)
    - [Example 3: Sorting a Portfolio](#example-3-sorting-a-portfolio)
    - [Example 4: Filtering a Portfolio](#example-4-filtering-a-portfolio)
    - [Example 5: Adding Columns to a Portfolio](#example-5-adding-columns-to-a-portfolio)
    - [Example 6: Using Functions](#example-6-using-functions)
    - [Example 7: Creating a Complex Pipeline](#example-7-creating-a-complex-pipeline)
10. [Reference](#10-reference)
    - [10.1. Operators](#101-operators)
    - [10.2. Commands](#102-commands)
    - [10.3. Variable Types](#103-variable-types)
    - [10.4. Function Definition Syntax](#104-function-definition-syntax)
    - [10.5. Time Range Selector Syntax](#105-time-range-selector-syntax)
    - [10.6. Number Shortcuts](#106-number-shortcuts)
11. [Final Notes](#11-final-notes)

---

## 1. Introduction

The **Stock Screener Terminal** is a powerful tool designed to help you filter, sort, and manage stock portfolios through a concise and intuitive syntax. Inspired by functional programming and set theory, the terminal allows you to build pipelines that process portfolios step-by-step, enabling detailed analysis and optimization based on various financial metrics.

This manual will guide you through the terminal's syntax, commands, and features, enabling you to harness its full potential.

---

## 2. Syntax Overview

Understanding the core syntax is essential for effectively using the Stock Screener Terminal. This section covers the fundamental components, including symbols, variables, operators, and the general command structure.

### 2.1. Symbols and Variables

#### **Symbols**

- **Stock Symbol:** Represents an individual stock.  
  *Example:* `AAPL`, `GOOGL`, `MSFT`

- **Fund Symbol:** Represents an ETF or mutual fund.  
  *Example:* `ETF1`, `VTI`

- **Index Symbol:** Represents a market index, prefixed with `^`.  
  *Example:* `^SPX`, `^GSPC`

#### **Variables**

All variables store **portfolios**, which are lists of stock symbols with associated weights.

- **Non-Persistent Variables:** Prefixed with `$`.  
  *Examples:* `$A`, `$B`

- **Persistent Variables:** Prefixed with `/` or deeper paths.  
  *Examples:* `/A`, `/B`, `/foo/bar`

- **Function Variables:** Prefixed with `!`.  
  *Examples:* `!f`

**Notes:**

- A **single symbol** is considered a portfolio with one item.
- A **list of symbols** is a portfolio with equal weights.
- All variables represent portfolios; there are no other data types.

### 2.2. Operators

Operators allow you to perform various operations on portfolios.

- **Spread/Constituents Operator (`..`):**  
  - **Usage:** `..Symbol`  
  - **Function:** Expands a symbol (like an ETF or Index) into its constituents.  
  - **Precedence:** Highest (due to being glued to the symbol without a space).  
  - **Example:** `..ETF1` expands `ETF1` into its underlying stocks.

- **Union Operator (`+`):**  
  - **Usage:** `+ PortfolioOrSymbol`  
  - **Function:** Combines the current portfolio with another portfolio or symbol.  
  - **Precedence:** Left-to-right.

- **Difference Operator (`-`):**  
  - **Usage:** `- PortfolioOrSymbol`  
  - **Function:** Removes all elements in the specified portfolio or symbol from the current portfolio.  
  - **Precedence:** Left-to-right.

- **Intersection Operator (`&`):**  
  - **Usage:** `& PortfolioOrSymbol`  
  - **Function:** Creates a new portfolio containing only elements present in both the current and specified portfolios.  
  - **Precedence:** Left-to-right.

- **Assignment/Pipe Operator (`->`):**  
  - **Usage:** `-> Variable`  
  - **Function:** Pipes the result of an operation to the next step and optionally stores it into a variable.  
  - **Precedence:** Right-to-left.  
  - **Note:** It is the **only piping operator**, passing the result of each step to the next.

- **Grouping Parentheses (`(` and `)`):**  
  - **Usage:** `(Operation)`  
  - **Function:** Defines explicit precedence in operations.  
  - **Example:** `(STOCK1 + STOCK2) & ETF1`

### 2.3. Command Structure

Commands are executed in a pipeline fashion, where the output of one command serves as the input to the next. The general structure follows:

```
Input -> Operation1 -> Operation2 -> ... -> Output
```

- **Input:** Can be a single symbol, a list of symbols, or a variable.
- **Operation:** Can be an operator (`+`, `-`, `&`, `..`) or a command (`sort`, `filter`, etc.).
- **Output:** The result is passed to the next operation and can be optionally stored in a variable using the `->` operator.

**Example:**

```
MSFT AAPL -> $A -> + META -> $THREE -> sort mcap desc -> /THREESORTED
```

In this example:

1. **Combine `MSFT` and `AAPL` into `$A`.**
2. **Add `META` to `$A`, resulting in `$THREE`.**
3. **Sort `$THREE` by market capitalization in descending order, storing the sorted portfolio in `/THREESORTED`.**

---

## 3. Basic Commands

Basic commands involve retrieving information about symbols and creating initial portfolios.

### 3.1. Getting Information on Symbols

Retrieve detailed information about a specific stock, ETF, or index.

- **Get Info on a Stock:**

    ```
    : STOCK1
    ```

- **Get Info on a Fund:**

    ```
    : ETF1
    ```

**Examples:**

```
: AAPL
: VTI
```

### 3.2. Creating Portfolios

Combine multiple symbols into a single portfolio.

- **Combine Two Symbols:**

    ```
    : STOCK1 STOCK2
    ```

- **Build a Portfolio and Store in a Variable:**

    ```
    : STOCK1 STOCK2 -> $A
    ```

- **Build a Persistent Portfolio:**

    ```
    : STOCK1 STOCK2 -> /A
    ```

**Examples:**

```
: AAPL MSFT -> $TechPortfolio
: AAPL MSFT VTI -> /MyPortfolio
```

---

## 4. Modifying Portfolios

Once portfolios are created, you can modify them by adding or removing symbols and performing set operations.

### 4.1. Adding Symbols

Add symbols to an existing portfolio using the `+` operator or the `..` operator for expansion.

- **Add a Single Symbol:**

    ```
    : + META -> $A
    ```

- **Add All Elements from Another Portfolio:**

    ```
    : + $B -> $A
    ```

- **Expand and Add Constituents of an ETF or Index:**

    ```
    : ..ETF1 -> $A
    : ..^SPX -> $A
    ```

**Examples:**

```
: + GOOGL -> $TechPortfolio
: + $AdditionalStocks -> $TechPortfolio
: ..VTI -> $TechETF
: ..^SPX -> $MarketIndex
```

**Explanation:**

- **`+ META`:** Adds the `META` symbol to the current portfolio.
- **`+ $B`:** Adds all symbols from portfolio `$B` to the current portfolio `$A`.
- **`..VTI`:** Expands ETF `VTI` into its constituent stocks and adds them to the portfolio.
- **`..^SPX`:** Expands the S&P 500 index (`^SPX`) into its constituent stocks and adds them to the portfolio.

### 4.2. Removing Symbols

Remove symbols from an existing portfolio using the `-` operator.

- **Remove a Single Symbol:**

    ```
    : - MSFT -> $A
    ```

- **Remove All Elements in Another Portfolio:**

    ```
    : - $B -> $A
    ```

**Examples:**

```
: - MSFT -> $TechPortfolio
: - $ExcludedStocks -> $MyPortfolio
```

**Explanation:**

- **`- MSFT`:** Removes the `MSFT` symbol from the current portfolio.
- **`- $ExcludedStocks`:** Removes all symbols present in portfolio `$ExcludedStocks` from `$A`.

### 4.3. Set Operations

Perform set-based operations like union, intersection, and difference.

- **Union (`+`):** Combines the current portfolio with another portfolio or symbol.

    ```
    : + $B -> $A
    ```

- **Intersection (`&`):** Retains only common elements between the current portfolio and another.

    ```
    : & $B -> $A
    ```

- **Difference (`-`):** Removes elements of one portfolio from the current portfolio.

    ```
    : - $B -> $A
    ```

**Examples:**

```
: + $Healthcare -> $CombinedPortfolio
: & $SPX -> $FilteredPortfolio
: - $ExcludedStocks -> $FinalPortfolio
```

**Explanation:**

- **`+ $Healthcare`:** Unites the current portfolio with `$Healthcare`, resulting in `$CombinedPortfolio`.
- **`& $SPX`:** Intersects the current portfolio with the S&P 500 index portfolio (`^SPX`), resulting in `$FilteredPortfolio`.
- **`- $ExcludedStocks`:** Removes all symbols in `$ExcludedStocks` from the current portfolio, resulting in `$FinalPortfolio`.

---

## 5. Transformations and Filters

Transformations modify the portfolio's data, while filters refine the portfolio based on specific criteria.

### 5.1. Sorting

Sort the portfolio based on a specified attribute.

- **Sort Command Structure:**

    ```
    : sort attribute order -> OutputVariable
    ```

    - **`attribute`:** The attribute to sort by (e.g., `mcap`, `price`).
    - **`order`:** The order of sorting (`asc` for ascending, `desc` for descending).

- **Example: Sort by Market Capitalization (Descending):**

    ```
    : sort mcap desc -> $ASorted
    ```

**Available Sort Attributes:**

- `mcap` : Market Capitalization
- `price` : Stock Price
- `volume` : Trading Volume
- *(Add more as needed)*

**Example:**

```
: sort mcap desc -> $TechSorted
```

**Explanation:**

- **`sort mcap desc`:** Sorts the current portfolio by market capitalization in descending order.
- **`-> $TechSorted`:** Stores the sorted portfolio in `$TechSorted`.

### 5.2. Filtering

Filter the portfolio based on specific criteria using comparison operators.

- **Filter Command Structure:**

    ```
    : filter_command operator value -> OutputVariable
    ```

    - **`filter_command`:** The attribute to filter by (e.g., `mcap`, `volume`).
    - **`operator`:** The comparison operator (`>`, `<`, `=`).
    - **`value`:** The value to compare against.

    - **Note:** The previous step's result is implicitly the left argument.

- **Example: Filter by Market Capitalization Greater Than 10,000:**

    ```
    : mcap > 10000 -> $ABig
    ```

**Available Comparison Operators:**

- `>` : Greater Than
- `<` : Less Than
- `=` : Equal To

**Example:**

```
: volume > 1000000 -> $HighVolume
```

**Important:**  
Filters are distinguished from column addition commands by the presence of comparison operators (`>`, `<`, `=`) immediately following the command name.

**Explanation:**

- **`mcap > 10000`:** Filters the current portfolio to include only stocks with `mcap > 10000`.
- **`-> $ABig`:** Stores the filtered portfolio in `$ABig`.
- **`volume > 1000000`:** Filters the current portfolio to include only stocks with a trading volume greater than 1,000,000.
- **`-> $HighVolume`:** Stores the filtered portfolio in `$HighVolume`.

### 5.3. Time Range Selectors

Specify a time range for commands that support it using the `[:]` syntax, similar to Python.

- **Time Range Selector Syntax:**

    ```
    [StartYear:EndYear]
    ```

    - **`StartYear`:** The starting year (inclusive).
    - **`EndYear`:** The ending year (inclusive).

- **Example: Focus CAGR on Years 2010 to 2015:**

    ```
    : cagr [2010:2015] -> $CAGR2010to2015
    ```

**Explanation:**

- **`cagr [2010:2015]`:** Calculates the Compound Annual Growth Rate for the years 2010 through 2015.
- **`-> $CAGR2010to2015`:** Stores the result in `$CAGR2010to2015`.

**Note:**  
Functions that calculate additional columns should always allow for such selectors to focus on specific time ranges.

---

## 6. Adding Columns

Enhance your portfolio with additional financial metrics by adding new columns, similar to performing a left join.

- **Add Column Command Structure:**

    ```
    : [|ColumnName] command [time_range] argument -> OutputVariable
    ```

    - **`|ColumnName` (optional):** Names the column being added.
    - **`command`:** The column to add (e.g., `cagr`, `dividend`).
    - **`time_range` (optional):** Specifies the time range using `[:]` syntax.
    - **`argument`:** Additional arguments required by the command.

- **Examples:**

    - **Without Naming Operator (Default Column Name):**

        ```
        : cagr 10y -> $A
        ```

    - **With Naming Operator:**

        ```
        : |cagr10 cagr [2010:2020] -> $A
        ```

**Common Column Commands:**

- `cagr` : Compound Annual Growth Rate  
  **Usage:** `cagr [start_year:end_year] <period>`  
  **Example:** `cagr [2010:2020] 5y`

- `dividend` : Dividend Yield  
  **Usage:** `dividend [start_year:end_year] <period>`  
  **Example:** `dividend [2015:2020] 1y`

- `pe` : Price-to-Earnings Ratio  
  **Usage:** `pe`  
  **Example:** `pe`

**Explanation:**

- **`cagr [2010:2020] 5y`:** Adds a 5-year CAGR column focusing on the years 2010 to 2020.
- **`|cagr10 cagr [2010:2020]`:** Adds a CAGR column named `cagr10` focusing on the years 2010 to 2020.
- **`pe`:** Adds the Price-to-Earnings Ratio column with the default name `pe`.

**Shortcut for Recent Years:**

- **`cagr 10y`:** Automatically selects the time range "from 10 years ago until now."

**Example:**

```
cagr 10y
```

**Explanation:**

- **`cagr 10y`:** Calculates the 10-year CAGR for the period from 10 years ago to the current date.

**Note:**  
All data in the system is monthly, so time ranges are based on monthly intervals.

**Alternative Example Without Naming Operator (Default Column Name):**

```
: cagr 10y -> $A
```

**Explanation:**

- **`cagr 10y`:** Adds a 10-year CAGR column to the current portfolio, using the default column name `cagr`.
- **`-> $A`:** Stores the updated portfolio in `$A`.

**Example:**

```
: |cagr10 cagr [2010:2020] -> $A
: pe -> $TechWithPE
```

---

## 7. Defining and Using Functions

Functions allow you to create reusable command templates, simplifying complex or repetitive tasks.

### 7.1. Defining Functions

- **Function Definition Syntax:**

    ```
    DEFINE !FunctionName = "Command Sequence"
    ```

    - **`!FunctionName`:** The name of the function, prefixed with `!`.
    - **`"Command Sequence"`:** The sequence of commands the function will execute.

- **Example: Define a Function to Filter by Market Cap and Add CAGR:**

    ```
    DEFINE !HighCapCAGR = "mcap > 10000 -> cagr [2010:2020] 10y"
    ```

**Explanation:**

- **`DEFINE`:** Keyword used to define a new function.
- **`!HighCapCAGR`:** Name of the function.
- **`"mcap > 10000 -> cagr [2010:2020] 10y"`:** Command sequence that filters for `mcap > 10000` and adds a 10-year CAGR focused on 2010 to 2020.

### 7.2. Using Functions

- **Function Usage Syntax:**

    ```
    : !FunctionName -> OutputVariable
    ```

    - **`!FunctionName`:** The function to execute.
    - **`-> OutputVariable`:** Stores the result of the function into a variable.

- **Example: Apply the `!HighCapCAGR` Function:**

    ```
    : !HighCapCAGR -> $ABigCAGR
    ```

**Explanation:**

- **`!HighCapCAGR`:** Invokes the predefined function which filters the portfolio by `mcap > 10000` and adds a 10-year CAGR column focused on 2010 to 2020.
- **`-> $ABigCAGR`:** Stores the result of the function in `$ABigCAGR`.

**Example Workflow:**

1. **Define the Function:**

    ```
    DEFINE !FilterAndCAGR = "mcap > 10000 -> cagr [2010:2020] 10y"
    ```

2. **Use the Function in a Pipeline:**

    ```
    : $TechPortfolio -> !FilterAndCAGR -> $FilteredPortfolio
    ```

**Explanation:**

- **`!FilterAndCAGR`:** Invokes the predefined function which filters the portfolio by `mcap > 10000` and adds a 10-year CAGR column focused on 2010 to 2020.
- **`-> $FilteredPortfolio`:** Stores the result of the function in `$FilteredPortfolio`.

**Note:**  
Functions (`!f`) act as template strings that can be inserted into command pipelines, enhancing reusability and readability.

---

## 8. Variable Management

Efficient management of variables ensures data integrity and prevents unintended modifications.

### 8.1. Locking Variables

Locking a variable protects it from being modified accidentally.

- **Lock Variable Syntax:**

    ```
    lock $VariableName
    ```

    - **`$VariableName`:** The variable to be locked.

- **Example: Locking a Non-Persistent Variable:**

    ```
    lock $A
    ```

**Usage Example:**

```
: AAPL MSFT -> $A
lock $A
: + META -> $A  # This will fail if $A is locked
```

**Explanation:**

- **`lock $A`:** Locks variable `$A`, preventing any further modifications.
- **Attempting to add `META` to `$A` while locked will fail.

### 8.2. Unlocking Variables

Unlocking a variable removes the write protection, allowing modifications.

- **Unlock Variable Syntax:**

    ```
    unlock $VariableName
    ```

    - **`$VariableName`:** The variable to be unlocked.

- **Example: Unlocking a Non-Persistent Variable:**

    ```
    unlock $A
    ```

**Usage Example:**

```
: AAPL MSFT -> $A
lock $A
: + META -> $A  # This will fail if $A is locked
unlock $A
: + META -> $A  # Now succeeds
```

**Explanation:**

- **`unlock $A`:** Unlocks variable `$A`, allowing modifications.
- **Subsequent addition of `META` to `$A` will now succeed.

---

## 9. Examples

This section provides practical examples to illustrate how to use the Stock Screener Terminal effectively. Each example builds upon the previous ones, demonstrating various features and commands.

### Example 1: Creating a Simple Portfolio

**Objective:**  
Create a portfolio containing Microsoft (`MSFT`) and Apple (`AAPL`), and store it in `$A`.

**Commands:**

```
: MSFT AAPL -> $A
```

**Explanation:**

- **`MSFT AAPL`:** Combines `MSFT` and `AAPL` into a portfolio.
- **`-> $A`:** Stores the resulting portfolio in variable `$A`.

**Result:**  
Variable `$A` now contains a portfolio with `MSFT` and `AAPL`, each with equal weights.

---

### Example 2: Adding Symbols to a Portfolio

**Objective:**  
Add Meta (`META`) to the existing portfolio `$A` and store the updated portfolio in `$THREE`.

**Commands:**

```
: + META -> $THREE
```

**Explanation:**

- **`+ META`:** Adds the `META` symbol to the current portfolio (implicitly `$A`).
- **`-> $THREE`:** Stores the updated portfolio in `$THREE`.

**Result:**  
Variable `$THREE` now contains `MSFT`, `AAPL`, and `META`.

---

### Example 3: Sorting a Portfolio

**Objective:**  
Sort the portfolio `$A` by market capitalization in descending order and store the sorted portfolio in `$ASorted`.

**Commands:**

```
: sort mcap desc -> $ASorted
```

**Explanation:**

- **`sort mcap desc`:** Sorts the current portfolio by market capitalization in descending order.
- **`-> $ASorted`:** Stores the sorted portfolio in `$ASorted`.

**Result:**  
Variable `$ASorted` contains the symbols from `$A` sorted by market capitalization in descending order.

---

### Example 4: Filtering a Portfolio

**Objective:**  
Filter the portfolio `$A` to include only stocks with a market capitalization greater than 10,000 and store the result in `$ABig`.

**Commands:**

```
: mcap > 10000 -> $ABig
```

**Explanation:**

- **`mcap > 10000`:** Filters the current portfolio to include only stocks with `mcap > 10000`.
- **`-> $ABig`:** Stores the filtered portfolio in `$ABig`.

**Result:**  
Variable `$ABig` contains only the stocks from `$A` with a market capitalization greater than 10,000.

---

### Example 5: Adding Columns to a Portfolio

**Objective:**  
Add a 5-year Compound Annual Growth Rate (CAGR) column to the portfolio `$ABig` and store the updated portfolio in `$ABigCAGR`.

**Commands:**

```
: |cagr5 cagr [2015:2020] 5y -> $ABigCAGR
```

**Explanation:**

- **`|cagr5`:** Names the new column `cagr5`.
- **`cagr [2015:2020] 5y`:** Calculates the 5-year CAGR focusing on the years 2015 to 2020.
- **`-> $ABigCAGR`:** Stores the updated portfolio with the CAGR column in `$ABigCAGR`.

**Result:**  
Variable `$ABigCAGR` now includes the `cagr5` column with CAGR data for each stock in `$ABig`.

**Alternative Example Without Naming Operator (Default Column Name):**

```
: cagr 10y -> $A
```

**Explanation:**

- **`cagr 10y`:** Adds a 10-year CAGR column to the current portfolio, using the default column name `cagr`.
- **`-> $A`:** Stores the updated portfolio in `$A`.

**Result:**  
Variable `$A` now includes the `cagr` column with 10-year CAGR data for each stock.

---

### Example 6: Using Functions

**Objective:**  
Define a function to filter by market cap and add CAGR, then apply it to multiple portfolios.

**Commands:**

1. **Define the Function:**

    ```
    DEFINE !FilterAndCAGR = "mcap > 10000 -> cagr [2010:2020] 10y"
    ```

2. **Apply the Function to Portfolio `$A`:**

    ```
    : $A -> !FilterAndCAGR -> $FilteredA
    ```

3. **Apply the Function to Portfolio `$B`:**

    ```
    : $B -> !FilterAndCAGR -> $FilteredB
    ```

**Explanation:**

- **Function Definition:**
    - **`DEFINE`:** Keyword to define a new function.
    - **`!FilterAndCAGR`:** Name of the function.
    - **`"mcap > 10000 -> cagr [2010:2020] 10y"`:** Command sequence that filters for `mcap > 10000` and adds a 10-year CAGR focused on 2010 to 2020.

- **Function Usage:**
    - **`$A -> !FilterAndCAGR -> $FilteredA`:** Applies the `!FilterAndCAGR` function to `$A`, storing the result in `$FilteredA`.
    - **`$B -> !FilterAndCAGR -> $FilteredB`:** Applies the same function to `$B`, storing the result in `$FilteredB`.

**Result:**  
Variables `$FilteredA` and `$FilteredB` contain portfolios from `$A` and `$B` respectively, filtered by market cap and enhanced with a 10-year CAGR column.

---

### Example 7: Creating a Complex Pipeline

**Objective:**  
Create a complex pipeline that combines portfolios, filters, adds columns, sorts, and stores results persistently.

**Commands:**

```
: MSFT AAPL -> $A -> + META -> $THREE -> sort mcap desc -> /THREESORTED
```

**Explanation:**

1. **Create Initial Portfolio:**
    - **`MSFT AAPL`:** Combines `MSFT` and `AAPL` into a portfolio.
    - **`-> $A`:** Stores the resulting portfolio in `$A`.

2. **Add `META` to the Portfolio:**
    - **`+ META`:** Adds `META` to `$A`.
    - **`-> $THREE`:** Stores the updated portfolio in `$THREE`.

3. **Sort the Portfolio by Market Cap Descending:**
    - **`sort mcap desc`:** Sorts `$THREE` by market capitalization in descending order.
    - **`-> /THREESORTED`:** Stores the sorted portfolio persistently in `/THREESORTED`.

**Result:**  
Persistent variable `/THREESORTED` contains a sorted portfolio with `MSFT`, `AAPL`, and `META` sorted by market capitalization in descending order.

---

## 10. Reference

### 10.1. Operators

| Operator          | Symbol | Description                                                    |
|-------------------|--------|----------------------------------------------------------------|
| Union             | `+`    | Combines the current portfolio with another portfolio or symbol.|
| Difference        | `-`    | Removes elements of the specified portfolio or symbol from the current portfolio.|
| Intersection      | `&`    | Retains only common elements between the current and specified portfolios.|
| Spread/Constituents| `..`  | Expands a symbol into its constituents.                        |
| Assignment/Pipe   | `->`   | Pipes the result of an operation to the next step and optionally stores it into a variable.|
| Grouping          | `(` `)`| Defines explicit precedence in operations.                     |

### 10.2. Commands

| Command    | Description                                       | Example                          |
|------------|---------------------------------------------------|----------------------------------|
| `sort`     | Sorts the portfolio based on an attribute and order.| `sort mcap desc`                 |
| `mcap`     | Filters based on market capitalization.           | `mcap > 10000`                   |
| `volume`   | Filters based on trading volume.                  | `volume > 1000000`               |
| `cagr`     | Adds Compound Annual Growth Rate column.          | `cagr [2010:2020] 10y`            |
| `dividend` | Adds Dividend Yield column.                       | `dividend [2015:2020] 1y`         |
| `pe`       | Adds Price-to-Earnings Ratio column.              | `pe`                              |

### 10.3. Variable Types

- **Non-Persistent Variables (`$`):** Temporary portfolios that exist during the session.
- **Persistent Variables (`/`):** Saved portfolios that persist across sessions.
- **Function Variables (`!`):** Reusable command templates.

### 10.4. Function Definition Syntax

```
DEFINE !FunctionName = "Command Sequence"
```

**Example:**

```
DEFINE !HighCap = "mcap > 50000"
```

### 10.5. Time Range Selector Syntax

```
[StartYear:EndYear]
```

- **`StartYear`:** The starting year (inclusive).
- **`EndYear`:** The ending year (inclusive).

**Example:**

```
cagr [2010:2015] 5y
```

**Explanation:**

- **`cagr [2010:2015] 5y`:** Calculates the 5-year CAGR focusing on the years 2010 to 2015.

**Shortcut for Recent Years:**

- **`cagr 10y`:** Automatically selects the time range "from 10 years ago until now."

**Example:**

```
cagr 10y
```

**Explanation:**

- **`cagr 10y`:** Calculates the 10-year CAGR for the period from 10 years ago to the current date.

**Note:**  
All data in the system is monthly, so time ranges are based on monthly intervals.

### 10.6. Number Shortcuts

To simplify the entry of large numbers, the terminal supports shorthand notations using the following suffixes:

| Shortcut | Meaning      | Example Usage    |
|----------|--------------|-------------------|
| `T`      | Trillion     | `1T` (1,000,000,000,000) |
| `B`      | Billion      | `10B` (10,000,000,000)    |
| `M`      | Million      | `7M` (7,000,000)          |
| `K`      | Thousand     | `57K` (57,000)            |

**Usage Examples:**

- **Filtering by Market Cap Greater Than 1 Trillion:**

    ```
    : mcap > 1T -> $LargeCap
    ```

- **Filtering by Volume Greater Than 500 Million:**

    ```
    : volume > 500M -> $HighVolume
    ```

- **Setting a Threshold of 100 Thousand for Another Metric:**

    ```
    : some_metric > 100K -> $MetricHigh
    ```

**Explanation:**

- **`1T`:** Represents 1 Trillion.
- **`10B`:** Represents 10 Billion.
- **`7M`:** Represents 7 Million.
- **`57K`:** Represents 57 Thousand.

**Note:**  
These shortcuts can be used in any command that requires numerical values, making command entry more efficient and readable.

---

## 11. Final Notes

The **Stock Screener Terminal** is designed for flexibility and efficiency in managing stock portfolios. By leveraging the functional pipeline approach, you can build pipelines that filter, sort, and enhance your portfolios step-by-step with minimal effort.

**Key Takeaways:**

- **Chaining Commands:** Use the `->` operator to build pipelines that process data sequentially. Each `->` passes the result of the previous operation to the next.
- **Set Operations:** Utilize `+`, `-`, and `&` to combine and refine portfolios.
- **Functions:** Define reusable functions with `!` to streamline repetitive tasks.
- **Variable Management:** Use `lock` and `unlock` to protect critical portfolios from unintended changes.
- **Extensibility:** Although transformations and filters are hardcoded, the syntax allows for robust pipeline creation to meet diverse analysis needs.

**Best Practices:**

- **Start Simple:** Begin with basic commands to familiarize yourself with the syntax before moving to complex pipelines.
- **Use Descriptive Variable Names:** Clearly name your variables to reflect their contents and purpose.
- **Leverage Functions:** Create functions for common operations to save time and maintain consistency.
- **Document Your Pipelines:** Keep track of your command sequences for future reference and troubleshooting.

**Recommendations:**

1. **Consistency in Operator Usage:**
   - Ensure that all operators behave consistently across different contexts to avoid confusion.
   - Use parentheses to manage complex expressions and define explicit precedence when necessary.

2. **User-Friendly Error Messages:**
   - Implement comprehensive error handling with descriptive messages to guide you in correcting your queries.

3. **Comprehensive Documentation:**
   - Keep this manual updated with new features, commands, and examples to help you maximize the potential of your stock screener.

4. **User Feedback and Iteration:**
   - Continuously refine the syntax and features based on your usage patterns and needs to ensure the tool remains intuitive and powerful.

5. **Testing and Validation:**
   - Regularly test your command pipelines to ensure reliability and correctness, especially for complex operations.

6. **Extensibility for Future Features:**
   - Design your pipelines and functions with future enhancements in mind, allowing for easy integration of new operators, commands, and features as your analysis needs evolve.

By following this manual and incorporating these best practices, you can effectively utilize the Stock Screener Terminal to manage and optimize your stock portfolios with precision and ease.

Happy Screening!