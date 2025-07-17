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
        from fins.utils import ProgressTracker
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from fins.shutdown import is_shutdown_requested
        
        basket_items = runtime.basket_items()
        
        # Count how many items actually need updates
        print(f"Checking {len(basket_items)} symbols for update requirement")
        items_needing_update = [item for item in basket_items if self._update_required(item.symbol())]
        actual_update_count = min(len(items_needing_update), self.max_updates)
        print(f"{len(items_needing_update)} symbols need updating, updating {actual_update_count} of them according to max_updates")
        
        if actual_update_count == 0:
            print("No symbols need updating")
            return
        
        tracker = ProgressTracker(actual_update_count, f"Updating symbols (max {self.max_updates})")
        
        def update_symbol_for_item(item: BasketItem):
            if is_shutdown_requested():
                return item
            try:
                symbol = item.symbol()
                if self._update_required(symbol):
                    symbol.update()
                    tracker.next()
                return item
            except Exception as e:
                print(f"Error updating {item.ticker}: {e}")
                tracker.next()  # Still count it as processed
                return item
        
        # Take only the items that need updates, limited by max_updates
        items_to_update = items_needing_update[:self.max_updates]
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(update_symbol_for_item, item): item for item in items_to_update}
            for future in as_completed(futures):
                if is_shutdown_requested():
                    break
                future.result()  # This will raise any exceptions that occurred
        
        tracker.done()

    def _update_required(self, symbol: Symbol):
        last_update = symbol.last_update()
        return last_update is None or last_update < self.older_than



    def __init__(self, alias: Optional[str] = None, older_than: str | datetime.datetime | datetime.date | None = None, max: int = 100) -> None:
        self._register_call_args(alias=alias, older_than=older_than, max=max)
        super().__init__(alias=alias)
        if isinstance(older_than, str):
            older_than = datetime.datetime.fromisoformat(older_than)
        self.older_than = older_than if older_than else beginning_of_current_month()

        self.max_updates = max




