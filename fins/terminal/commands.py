from typing import Optional, Union
from fins.entities.basket import Basket
from fins.entities.plugins import Inception
from fins.data_sources import fmp
from fins.financial import Symbol
from fins.terminal.notebook import Notes
from fins.terminal.persistence import Get, Put
from fins.entities.basket_item import BasketItem

# Market cap convenience constants
Million = 1_000_000
Billion = 1_000_000_000
Trillion = 1_000_000_000_000


def Screen(
    mcap_min: Optional[int] = None,
    mcap_max: Optional[int] = None,
    type: str = "all",
    sector: Optional[str] = None,
    industry: Optional[str] = None,
    country: Optional[str] = None,
    exchange: Optional[str] = None,
    limit: int = 1000
) -> Basket:
    """
    Screen stocks using Financial Modeling Prep filters and create a Basket.
    Automatically excludes exotic derivatives (warrants, rights, units) without inception dates.

    Args:
        mcap_min: Minimum market capitalization filter
        mcap_max: Maximum market capitalization filter  
        type: Security type filter ("all", "stock", "etf", "fund")
        sector: Sector filter (e.g., "Technology", "Healthcare")
        industry: Industry filter (e.g., "Software", "Biotechnology")
        country: Country filter (e.g., "US", "CA")
        exchange: Exchange filter (e.g., "NASDAQ", "NYSE") 
        limit: Maximum number of results (default 1000)

    Returns:
        Basket containing the screened symbols with equal weights (excluding derivatives)

    Examples:
        Screen(mcap_min=Billion)  # Large cap stocks (>$1B)
        Screen(mcap_min=5*Billion, mcap_max=50*Billion)  # Mid cap ($5B-$50B)
        Screen(sector="Technology", limit=50)  # Top 50 tech stocks
        Screen(type="etf", exchange="NYSE")  # NYSE ETFs
    """
    tickers = fmp.screen(
        mcap_min=mcap_min,
        mcap_max=mcap_max,
        type=type,
        sector=sector,
        industry=industry,
        country=country,
        exchange=exchange,
        limit=limit
    )

    basket = Basket.from_tickers(tickers)

    # Automatically filter out exotic derivatives without inception dates
    filtered_basket = basket(Inception().not_none()).basket()

    return filtered_basket


def _normalize_symbol(symbol, target_type: type = BasketItem):

    if isinstance(symbol, target_type):
        return symbol

    if target_type == str:
        if isinstance(symbol, Symbol):
            return symbol.symbol
        elif isinstance(symbol, BasketItem):
            return symbol.ticker
        else:
            raise ValueError(f"Unsupported symbol type: {type(symbol)}")
    elif target_type == BasketItem:
        return BasketItem(symbol, amount=1.0)
    elif target_type == Symbol:
        if isinstance(symbol, str):
            return Symbol.get(symbol)
        elif isinstance(symbol, BasketItem):
            return symbol.symbol()
        else:
            raise ValueError(f"Unsupported symbol type: {type(symbol)}")
    raise ValueError(f"Unsupported target type: {target_type}")


def Info(symbol) -> None:
    """
    Display comprehensive information about a symbol including profile and related notes.

    Args:
        symbol: The ticker symbol (str), Symbol, or BasketItem

    Examples:
        Info("AAPL")  # Get info for Apple
        Info(AAPL)    # Get info for Apple Symbol object
        Info(basket_item)  # Get info for BasketItem
    """

    # Get the Symbol object
    symbol_obj = _normalize_symbol(symbol, Symbol)

    if not symbol_obj:
        print(f"✗ Symbol '{symbol}' not found")
        return

    # Display symbol profile information
    print(f"📊 {symbol_obj.ticker} - {symbol_obj.name}")
    print("=" * 50)

    # Basic info
    if symbol_obj.sector:
        print(f"Sector: {symbol_obj.sector}")
    if symbol_obj.industry:
        print(f"Industry: {symbol_obj.industry}")
    if symbol_obj.exchange:
        print(f"Exchange: {symbol_obj.exchange}")
    if symbol_obj.country:
        print(f"Country: {symbol_obj.country}")

    # Market data
    price = symbol_obj.get_data('price')
    if price:
        print(f"Price: ${price:.2f}")

    mcap = symbol_obj.get_data('marketCap')
    if mcap:
        if mcap >= Trillion:
            print(f"Market Cap: ${mcap/Trillion:.2f}T")
        elif mcap >= Billion:
            print(f"Market Cap: ${mcap/Billion:.2f}B")
        elif mcap >= Million:
            print(f"Market Cap: ${mcap/Million:.2f}M")
        else:
            print(f"Market Cap: ${mcap:,.0f}")

    pe_ratio = symbol_obj.get_data('peRatio')
    if pe_ratio:
        print(f"P/E Ratio: {pe_ratio:.2f}")

    # Additional data points
    volume = symbol_obj.get_data('volume')
    if volume:
        print(f"Volume: {volume:,.0f}")

    beta = symbol_obj.get_data('beta')
    if beta:
        print(f"Beta: {beta:.2f}")

    print()  # Empty line before notes

    # Display related notes
    # TODO: make this work
    # print("📝 Related Notes:")
    # print("-" * 30)
    # Notes(symbol=symbol_obj.ticker, return_results=True)


