class NoPriceDataError(ValueError):
    """Raised when no price data is found for the given symbol/date range."""
    pass

class SymbolNotFound(ValueError):
    """Raised when a symbol cannot be found for the given date range."""
    pass