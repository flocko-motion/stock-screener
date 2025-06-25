from datetime import datetime
from typing import Optional

from .. import BasketItem
from ..plugin import FieldPlugin


class LastUpdateProfile(FieldPlugin):
    """ Add 'LastProfileUpdate' field """

    def __init__(self, alias: Optional[str] = None):
        super().__init__(alias=alias)

    def field_type(self) -> type:
        return Optional[datetime]

    def field_value(self, item: BasketItem):
        return item.symbol().last_profile_update