def Fav(symbol, listname: str) -> None:
    """
    Add a symbol to a favorite list.

    Args:
        symbol: The ticker symbol (str), Symbol, or BasketItem
        listname: Name of the favorite list

    Examples:
        Fav("AAPL", "tech_stocks")  # Add Apple to tech_stocks list
        Fav(AAPL, "watchlist")      # Add Apple Symbol to watchlist
    """
    # Load or create the favorite list
    fav_path = f"/fav/{listname}.Basket"
    fav_basket = Get(fav_path)

    if fav_basket is None:
        fav_basket = Basket(name=listname)

    # Add the symbol to the basket
    fav_basket += _normalize_symbol(symbol, BasketItem)

    # Save the updated basket
    Put(fav_basket, f"/fav/{listname}", overwrite=True)


def Unfav(symbol, listname: str) -> None:
    """
    Remove a symbol from a favorite list.

    Args:
        symbol: The ticker symbol (str), Symbol, or BasketItem
        listname: Name of the favorite list

    Examples:
        Unfav("AAPL", "tech_stocks")  # Remove Apple from tech_stocks list
        Unfav(AAPL, "watchlist")      # Remove Apple Symbol from watchlist
    """
    # Load the favorite list
    fav_path = f"/fav/{listname}.Basket"
    fav_basket = Get(fav_path)

    if fav_basket is None:
        print(f"List '{listname}' not found")
        return

    # Remove the symbol from the basket
    fav_basket -= _normalize_symbol(symbol, BasketItem)

    # Save the updated basket
    Put(fav_basket, f"/fav/{listname}", overwrite=True)


def Favs(listname: str) -> Basket:
    """
    Fetch a favorite list basket.

    Args:
        listname: Name of the favorite list

    Returns:
        Basket from "/fav/<listname>.Basket" or None if not found

    Examples:
        Favs("tech_stocks")  # Get tech_stocks basket
        Favs("watchlist")    # Get watchlist basket
    """
    return Get(f"/fav/{listname}.Basket")


