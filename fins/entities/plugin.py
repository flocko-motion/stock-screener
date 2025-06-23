"""
Plugin Entity

Base class for all plugin types in FINS.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
import pandas as pd

from fins.entities import BasketItem, Basket


class Plugin(ABC):

    def __init__(self, alias: Optional[str] = None):
        self.alias = alias if alias is not None else self.__class__.__name__

    @abstractmethod
    def run(self, runtime: 'BasketRuntime'):
        pass

    def __rshift__(self, other: 'Plugin') -> 'BasketPipeline':
        """Chain plugins using >> operator"""
        if isinstance(other, Plugin):
            return BasketPipeline(self, other)
        elif isinstance(other, BasketPipeline):
            return BasketPipeline(self, *other._plugins)
        else:
            return NotImplemented


class FieldPlugin(Plugin):

    def __init__(self, alias: Optional[str] = None):
        super().__init__(alias)

    @abstractmethod
    def field_value(self, item: BasketItem) -> Optional[float] | str:
        pass

    @abstractmethod
    def field_type(self) -> type:
        pass

    def run(self, runtime: 'BasketRuntime'):
        runtime.register_field(self.alias, self.field_type())
        for idx, basket_item in enumerate(runtime.basket_items()):
            field_value = self.field_value(basket_item)
            runtime.set_field_value(idx, self.alias, field_value)


class BasketPipeline:
    """A pipeline of several chained plugins"""

    def __init__(self, *plugins: Plugin):
        self._plugins: List[Plugin] = list(plugins)
        aliases = set()
        for plugin in self._plugins:
            if plugin.alias in aliases:
                raise RuntimeError(f"Plugin {plugin.alias} already exists in pipe - please provide a different alias")
            aliases.add(plugin.alias)

    def __rshift__(self, other: 'Plugin') -> 'BasketPipeline':
        """Chain additional plugins using >> operator"""
        if isinstance(other, Plugin):
            return BasketPipeline(*self._plugins, other)
        elif isinstance(other, BasketPipeline):
            return BasketPipeline(*self._plugins, *other._plugins)
        else:
            return NotImplemented

    def run(self, basket: Basket) -> 'BasketRuntime':
        runtime = BasketRuntime(basket)
        for plugin in self._plugins:
            plugin.run(runtime)
        return runtime


class BasketRuntime:

    def __init__(self, basket: Basket):
        self._basket = basket
        self._df = basket.df().copy()  # Start with basket's DataFrame
        self._fields = dict[str, type]()

    def __repr__(self) -> str:
        return repr(self.df())

    def basket_items(self) -> List[BasketItem]:
        """Return the original basket items for plugin processing"""
        return self._basket.items()

    def register_field(self, field_name: str, field_type: type):
        """Register a new field and add it as a column to the DataFrame"""
        if field_name in self._fields:
            raise RuntimeError(f"Field {field_name} is already registered")
        
        # Validate field type
        valid_types = [float, str, type(None)]
        if field_type not in valid_types and field_type != Optional[float]:
            raise RuntimeError(f"Field {field_name} has invalid type {field_type}")
        
        self._fields[field_name] = field_type
        
        # Add column to DataFrame with appropriate default value
        if field_type == str:
            self._df[field_name] = ""
        elif field_type == float or field_type == Optional[float]:
            self._df[field_name] = None
        else:
            self._df[field_name] = None

    def set_field_value(self, row_index: int, field_name: str, value):
        """Set a field value directly in the DataFrame"""
        if field_name not in self._fields:
            raise RuntimeError(f"Field {field_name} is not registered")
        
        self.validate_field_value(field_name, value)
        self._df.iloc[row_index, self._df.columns.get_loc(field_name)] = value

    def validate_field_value(self, field_name: str, value):
        """Validate that the value matches the registered field type"""
        expected_type = self._fields[field_name]
        
        # Handle Optional[float] case
        if expected_type == Optional[float]:
            if value is not None and not isinstance(value, (int, float)):
                raise RuntimeError(f"Invalid value of type {type(value)} (expected: Optional[float]) for field {field_name}")
        elif expected_type == float:
            if not isinstance(value, (int, float)):
                raise RuntimeError(f"Invalid value of type {type(value)} (expected: float) for field {field_name}")
        elif expected_type == str:
            if not isinstance(value, str):
                raise RuntimeError(f"Invalid value of type {type(value)} (expected: str) for field {field_name}")

    def df(self) -> pd.DataFrame:
        """Return the enriched DataFrame with all plugin outputs"""
        return self._df.copy()

    def basket(self) -> Basket:
        """Return the original basket"""
        return self._basket




