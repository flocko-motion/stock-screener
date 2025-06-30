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
        formatted_args = [self._format_value(arg) for arg in self._call_args]
        
        # Format keyword arguments
        formatted_kwargs = [f"{key}={self._format_value(value)}" for key, value in self._call_kwargs.items()]
        
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

    def _format_value(self, value) -> str:
        """Format a value for inclusion in Python code."""
        if value is None:
            return "None"
        elif isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, bool):
            return str(value)
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, (list, tuple)):
            formatted_items = [self._format_value(item) for item in value]
            if isinstance(value, list):
                return f"[{', '.join(formatted_items)}]"
            else:
                return f"({', '.join(formatted_items)})"
        elif isinstance(value, dict):
            formatted_items = [f"{self._format_value(k)}: {self._format_value(v)}" for k, v in value.items()]
            return f"{{{', '.join(formatted_items)}}}"
        elif hasattr(value, 'isoformat') and hasattr(value, 'date'):  # datetime.date objects
            if hasattr(value, 'time'):  # datetime.datetime
                return f"datetime.datetime.fromisoformat('{value.isoformat()}')"
            else:  # datetime.date
                return f"datetime.date.fromisoformat('{value.isoformat()}')"
        elif hasattr(value, '__class__'):
            # For other objects, try to represent them reasonably
            return f"{value.__class__.__name__}(...)"
        else:
            return repr(value)

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