def Help():
    """
    Display available FINS terminal commands organized by category.
    Dynamically generates help from function docstrings.

    Returns:
        None (prints help to console)
    """
    from fins.entities import S
    from fins.entities.basket import Basket
    from fins.terminal.persistence import Get, Put, Dir, Delete
    from fins.terminal.notebook import (
        NotePrinciple, NoteObservation, NoteTrade, NoteFact, NoteStrategy,
        Notes, Note, NoteSymbolCmd, AiSync, Ai, AiStatus
    )

    def get_short_desc(func):
        """Extract first line of docstring."""
        if func.__doc__:
            lines = func.__doc__.strip().split('\n')
            return lines[0].strip()
        return "No description available"

    # Command registry organized by category
    command_categories = [
        {
            'icon': '📊',
            'title': 'SCREENING & FILTERING',
            'commands': [
                ('Screen(...)', Screen, 'Screen stocks by filters'),
                ('S("TICKER")', S, None),
                ('Basket([...])', Basket, 'Create a basket of symbols'),
            ],
            'notes': [
                'Market Cap Constants: Million, Billion, Trillion',
                'Example: Screen(mcap_min=5*Billion, mcap_max=50*Billion)'
            ]
        },
        {
            'icon': '🔌',
            'title': 'PLUGINS (Data Enrichment)',
            'intro': 'Available plugins (chain with any Basket):',
            'commands': [
                ('.Inception()', None, 'Add IPO/inception date'),
                ('.MarketCap()', None, 'Add market capitalization'),
                ('.Price()', None, 'Add current stock price'),
                ('.Revenue()', None, 'Add revenue data'),
                ('.RevenueGrowth()', None, 'Add revenue growth metrics'),
                ('.RevenueAcceleration()', None, 'Add revenue acceleration'),
                ('.Profit()', None, 'Add profit metrics'),
                ('.ProfitGrowth()', None, 'Add profit growth metrics'),
                ('.ProfitAcceleration()', None, 'Add profit acceleration'),
                ('.Employees()', None, 'Add employee count'),
                ('.Age()', None, 'Add company age'),
                ('.RAGR()', None, 'Revenue Average Growth Rate'),
                ('.PAGR()', None, 'Profit Average Growth Rate'),
                ('.EBITDA()', None, 'Add EBITDA metrics'),
                ('.NetIncome()', None, 'Add net income'),
                ('.OperatingIncome()', None, 'Add operating income'),
                ('.FreeCashFlow()', None, 'Add free cash flow'),
            ],
            'notes': [
                'Example: Screen(sector="Technology").MarketCap().Price().Revenue()'
            ]
        },
        {
            'icon': '📈',
            'title': 'BASKET OPERATIONS',
            'commands': [
                ('basket.df()', None, 'Convert basket to DataFrame'),
                ('basket.sort(...)', None, 'Sort basket by column'),
                ('basket.filter(...)', None, 'Filter basket by condition'),
                ('basket[...]', None, 'Access items by index/slice'),
            ]
        },
        {
            'icon': '⭐',
            'title': 'FAVORITES',
            'commands': [
                ('Fav(basket, "name")', Fav, None),
                ('Unfav("name")', Unfav, None),
                ('Favs("name")', Favs, None),
            ]
        },
        {
            'icon': '💾',
            'title': 'PERSISTENCE',
            'commands': [
                ('Put(obj, "/path")', Put, None),
                ('Get("/path")', Get, None),
                ('Dir("/path")', Dir, None),
                ('Delete("/path")', Delete, None),
            ]
        },
        {
            'icon': '📝',
            'title': 'NOTEBOOK (Research Notes)',
            'commands': [
                ('NotePrinciple(text)', NotePrinciple, None),
                ('NoteObservation(text)', NoteObservation, None),
                ('NoteTrade(text)', NoteTrade, None),
                ('NoteFact(text)', NoteFact, None),
                ('NoteStrategy(text)', NoteStrategy, None),
                ('NoteSymbol(ticker, text)', NoteSymbolCmd, None),
                ('Notes()', Notes, None),
                ('Note(id)', Note, None),
                ('', None, None),  # Blank line
                ('AiSync()', AiSync, None),
                ('Ai(question)', Ai, None),
                ('AiStatus()', AiStatus, None),
            ]
        },
        {
            'icon': 'ℹ️',
            'title': 'INFORMATION',
            'commands': [
                ('Info("TICKER")', Info, None),
                ('Help()', Help, 'Show this help message'),
            ]
        },
    ]

    # Build help output
    output = []
    output.append(
        '╔══════════════════════════════════════════════════════════════════════════════╗')
    output.append(
        '║                            FINS TERMINAL HELP                                ║')
    output.append(
        '╚══════════════════════════════════════════════════════════════════════════════╝')
    output.append('')

    for category in command_categories:
        # Category header
        output.append(f"{category['icon']} {category['title']}")

        # Category intro
        if 'intro' in category:
            output.append(f"  {category['intro']}")

        # Commands
        for cmd_name, cmd_func, custom_desc in category['commands']:
            # Handle blank lines
            if not cmd_name:
                output.append('')
                continue

            desc = custom_desc if custom_desc else (
                get_short_desc(cmd_func) if cmd_func else '')
            if desc:
                output.append(f"  {cmd_name:<22} - {desc}")
            else:
                output.append(f"  {cmd_name}")

        # Additional notes
        if 'notes' in category:
            for note in category['notes']:
                output.append(f"  {note}")

        output.append('')

    # Python features section
    output.append('🔧 PYTHON FEATURES')
    output.append('  All standard Python features are available:')
    output.append('  - Variables: x = Screen(...)')
    output.append('  - Loops: for item in basket: ...')
    output.append('  - Functions: def my_screen(): ...')
    output.append('  - Import: import pandas as pd')
    output.append('')

    # Tips section
    output.append('💡 TIPS')
    output.append(
        '  - Chain plugins: Screen(...).MarketCap().Price().Revenue()')
    output.append('  - Use tab completion to explore available methods')
    output.append(
        '  - DataFrames support filtering: basket.df()[basket.df()["MarketCap"] > Billion]')
    output.append(
        '  - Save your work: Put(basket, "/my_screens/tech_large_cap")')
    output.append('')

    # Footer
    output.append(
        '═══════════════════════════════════════════════════════════════════════════════')
    output.append(
        'For detailed documentation on any command, use: command_name.__doc__')
    output.append('Example: Screen.__doc__')
    output.append(
        '═══════════════════════════════════════════════════════════════════════════════')

    print('\n'.join(output))
    return None
