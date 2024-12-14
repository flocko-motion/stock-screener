class TickerInfo:
    def __init__(self, ticker: str, name: str, market_cap: float = None, trailing_pe: float = None, forward_pe: float = None):
        self.ticker = ticker
        self.name = name
        self.market_cap = market_cap
        self.trailing_pe = trailing_pe
        self.forward_pe = forward_pe

    def __repr__(self):
        return (
            f"TickerInfo(name={self.name}, market_cap={self.market_cap}, "
            f"trailing_pe={self.trailing_pe}, forward_pe={self.forward_pe})"
        )

