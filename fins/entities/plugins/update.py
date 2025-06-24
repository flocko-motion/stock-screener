import datetime
from typing import Optional

from .. import BasketItem, BasketRuntime
from ..plugin import Plugin
from ...financial import Symbol


def beginning_of_current_month() -> datetime.datetime:
    """Get the beginning of current month at 12:00."""
    now = datetime.datetime.now()
    return datetime.datetime(now.year, now.month, 1, 12, 0, 0)


class Update(Plugin):
    """ Fetch latest data for Symbols in Basket
    """

    def run(self, runtime: 'BasketRuntime'):
        updates_count = 0
        for item in runtime.basket_items():
            symbol = item.symbol()
            if self._update_required(symbol):
                symbol.update()
                updates_count += 1
                if updates_count > self.max_updates:
                    print('Max updates reached')
                    break

    def _update_required(self, symbol: Symbol):
        return (symbol.last_price_update is None or symbol.last_price_update < self.older_than
                or symbol.last_profile_update is None or symbol.last_profile_update < self.older_than)


    def __init__(self, alias: Optional[str] = None, older_than: datetime.datetime | None = None, max_updates: int = 100) -> None:
        super().__init__(alias=alias)
        self.older_than = older_than if older_than else beginning_of_current_month()
        self.max_updates = max_updates




