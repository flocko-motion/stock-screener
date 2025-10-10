"""
FINS Entities

This package contains the core domain entities used throughout the FINS system, which can be managed and manipulated by the DSL commands.
"""

from .basket_item import BasketItem
from .basket import Basket
from .plugin import Plugin, BasketPipeline, BasketRuntime
from .entity import Entity, JsonSerializable
from .note import Note, Principle, Observation, Trade, Fact, Strategy
from fins.financial import Symbol


class SymbolAccessor:
    """
    Get any symbol as basket item

    Usage:
        S.AAPL  - Returns a BasketItem for Apple Inc.
        S.MSFT  - Returns a BasketItem for Microsoft Corp.

    The ticker symbol is automatically converted to uppercase.
    """

    def __getattr__(self, name: str):
        name = str(name).upper()
        return BasketItem(Symbol.get(name))


# Global instance for convenient access
S = SymbolAccessor()

__all__ = [
    'JsonSerializable',
    'BasketItem',
    'Basket',
    'Plugin',
    'BasketPipeline',
    'BasketRuntime',
    'Entity',
    'Note',
    'Principle',
    'Observation',
    'Trade',
    'Fact',
    'Strategy',
    'S',
]


def entity_from_dict(data: dict) -> 'Entity':
    data_copy = data.copy()
    class_name = data_copy.pop("class", None)

    if not class_name:
        raise ValueError("Class name not provided in data dictionary")

    if class_name in globals():
        cls = globals()[str(class_name)]
        # Pass the data without the "class" key
        return cls.from_dict(data_copy)

    raise ValueError(f"Class {class_name} not found")
