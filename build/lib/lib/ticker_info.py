class TickerInfo:
    def __init__(self,
                    ticker: str,
                    name: str,
                    exchange: str = None,
                    currency: str = None,
                    industry: str = None,
                    sector: str = None,
                    country: str = None,
                    market_cap: float = None,
                    beta: float = None,
                 ):
        self.ticker = ticker
        self.name = name
        self.exchange = exchange
        self.currency = currency
        self.industry = industry
        self.sector = sector
        self.country = country
        self.market_cap = market_cap
        self.beta = beta

    def __repr__(self):
        return (
            f"TickerInfo(name={self.name}:{self.exchange}, market_cap={self.market_cap}, "
        )

