"""
Plugin Entity

Base class for all plugin types in FINS.
"""

from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import Optional, List, Union, Any
import pandas as pd

from fins.entities import BasketItem, Basket

from fins.financial import Symbol
from fins.utils import format_value


class Plugin(ABC):

    def __init__(self, alias: Optional[str] = None):
        self.alias = alias if alias is not None else self.__class__.__name__

    @abstractmethod
    def run(self, runtime: 'BasketRuntime'):
        pass

    def __str__(self) -> str:
        """Return Python code to recreate this plugin with its current configuration."""
        if not hasattr(self, '_call_args') or not hasattr(self, '_call_kwargs'):
            raise RuntimeError(f"Plugin {self.__class__.__name__} must call self._register_call_args() in __init__")
        
        class_name = self.__class__.__name__
        
        # Format positional arguments
        formatted_args = [format_value(arg) for arg in self._call_args]
        
        # Format keyword arguments
        formatted_kwargs = [f"{key}={format_value(value)}" for key, value in self._call_kwargs.items()]
        
        # Combine all arguments
        all_args = formatted_args + formatted_kwargs
        
        if not all_args:
            return f"{class_name}()"
        
        args_str = ", ".join(all_args)
        return f"{class_name}({args_str})"

    def _register_call_args(self, *args, **kwargs):
        """
        Register the constructor arguments for this plugin instance.
        
        Plugins should call this method in their __init__ to enable accurate __str__ representation.
        
        Args:
            *args: Positional arguments passed to constructor
            **kwargs: Keyword arguments passed to constructor
        """
        self._call_args = args
        self._call_kwargs = kwargs

    def __rshift__(self, other: 'Plugin') -> 'BasketPipeline':
        """Chain plugins using >> operator"""
        if isinstance(other, Plugin):
            return BasketPipeline(self, other)
        elif isinstance(other, BasketPipeline):
            return BasketPipeline(self, *other._plugins)
        else:
            return NotImplemented


def _parse_filter_value(value):
    if isinstance(value, str):
        try:
            d = datetime.fromisoformat(value)
            return d
        except ValueError:
            pass
    if isinstance(value, date) and not isinstance(value, datetime):
        # Convert date to datetime (midnight of that date)
        return datetime.combine(value, datetime.min.time())
    return value


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
            print(f"Plugin: {plugin}")
            plugin.run(runtime)
        print(f"Finished pipeline - final basket has {len(runtime.basket())} items")
        return runtime




class BasketRuntime:

    def __init__(self, basket: Basket):
        from fins.entities.plugin_output import OutputData
        self._basket = basket
        self._df = basket.df().copy()  # Start with basket's DataFrame
        self._fields = dict[str, type]()
        self._output_data = OutputData()

    def __call__(self, arg):
        self._basket.__call__(arg)

    def __len__(self):
        return self._basket.__len__()

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
        valid_types = [float, str, bool, type(None), datetime, Optional[datetime], Optional[float], Optional[str], pd.DataFrame, Optional[pd.DataFrame]]
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
        elif field_type == Optional[str]:
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
        elif expected_type == Optional[str]:
            if value is not None and not isinstance(value, str):
                raise RuntimeError(f"Invalid value of type {type(value)} (expected: Optional[str]) for field {field_name}")
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

    def remove_items(self, indices_to_remove: List[int]):
        """
        Remove items from the runtime by their indices.
        
        Args:
            indices_to_remove: List of row indices to remove (sorted in descending order)
        """
        if not indices_to_remove:
            return
            
        # Remove from DataFrame (must be done in reverse order to maintain indices)
        indices_to_remove.sort(reverse=True)
        for idx in indices_to_remove:
            self._df = self._df.drop(self._df.index[idx]).reset_index(drop=True)
        
        # Remove from output data
        if hasattr(self, '_output_data') and self._output_data is not None:
            old_items = self._output_data._items
            new_items = {}
            
            # Remap remaining items with new indices
            remaining_indices = [i for i in range(len(self._basket.items())) if i not in set(indices_to_remove)]
            for new_idx, old_idx in enumerate(remaining_indices):
                if old_idx in old_items:
                    new_items[new_idx] = old_items[old_idx]
            
            self._output_data._items = new_items
        
        # Create new basket with remaining items
        remaining_items = [item for i, item in enumerate(self._basket.items()) if i not in set(indices_to_remove)]
        from fins.entities import Basket  # Import here to avoid circular import
        self._basket = Basket(items=remaining_items, name=self._basket._name)





