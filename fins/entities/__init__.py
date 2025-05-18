"""
FINS Entities

This package contains the core domain entities used throughout the FINS system, which can be managed and manipulated by the DSL commands.
"""

from .basket_item import BasketItem
from .basket import Basket
from .column import Column
from .entity import Entity, JsonSerializable
from .note import Note, Principle, Observation, Trade, Fact, Strategy
from .token import Token

__all__ = [
    'JsonSerializable',
    'BasketItem',
    'Basket',
    'Column',
    'Entity',
    'Note',
    'Principle',
    'Observation',
    'Trade',
    'Fact',
    'Strategy',
    'Token',
]

def entity_from_dict(data: dict) -> 'Entity':
    data_copy = data.copy()
    class_name = data_copy.pop("class", None)
    
    if not class_name:
        raise ValueError("Class name not provided in data dictionary")

    if class_name in globals():
        cls = globals()[class_name]
        return cls.from_dict(data_copy)  # Pass the data without the "class" key
    
    raise ValueError(f"Class {class_name} not found")