from abc import abstractmethod, ABC
from datetime import datetime
from typing import Union, Any, Optional, List, Tuple

from fins.entities import BasketItem, Plugin
from fins.entities.plugin import _parse_filter_value
from fins.utils import format_value
from fins.entities.media import Media, media_cache


class FilterOut:
	"""Sentinel value indicating that an item should be filtered out"""
	pass


FILTER_OUT = FilterOut()


class FieldOperator(ABC):
	"""
	A field operator that can transform values and/or filter items.

	Operators are applied in sequence and can:
	- Transform the value (return modified value)
	- Filter out the item (return FILTER_OUT)
	- Both transform and filter in one step
	"""

	def __init__(self, subfield: str = None):
		"""
		Args:
			subfield: Optional subfield name for multi-field plugins
		"""
		self.subfield = subfield

	def _register_call_args(self, method_name: str, *args, **kwargs):
		"""
		Register the method call arguments for string representation.
		
		Args:
			method_name: Name of the method (e.g., 'min', 'max', 'exclude')
			*args: Positional arguments passed to method
			**kwargs: Keyword arguments passed to method
		"""
		self._method_name = method_name
		self._call_args = args
		self._call_kwargs = kwargs

	def to_method_call(self) -> str:
		"""
		Return the method call representation of this operator.
		
		Returns:
			str: Method call like ".min(5)" or ".max(10, subfield='Med')"
		"""
		if not hasattr(self, '_method_name'):
			raise RuntimeError(f"Operator {self.__class__.__name__} must call self._register_call_args() in __init__")
		
		# Format positional arguments
		formatted_args = [format_value(arg) for arg in self._call_args]
		
		# Format keyword arguments, including subfield if present
		formatted_kwargs = []
		for key, value in self._call_kwargs.items():
			formatted_kwargs.append(f"{key}={format_value(value)}")
		
		# Add subfield if it exists and wasn't already in kwargs
		if self.subfield and 'subfield' not in self._call_kwargs:
			formatted_kwargs.append(f"subfield='{self.subfield}'")
		
		# Combine all arguments
		all_args = formatted_args + formatted_kwargs
		
		if not all_args:
			return f".{self._method_name}()"
		
		args_str = ", ".join(all_args)
		return f".{self._method_name}({args_str})"

	@abstractmethod
	def apply_operation(self, value: Any) -> Any:
		"""
		Apply this operator's logic to a value.

		Returns:
			- Transformed value if operator applies and doesn't filter out
			- FILTER_OUT if operator filters out the item
		"""
		pass

	def apply(self, value: Any, current_subfield: str = None) -> Any:
		"""
		Apply this operator to a value if the subfield matches.

		Returns:
			- Transformed value if operator applies and doesn't filter out
			- FILTER_OUT if operator filters out the item
			- Original value if subfield doesn't match
		"""
		# Only apply if subfield matches (None matches None)
		if self.subfield == current_subfield:
			return self.apply_operation(value)
		else:
			return value

	def __repr__(self) -> str:
		subfield_str = f"subfield='{self.subfield}'" if self.subfield else ""
		return f"{self.__class__.__name__}({subfield_str})"


class FieldOperatorMax(FieldOperator):
	"""Filter operator for values <= threshold"""

	def __init__(self, threshold, subfield: str = None):
		self.threshold = _parse_filter_value(threshold)
		super().__init__(subfield)
		self._register_call_args("max", threshold)

	def apply_operation(self, field_value):
		if field_value is None:
			return FILTER_OUT
		try:
			return field_value if field_value <= self.threshold else FILTER_OUT
		except (TypeError, ValueError):
			return FILTER_OUT

	def __repr__(self) -> str:
		subfield_str = f", subfield='{self.subfield}'" if self.subfield else ""
		return f"FieldOperatorMax({self.threshold}{subfield_str})"


class FieldOperatorMin(FieldOperator):
	"""Filter operator for values >= threshold"""

	def __init__(self, threshold, subfield: str = None):
		self.threshold = _parse_filter_value(threshold)
		super().__init__(subfield)
		self._register_call_args("min", threshold)

	def apply_operation(self, field_value):
		if field_value is None:
			return FILTER_OUT
		try:
			return field_value if field_value >= self.threshold else FILTER_OUT
		except (TypeError, ValueError):
			return FILTER_OUT

	def __repr__(self) -> str:
		subfield_str = f", subfield='{self.subfield}'" if self.subfield else ""
		return f"FieldOperatorMin({self.threshold}{subfield_str})"


