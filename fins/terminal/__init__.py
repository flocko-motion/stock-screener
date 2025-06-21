from fins.entities import BasketItem
from fins.entities.basket import Basket

__all__ = [
    'Basket',
    "AAPL",
    "MSFT",
    "GOOG",
    "NFLX",
]

AAPL = BasketItem('AAPL')
MSFT = BasketItem('MSFT')
GOOG = BasketItem('GOOG')
NFLX = BasketItem('NFLX')


"""
def inject_all_symbols():
    for ticker in load_all_tickers():
        if ticker not in globals():
            globals()[ticker] = BasketItem(ticker)
            __all__.append(ticker)
"""