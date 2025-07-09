from typing import Optional
from fins.entities.basket import Basket
from fins.entities.plugins import Inception
from fins.data_sources import fmp
from fins.financial import Symbol
from fins.terminal.notebook import Notes

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
    # Extract ticker from symbol parameter
    ticker = None
    if hasattr(symbol, 'ticker'):
        ticker = symbol.ticker
    elif hasattr(symbol, 'symbol'):
        ticker = symbol.symbol
    else:
        ticker = str(symbol)
    
    # Get the Symbol object
    symbol_obj = Symbol.get(ticker)
    
    if not symbol_obj:
        print(f"✗ Symbol '{ticker}' not found")
        return
    
    # Display symbol profile information
    print(f"📊 {ticker} - {symbol_obj.name}")
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
    print("📝 Related Notes:")
    print("-" * 30)
    Notes(symbol=ticker, return_results=True)