class FieldOperatorEquals(FieldOperator):
	"""Filter operator for values == target"""

	def __init__(self, target, subfield: str = None):
		self.target = target
		super().__init__(subfield)
		self._register_call_args("equals", target)

	def apply_operation(self, field_value):
		if field_value is None:
			return FILTER_OUT
		try:
			return field_value if field_value == self.target else FILTER_OUT
		except (TypeError, ValueError):
			return FILTER_OUT

	def __repr__(self) -> str:
		subfield_str = f", subfield='{self.subfield}'" if self.subfield else ""
		return f"FieldOperatorEquals({self.target}{subfield_str})"


class FieldOperatorLog(FieldOperator):
	"""Transformation operator for log10"""

	def __init__(self, subfield: str = None):
		super().__init__(subfield)
		self._register_call_args("log")

	def apply_operation(self, value):
		import math

		if value is None:
			return None

		try:
			if isinstance(value, (int, float)) and value > 0:
				return math.log10(value)
			else:
				# Can't take log of zero or negative numbers
				return None
		except (TypeError, ValueError):
			return None

	def __repr__(self) -> str:
		subfield_str = f", subfield='{self.subfield}'" if self.subfield else ""
		return f"FieldOperatorLog({subfield_str})"


class FieldOperatorExclude(FieldOperator):
	"""Filter operator for values != target(s)"""

	def __init__(self, values, subfield: str = None):
		if isinstance(values, (list, tuple, set)):
			self.values = set(values)
		else:
			self.values = {_parse_filter_value(values)}
		super().__init__(subfield)
		self._register_call_args("exclude", values)

	def apply_operation(self, field_value):
		if field_value is None:
			return FILTER_OUT
		try:
			return field_value if field_value not in self.values else FILTER_OUT
		except (TypeError, ValueError):
			return FILTER_OUT

	def __repr__(self) -> str:
		subfield_str = f", subfield='{self.subfield}'" if self.subfield else ""
		values_str = list(self.values) if len(self.values) > 1 else next(iter(self.values))
		return f"FieldOperatorExclude({values_str}{subfield_str})"


class FieldOperatorTrue(FieldOperator):
	"""Filter operator for True values"""

	def __init__(self, subfield: str = None):
		super().__init__(subfield)
		self._register_call_args("true")

	def apply_operation(self, field_value):
		try:
			return field_value if field_value is True else FILTER_OUT
		except (TypeError, ValueError):
			return FILTER_OUT

	def __repr__(self) -> str:
		subfield_str = f", subfield='{self.subfield}'" if self.subfield else ""
		return f"FieldOperatorTrue({subfield_str})"


class FieldOperatorFalse(FieldOperator):
	"""Filter operator for False values"""

	def __init__(self, subfield: str = None):
		super().__init__(subfield)
		self._register_call_args("false")

	def apply_operation(self, field_value):
		try:
			return field_value if field_value is False else FILTER_OUT
		except (TypeError, ValueError):
			return FILTER_OUT

	def __repr__(self) -> str:
		subfield_str = f", subfield='{self.subfield}'" if self.subfield else ""
		return f"FieldOperatorFalse({subfield_str})"


class FieldOperatorContains(FieldOperator):
	"""Filter operator for substring containment"""

	def __init__(self, substring, subfield: str = None):
		self.substring = _parse_filter_value(substring)
		super().__init__(subfield)
		self._register_call_args("contains", substring)

	def apply_operation(self, field_value):
		if field_value is None:
			return FILTER_OUT
		try:
			if isinstance(field_value, str) and isinstance(self.substring, str):
				return field_value if self.substring in field_value else FILTER_OUT
			else:
				return FILTER_OUT
		except (TypeError, ValueError):
			return FILTER_OUT

	def __repr__(self) -> str:
		subfield_str = f", subfield='{self.subfield}'" if self.subfield else ""
		return f"FieldOperatorContains({self.substring}{subfield_str})"


class FieldOperatorAny(FieldOperator):
	"""Filter operator for membership in collection"""

	def __init__(self, collection, subfield: str = None):
		self.collection = collection
		super().__init__(subfield)
		self._register_call_args("any", collection)

	def apply_operation(self, field_value):
		if field_value is None:
			return FILTER_OUT
		try:
			return field_value if field_value in self.collection else FILTER_OUT
		except (TypeError, ValueError):
			return FILTER_OUT

	def __repr__(self) -> str:
		subfield_str = f", subfield='{self.subfield}'" if self.subfield else ""
		return f"FieldOperatorAny({self.collection}{subfield_str})"


