from typing import Optional

from .. import BasketItem
from ..plugin import FieldPlugin


class Alive(FieldPlugin):
    """ Add 'Alive' field indicating if symbol is still actively traded """

    def __init__(self, alias: Optional[str] = None):
        self._register_call_args(alias=alias)
        if alias is None:
            alias = 'Alive'
        super().__init__(alias=alias)

    def field_type(self) -> type:
        return bool

    def field_value(self, item: BasketItem):
        symbol = item.symbol()
        
        # Check if we have recent price data (within last 30 days)
        try:
            weekly_data = symbol.get_weekly()
            if weekly_data is not None and not weekly_data.empty:
                from datetime import datetime, timedelta
                last_date = weekly_data['date'].max()
                cutoff_date = datetime.now() - timedelta(days=30)
                return bool(last_date >= cutoff_date)  # Convert numpy bool to Python bool
        except:
            pass
            
        # Fallback: assume alive if no data issues
        return True 