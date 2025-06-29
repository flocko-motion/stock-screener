from typing import Optional
from datetime import datetime

from .. import BasketItem
from ..plugin import FieldPlugin


class Age(FieldPlugin):
    """ Add 'Age' field showing company age in years since inception """

    def __init__(self, alias: Optional[str] = None):
        self._register_call_args(alias=alias)
        if alias is None:
            alias = 'Age'
        super().__init__(alias=alias)

    def field_type(self) -> type:
        return Optional[float]

    def field_value(self, item: BasketItem):
        """Return age in years since inception, or None if inception unknown"""
        symbol = item.symbol()
        
        # Return None for symbols with unknown inception
        if symbol.inception is None:
            return None
            
        # Calculate age in years
        time_diff = datetime.now() - symbol.inception
        age_years = time_diff.days / 365.25  # Account for leap years
        
        return age_years 