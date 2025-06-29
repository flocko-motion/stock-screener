from typing import Optional
from fins.entities.basket import Basket
from fins.entities.plugins import Inception
from fins.data_sources import fmp

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