class FieldPlugin(Plugin):

    def __init__(self, alias: Optional[str] = None):
        super().__init__(alias)
        self._filters = []  # List of (operator, value) tuples

    @abstractmethod
    def field_value(self, item: BasketItem) -> Optional[float] | str | pd.DataFrame:
        pass

    @abstractmethod
    def field_type(self) -> type | dict[str, type]:
        pass

    def run(self, runtime: 'BasketRuntime'):
        from fins.utils import ProgressTracker
        
        # Check if field_type returns a dictionary (for multi-field plugins)
        field_type_result = self.field_type()
        is_multi_field = isinstance(field_type_result, dict)
        
        if is_multi_field:
            # Register multiple fields with suffixes
            field_names = []
            for suffix, field_type in field_type_result.items():
                field_name = f"{self.alias}[{suffix}]"
                runtime.register_field(field_name, field_type)
                field_names.append(field_name)
        else:
            # Single field registration
            runtime.register_field(self.alias, field_type_result)
            field_names = [self.alias]
        
        basket_items = runtime.basket_items()
        if len(basket_items) > 10:  # Only show progress for larger datasets
            tracker = ProgressTracker(len(basket_items), f"Computing {self.alias}")
            for idx, basket_item in enumerate(basket_items):
                try:
                    field_value = self.field_value(basket_item)
                    if is_multi_field:
                        self._set_multi_field_values(runtime, idx, field_names, field_value, field_type_result)
                    else:
                        runtime.set_field_value(idx, self.alias, field_value)
                except Exception as e:
                    raise Exception(f"Failed to compute {self.alias} for {basket_item.ticker}: {e}") from e
                finally:
                    tracker.next()
            tracker.done()
        else:
            # For small datasets, don't show progress
            for idx, basket_item in enumerate(basket_items):
                try:
                    field_value = self.field_value(basket_item)
                    if is_multi_field:
                        self._set_multi_field_values(runtime, idx, field_names, field_value, field_type_result)
                    else:
                        runtime.set_field_value(idx, self.alias, field_value)
                except Exception as e:
                    raise Exception(f"Failed to compute {self.alias} for {basket_item.ticker}: {e}") from e

        # Then apply any filters
        if self._filters:
            if is_multi_field:
                self._apply_multi_field_filters(runtime, field_names, field_type_result)
            else:
                self._apply_filters(runtime)
    
    def _set_multi_field_values(self, runtime: 'BasketRuntime', idx: int, field_names: list, field_value, field_type_dict: dict):
        """Set values for multi-field plugins that return tuples or dicts"""
        if field_value is None:
            # Set all fields to None
            for field_name in field_names:
                runtime.set_field_value(idx, field_name, None)
        elif isinstance(field_value, tuple):
            # Decompose tuple into individual field values
            suffixes = list(field_type_dict.keys())
            if len(field_value) != len(suffixes):
                raise ValueError(f"Tuple length {len(field_value)} doesn't match field count {len(suffixes)}")
            for field_name, value in zip(field_names, field_value):
                runtime.set_field_value(idx, field_name, value)
        elif isinstance(field_value, dict):
            # Use dict keys to map to field names
            suffixes = list(field_type_dict.keys())
            for suffix, field_name in zip(suffixes, field_names):
                value = field_value.get(suffix)
                runtime.set_field_value(idx, field_name, value)
        else:
            raise ValueError(f"Multi-field plugin returned unexpected type: {type(field_value)}")
    
    def _apply_filters(self, runtime: 'BasketRuntime'):
        """Apply all filters to the runtime"""
        df = runtime.df()
        field_name = self.alias
        
        if field_name not in df.columns:
            raise RuntimeError(f"Field {field_name} not found in runtime data")
        
        # Determine which items to keep based on all filters
        keep_indices = []
        filtered_items = []
        
        for idx, (basket_item, field_value) in enumerate(zip(runtime.basket_items(), df[field_name])):
            if self._passes_all_filters(field_value):
                keep_indices.append(idx)
                filtered_items.append(basket_item)
        
        self._update_runtime_with_filtered_items(runtime, keep_indices, filtered_items)
    
    def _apply_multi_field_filters(self, runtime: 'BasketRuntime', field_names: list, field_type_dict: dict):
        """Apply all filters to multi-field plugins"""
        df = runtime.df()
        
        # Check that all specified subfields exist
        for operator, threshold, subfield in self._filters:
            if subfield is None:
                raise RuntimeError(f"Multi-field plugin {self.alias} requires subfield specification for filters")
            expected_field_name = f"{self.alias}[{subfield}]"
            if expected_field_name not in df.columns:
                available_subfields = list(field_type_dict.keys())
                raise RuntimeError(f"Subfield '{subfield}' not found. Available subfields: {available_subfields}")
        
        # Determine which items to keep based on all filters
        keep_indices = []
        filtered_items = []
        
        for idx, basket_item in enumerate(runtime.basket_items()):
            if self._passes_all_multi_field_filters(df, idx, field_type_dict):
                keep_indices.append(idx)
                filtered_items.append(basket_item)
        
        self._update_runtime_with_filtered_items(runtime, keep_indices, filtered_items)
    
    def _update_runtime_with_filtered_items(self, runtime: 'BasketRuntime', keep_indices: list, filtered_items: list):
        """Update runtime with filtered items"""
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
    
    def _passes_all_filters(self, field_value: Any) -> bool:
        """Check if field value passes all filters"""
        for filter_tuple in self._filters:
            if len(filter_tuple) == 2:
                operator, threshold = filter_tuple
            else:
                operator, threshold, _ = filter_tuple  # Ignore subfield for single-field plugins
            if not self._compare_value(field_value, operator, threshold):
                return False
        return True
    
    def _passes_all_multi_field_filters(self, df: pd.DataFrame, row_idx: int, field_type_dict: dict) -> bool:
        """Check if multi-field values pass all filters"""
        for operator, threshold, subfield in self._filters:
            field_name = f"{self.alias}[{subfield}]"
            field_value = df.iloc[row_idx][field_name]
            if not self._compare_value(field_value, operator, threshold):
                return False
        return True
    
    def _compare_value(self, field_value: Any, operator: str, threshold: Any) -> bool:
        """Compare field value with threshold using the specified operator"""
        # Handle None values
        if operator == 'is_none':
            return field_value is None
        elif operator == 'is_not_none':
            return field_value is not None
        elif field_value is None:
            return False
            
        try:
            if operator == '>':
                return field_value > threshold
            elif operator == '>=':
                return field_value >= threshold
            elif operator == '<':
                return field_value < threshold
            elif operator == '<=':
                return field_value <= threshold
            elif operator == '==':
                return field_value == threshold
            elif operator == '!=':
                return field_value != threshold
            elif operator == 'contains':
                return str(threshold) in str(field_value)
            elif operator == 'in':
                return field_value in threshold
            else:
                raise ValueError(f"Unsupported operator: {operator}")
        except (TypeError, ValueError):
            return False

    # Mathematical filtering methods that return self for chaining
    def min(self, value: Union[float, int, str, datetime], *, subfield: str = None) -> 'FieldPlugin':
        """Filter for values >= threshold: plugin.min(value) or plugin.min(value, subfield="fieldname")"""
        self._filters.append(('>=', _parse_filter_value(value), subfield))
        return self
    
    def max(self, value: Union[float, int, str, datetime], *, subfield: str = None) -> 'FieldPlugin':
        """Filter for values <= threshold: plugin.max(value) or plugin.max(value, subfield="fieldname")"""
        self._filters.append(('<=', _parse_filter_value(value), subfield))
        return self
    
    def equals(self, value: Union[float, int, str, datetime], *, subfield: str = None) -> 'FieldPlugin':
        """Filter for exact equality: plugin.equals(value) or plugin.equals(value, subfield="fieldname")"""
        self._filters.append(('==', _parse_filter_value(value), subfield))
        return self
    
    def exclude(self, value: Union[float, int, str, list, tuple, set], *, subfield: str = None) -> 'FieldPlugin':
        """Filter for inequality: plugin.exclude(value) or plugin.exclude(value, subfield="fieldname")"""
        if isinstance(value, (list, tuple, set)):
            # Add multiple != filters for each value in the collection
            for item in value:
                self._filters.append(('!=', item, subfield))
        else:
            # Single value exclusion
            self._filters.append(('!=', _parse_filter_value(value), subfield))
        return self
    
    def true(self, *, subfield: str = None) -> 'FieldPlugin':
        """Filter for boolean fields that are True: plugin.true() or plugin.true(subfield="fieldname")"""
        self._filters.append(('==', True, subfield))
        return self
    
    def false(self, *, subfield: str = None) -> 'FieldPlugin':
        """Filter for boolean fields that are False: plugin.false() or plugin.false(subfield="fieldname")"""
        self._filters.append(('==', False, subfield))
        return self
    
    def contains(self, value: Union[float, int, str], *, subfield: str = None) -> 'FieldPlugin':
        """Filter for substring: plugin.contains(value) or plugin.contains(value, subfield="fieldname")"""
        self._filters.append(('contains', _parse_filter_value(value), subfield))
        return self
    
    def any(self, collection: Union[list, tuple, set], *, subfield: str = None) -> 'FieldPlugin':
        """Filter for membership: plugin.any(collection) or plugin.any(collection, subfield="fieldname")"""
        self._filters.append(('in', collection, subfield))
        return self
    
    def within(self, from_value: Union[float, int], to_value: Union[float, int], *, subfield: str = None) -> 'FieldPlugin':
        """Filter for values within range: plugin.within(from_value, to_value) or plugin.within(from_value, to_value, subfield="fieldname")"""
        self._filters.append(('>=', _parse_filter_value(from_value), subfield))
        self._filters.append(('<=', _parse_filter_value(to_value), subfield))
        return self
    
    def around(self, value: Union[float, int], precision: float = 0.1, *, subfield: str = None) -> 'FieldPlugin':
        """Filter for values within percentage range: plugin.around(value, precision=0.1) or plugin.around(value, precision=0.1, subfield="fieldname")"""
        # precision of 0.1 means +/- 10%
        lower_bound = _parse_filter_value(value) / (1 + precision)
        upper_bound = _parse_filter_value(value) * (1 + precision)
        self._filters.append(('>=', lower_bound, subfield))
        self._filters.append(('<=', upper_bound, subfield))
        return self
    
    def none(self, *, subfield: str = None) -> 'FieldPlugin':
        """Filter for None/null values: plugin.none() or plugin.none(subfield="fieldname")"""
        self._filters.append(('is_none', None, subfield))
        return self
    
    def not_none(self, *, subfield: str = None) -> 'FieldPlugin':
        """Filter for non-None values: plugin.not_none() or plugin.not_none(subfield="fieldname")"""
        self._filters.append(('is_not_none', None, subfield))
        return self

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
            print(f"Plugin: {plugin}")
            plugin.run(runtime)
        print(f"Finished pipeline - final basket has {len(runtime.basket())} items")
        return runtime




class BasketRuntime:

    def __init__(self, basket: Basket):
        self._basket = basket
        self._df = basket.df().copy()  # Start with basket's DataFrame
        self._fields = dict[str, type]()
        self._output_data = OutputData()

    def __call__(self, arg):
        self._basket.__call__(arg)

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





