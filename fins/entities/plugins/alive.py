"""
Alive (Has Recent Data) Column
"""

from typing import Optional
from datetime import datetime, timedelta

from .. import BasketItem
from ..plugin_field import FieldPlugin


class Alive(FieldPlugin):
    """
    Add 'Alive' field indicating if symbol is still actively traded

    Useful to filter out inactive stocks with Alive().true()
    
    """

    def __init__(self, alias: Optional[str] = None):
        self._register_call_args(alias=alias)
        if alias is None:
            alias = 'Alive'
        super().__init__(alias=alias)

    def field_types(self):
        return [("", bool)]

    def field_values(self, item: BasketItem):
        # Check if we have recent price data (within last 30 days)
        weekly_data = item.symbol().get_weekly()
        if weekly_data.empty:
            return [False]
        last_date = weekly_data['date'].max()
        cutoff_date = datetime.now() - timedelta(days=30)
        return [bool(last_date >= cutoff_date)]  # Convert numpy bool to Python bool