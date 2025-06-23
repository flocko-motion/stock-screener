"""
Plugin Entity

Base class for all plugin types in FINS.
"""

from abc import ABC, abstractmethod
from typing import Optional

from fins.entities import BasketItem


class Plugin(ABC):
    """Base class for all plugins."""

    def __init__(self, alias: Optional[str] = None):
        self.alias = alias


    @abstractmethod
    def value(self, item: BasketItem) -> Optional[float] | str:
        pass

    @abstractmethod
    def run(self, basket):
        pass