class FieldOperatorWithin(FieldOperator):
	"""Filter operator for values within range [from_value, to_value]"""

	def __init__(self, from_value, to_value, subfield: str = None):
		self.from_value = _parse_filter_value(from_value)
		self.to_value = _parse_filter_value(to_value)
		super().__init__(subfield)
		self._register_call_args("within", from_value, to_value)

	def apply_operation(self, field_value):
		if field_value is None:
			return FILTER_OUT
		try:
			return field_value if self.from_value <= field_value <= self.to_value else FILTER_OUT
		except (TypeError, ValueError):
			return FILTER_OUT

	def __repr__(self) -> str:
		subfield_str = f", subfield='{self.subfield}'" if self.subfield else ""
		return f"FieldOperatorWithin({self.from_value}, {self.to_value}{subfield_str})"


class FieldOperatorAround(FieldOperator):
	"""Filter operator for values within percentage range"""

	def __init__(self, value, precision: float = 0.1, subfield: str = None):
		self.value = _parse_filter_value(value)
		self.precision = precision
		# Calculate bounds
		self.lower_bound = self.value / (1 + precision)
		self.upper_bound = self.value * (1 + precision)
		super().__init__(subfield)
		self._register_call_args("around", value, precision=precision)

	def apply_operation(self, field_value):
		if field_value is None:
			return FILTER_OUT
		try:
			return field_value if self.lower_bound <= field_value <= self.upper_bound else FILTER_OUT
		except (TypeError, ValueError):
			return FILTER_OUT

	def __repr__(self) -> str:
		subfield_str = f", subfield='{self.subfield}'" if self.subfield else ""
		return f"FieldOperatorAround({self.value}, precision={self.precision}{subfield_str})"


class FieldOperatorNone(FieldOperator):
	"""Filter operator for None values"""

	def __init__(self, subfield: str = None):
		super().__init__(subfield)
		self._register_call_args("none")

	def apply_operation(self, field_value):
		return field_value if field_value is None else FILTER_OUT

	def __repr__(self) -> str:
		subfield_str = f", subfield='{self.subfield}'" if self.subfield else ""
		return f"FieldOperatorNone({subfield_str})"


class FieldOperatorNotNone(FieldOperator):
	"""Filter operator for non-None values"""

	def __init__(self, subfield: str = None):
		super().__init__(subfield)
		self._register_call_args("not_none")

	def apply_operation(self, field_value):
		return field_value if field_value is not None else FILTER_OUT

	def __repr__(self) -> str:
		subfield_str = f", subfield='{self.subfield}'" if self.subfield else ""
		return f"FieldOperatorNotNone({subfield_str})"


