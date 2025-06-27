"""
Plugin Entity

Base class for all plugin types in FINS.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List
import pandas as pd

from fins.entities import BasketItem, Basket
from fins.financial import Symbol


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

class OutputPlugin(Plugin):

    def __init__(self, alias: Optional[str] = None):
        super().__init__(alias)

    def output_item(self, symbol: Symbol, data: dict[str, pd.DataFrame]):
        pass

    def output_all(self, data: 'OutputData'):
        pass

    def run(self, runtime: 'BasketRuntime'):
        output_data = runtime.output_data()
        self.output_all(output_data)
        items = output_data.items()
        for idx, basket_item in enumerate(runtime.basket_items()):
            self.output_item(basket_item.symbol(), items[idx])

class OutputData:

    def __init__(self):
        self._series = list[str]()
        self._items = dict[int, dict[str, pd.DataFrame]]()

    def register_series(self, field_name: str):
        self._series.append(field_name)

    def items(self) -> dict[int, dict[str, pd.DataFrame]]:
        return self._items

    def set_series(self, row_index: int, field_name: str, value: pd.DataFrame):
        if not row_index in self._series:
            self._items[row_index] = dict[str, pd.DataFrame]()
        self._items[row_index][field_name] = value


class FilterPlugin(Plugin):

    def __init__(self, alias: Optional[str] = None):
        super().__init__(alias)

    @abstractmethod
    def should_keep(self, item: BasketItem) -> bool:
        """Return True if the item should be kept in the basket"""
        pass

    def run(self, runtime: 'BasketRuntime'):
        # Determine which items to keep
        keep_indices = []
        filtered_items = []
        
        for idx, item in enumerate(runtime.basket_items()):
            if self.should_keep(item):
                keep_indices.append(idx)
                filtered_items.append(item)
        
        # Create new basket with filtered items
        filtered_basket = Basket(items=filtered_items, name=runtime.basket()._name)
        
        # Filter the accumulated DataFrame to keep only the corresponding rows
        runtime._df = runtime._df.iloc[keep_indices].reset_index(drop=True)
        
        # Filter and reindex the output data (time series with date indices)
        old_items = runtime._output_data._items
        new_items = {}
        for new_idx, old_idx in enumerate(keep_indices):
            if old_idx in old_items:
                new_items[new_idx] = old_items[old_idx]
        runtime._output_data._items = new_items
        
        # Update the basket reference
        runtime._basket = filtered_basket


class FieldPlugin(Plugin):

    def __init__(self, alias: Optional[str] = None):
        super().__init__(alias)

    @abstractmethod
    def field_value(self, item: BasketItem) -> Optional[float] | str | pd.DataFrame:
        pass

    @abstractmethod
    def field_type(self) -> type:
        pass

    def run(self, runtime: 'BasketRuntime'):
        runtime.register_field(self.alias, self.field_type())
        for idx, basket_item in enumerate(runtime.basket_items()):
            field_value = self.field_value(basket_item)
            runtime.set_field_value(idx, self.alias, field_value)

class SeriesPlugin(FieldPlugin):

    def __init__(self, alias: Optional[str] = None):
        super().__init__(alias)

    @abstractmethod
    def field_value(self, item: BasketItem) -> pd.DataFrame:
        pass

    def field_type(self) -> type:
        return pd.DataFrame


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
        self._output_data = OutputData()

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
        valid_types = [float, str, bool, type(None), datetime, Optional[datetime], Optional[float], pd.DataFrame, Optional[pd.DataFrame]]
        if field_type not in valid_types:
            raise RuntimeError(f"Field {field_name} has invalid type {field_type}")
        
        self._fields[field_name] = field_type
        
        # Add field to DataFrame with appropriate default value
        if field_type == str:
            self._df[field_name] = ""
        elif field_type == bool:
            self._df[field_name] = False
        elif field_type == float or field_type == Optional[float]:
            self._df[field_name] = None
        elif field_type == datetime or field_type == Optional[datetime]:
            self._df[field_name] = None
        elif field_type == pd.DataFrame or field_type == Optional[pd.DataFrame]:
            self._output_data.register_series(field_name)
        else:
            self._df[field_name] = None

    def set_field_value(self, row_index: int, field_name: str, value):
        """Set a field value directly in the DataFrame"""
        if field_name not in self._fields:
            raise RuntimeError(f"Field {field_name} is not registered")
        
        self.validate_field_value(field_name, value)

        if self._fields[field_name] == pd.DataFrame:
            self._output_data.set_series(row_index, field_name, value)
        else:
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
        elif expected_type == Optional[datetime]:
            if value is not None and not isinstance(value, datetime):
                raise RuntimeError(f"Invalid value of type {type(value)} (expected: Optional[datetime]) for field {field_name}")
        elif expected_type == datetime:
            if not isinstance(value, datetime):
                raise RuntimeError(f"Invalid value of type {type(value)} (expected: datetime) for field {field_name}")
        elif expected_type == str:
            if not isinstance(value, str):
                raise RuntimeError(f"Invalid value of type {type(value)} (expected: str) for field {field_name}")
        elif expected_type == bool:
            if not isinstance(value, bool):
                raise RuntimeError(f"Invalid value of type {type(value)} (expected: bool) for field {field_name}")
        elif expected_type == pd.DataFrame:
            if not isinstance(value, pd.DataFrame):
                raise RuntimeError(f"Invalid value of type {type(value)} (expected: pd.DataFrame) for field {field_name}")
        elif expected_type == Optional[pd.DataFrame]:
            if value is not None and not isinstance(value, pd.DataFrame):
                raise RuntimeError(f"Invalid value of type {type(value)} (expected: Optional[pd.DataFrame]) for field {field_name}")

    def df(self) -> pd.DataFrame:
        """Return the enriched DataFrame with all plugin outputs"""
        return self._df.copy()

    def basket(self) -> Basket:
        """Return the original basket"""
        return self._basket

    def output_data(self):
        return self._output_data