class FieldPlugin(Plugin):

	def __init__(self, alias: Optional[str] = None):
		super().__init__(alias)
		self._operators = []  # Ordered list of FieldOperator instances

	@abstractmethod
	def field_values(self, item: BasketItem, output_data) -> List[Any]:
		pass

	@abstractmethod
	def field_types(self) -> List[Tuple[str, type]]:
		pass

	def run(self, runtime: 'BasketRuntime'):
		from fins.utils import ProgressTracker

		# Get field definitions
		field_types = self.field_types()

		# Register fields
		field_info = []
		for field_name, field_type in field_types:
			full_field_name = self.alias if field_name == "" else f"{self.alias}[{field_name}]"
			runtime.register_field(full_field_name, field_type)
			field_info.append((field_name, full_field_name))

		basket_items = runtime.basket_items()
		items_to_filter = set()  # Track items that should be filtered out
		
		tracker = ProgressTracker(len(basket_items), f"Computing {self.alias}")
		for idx, basket_item in enumerate(basket_items):
			try:
				field_values = self.field_values(basket_item, runtime.output_data().item_series(idx))
				filtered = self._set_field_values(runtime, idx, field_values, field_info)
				if filtered:
					items_to_filter.add(idx)
			except Exception as e:
				raise Exception(f"Failed to compute {self.alias} for {basket_item.ticker}: {e}") from e
			finally:
				tracker.next()
		tracker.done()

		# Remove filtered items after processing all items
		if items_to_filter:
			indices_to_remove = sorted(list(items_to_filter), reverse=True)
			runtime.remove_items(indices_to_remove)
			print(f"Filtered out {len(items_to_filter)} items based on {self.alias} operators")

	def _set_field_values(self, runtime: 'BasketRuntime', idx: int, field_values_list, field_info):
		"""
		Set values for field plugins - expects list format
		
		Returns:
			bool: True if this item should be filtered out, False otherwise
		"""
		if field_values_list is None:
			return False  # Skip setting any values, but don't filter out

		if not isinstance(field_values_list, list):
			raise ValueError(f"Plugin must return list or None, got {type(field_values_list)}")

		if len(field_values_list) != len(field_info):
			raise ValueError(
				f"Field values list length {len(field_values_list)} doesn't match field count {len(field_info)}")

		# Process each field value and check for filtering
		item_should_be_filtered = False
		
		for (field_name, full_field_name), value in zip(field_info, field_values_list):
			# Convert empty string to None for consistency with operator default
			subfield_for_operators = None if field_name == "" else field_name
			processed_value = self._apply_operators(value, subfield_for_operators)
			if processed_value is FILTER_OUT:
				item_should_be_filtered = True
				break  # If any field filters out, the entire item is filtered
			else:
				# If the value is a Media instance, register and store handle
				if isinstance(processed_value, Media):
					media_cache.register(processed_value)
					processed_value = processed_value.handle()
				runtime.set_field_value(idx, full_field_name, processed_value)
		
		return item_should_be_filtered

	def _apply_operators(self, field_value: Any, subfield: str = None) -> Any:
		"""Apply operator chain to field value (transformations and filtering)"""
		# Apply operators in sequence
		for operator in self._operators:
			field_value = operator.apply(field_value, subfield)
			# If any operator returns FILTER_OUT, stop processing
			if field_value is FILTER_OUT:
				return FILTER_OUT

		return field_value

	# Operator methods
	def log(self, *, subfield: str = None) -> 'FieldPlugin':
		self._operators.append(FieldOperatorLog(subfield))
		return self

	def min(self, value: Union[float, int, str, datetime], *, subfield: str = None) -> 'FieldPlugin':
		self._operators.append(FieldOperatorMin(value, subfield))
		return self

	def max(self, value: Union[float, int, str, datetime], *, subfield: str = None) -> 'FieldPlugin':
		self._operators.append(FieldOperatorMax(value, subfield))
		return self

	def equals(self, value: Any, *, subfield: str = None) -> 'FieldPlugin':
		self._operators.append(FieldOperatorEquals(value, subfield))
		return self

	def exclude(self, value: Union[float, int, str, list, tuple, set], *, subfield: str = None) -> 'FieldPlugin':
		self._operators.append(FieldOperatorExclude(value, subfield))
		return self

	def true(self, *, subfield: str = None) -> 'FieldPlugin':
		self._operators.append(FieldOperatorTrue(subfield))
		return self

	def false(self, *, subfield: str = None) -> 'FieldPlugin':
		self._operators.append(FieldOperatorFalse(subfield))
		return self

	def contains(self, value: Union[float, int, str], *, subfield: str = None) -> 'FieldPlugin':
		self._operators.append(FieldOperatorContains(value, subfield))
		return self

	def any(self, collection: Union[list, tuple, set], *, subfield: str = None) -> 'FieldPlugin':
		self._operators.append(FieldOperatorAny(collection, subfield))
		return self

	def within(self, from_value: Union[float, int], to_value: Union[float, int], *,
			   subfield: str = None) -> 'FieldPlugin':
		self._operators.append(FieldOperatorWithin(from_value, to_value, subfield))
		return self

	def around(self, value: Union[float, int], precision: float = 0.1, *, subfield: str = None) -> 'FieldPlugin':
		self._operators.append(FieldOperatorAround(value, precision, subfield))
		return self

	def none(self, *, subfield: str = None) -> 'FieldPlugin':
		self._operators.append(FieldOperatorNone(subfield))
		return self

	def not_none(self, *, subfield: str = None) -> 'FieldPlugin':
		self._operators.append(FieldOperatorNotNone(subfield))
		return self

	def __str__(self) -> str:
		"""Return Python code to recreate this plugin with its current configuration including chained operators."""
		# Get the base constructor representation from parent class
		base_str = super().__str__()
		
		# Add chained operators
		if self._operators:
			method_calls = [operator.to_method_call() for operator in self._operators]
			return base_str + ''.join(method_calls)
		
		return base_str
