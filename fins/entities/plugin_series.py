from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import Optional, List, Union, Any
import pandas as pd

from fins.entities import BasketItem, Basket, Plugin
from fins.financial import Symbol
from fins.utils import format_value


class SeriesOperator(ABC):
	"""
	A series operator that transforms time series data.
	"""

	def __init__(self):
		pass

	def _register_call_args(self, method_name: str, *args, **kwargs):
		"""Register method call arguments for string representation."""
		self._method_name = method_name
		self._call_args = args
		self._call_kwargs = kwargs

	def to_method_call(self) -> str:
		"""Return the method call representation."""
		if not hasattr(self, '_method_name'):
			raise RuntimeError(f"Operator {self.__class__.__name__} must call self._register_call_args() in __init__")
		
		# Format positional arguments
		formatted_args = [format_value(arg) for arg in self._call_args]
		
		# Format keyword arguments
		formatted_kwargs = [f"{key}={format_value(value)}" for key, value in self._call_kwargs.items()]
		
		# Combine all arguments
		all_args = formatted_args + formatted_kwargs
		
		if not all_args:
			return f".{self._method_name}()"
		
		args_str = ", ".join(all_args)
		return f".{self._method_name}({args_str})"

	@abstractmethod
	def apply_transformation(self, df: pd.DataFrame) -> pd.DataFrame:
		"""Apply this operator's transformation to the DataFrame."""
		pass

	@abstractmethod
	def transform_alias(self, original_alias: str) -> str:
		"""Transform the plugin alias to reflect this operation."""
		pass


class YoyOperator(SeriesOperator):
	"""Year-over-Year transformation operator."""

	def __init__(self):
		super().__init__()
		self._register_call_args("yoy")

	def apply_transformation(self, df: pd.DataFrame) -> pd.DataFrame:
		"""Calculate Year-over-Year changes for time series data"""
		if df.empty or len(df) < 2:
			return df

		# Ensure date column exists and is properly formatted
		if 'date' not in df.columns:
			return df

		# Sort by date to ensure proper ordering
		df_sorted = df.sort_values('date').copy()

		# Extract year from date for YoY comparison
		df_sorted['year'] = pd.to_datetime(df_sorted['date']).dt.year

		# Get value column (typically the second column after date)
		value_col = df_sorted.columns[1]  # Assuming [date, close_price, ...]

		# Calculate YoY changes
		yoy_values = []
		for idx, row in df_sorted.iterrows():
			current_year = row['year']
			current_value = row[value_col]

			# Find value from same period previous year
			prev_year_data = df_sorted[df_sorted['year'] == current_year - 1]

			if not prev_year_data.empty and current_value is not None:
				# Use the closest date match from previous year
				prev_value = prev_year_data.iloc[-1][value_col]  # Take last value from prev year

				if prev_value is not None and prev_value != 0:
					yoy_change = (current_value - prev_value) / prev_value
					yoy_values.append(yoy_change)
				else:
					yoy_values.append(None)
			else:
				yoy_values.append(None)

		# Create result DataFrame with YoY values
		result_df = df_sorted.copy()
		result_df[value_col] = yoy_values
		result_df = result_df.drop('year', axis=1)  # Remove helper column

		# Set data type for plotting
		result_df.attrs['type'] = 'yoy'
		# Keep original title but indicate it's YoY transformed
		if 'title' in df.attrs:
			result_df.attrs['title'] = df.attrs['title'] + ' (YoY)'

		return result_df

	def transform_alias(self, original_alias: str) -> str:
		"""Add YoY suffix to the alias."""
		return f"{original_alias}YoY"


class LogOperator(SeriesOperator):
	"""Log10 transformation operator."""

	def __init__(self):
		super().__init__()
		self._register_call_args("log")

	def apply_transformation(self, df: pd.DataFrame) -> pd.DataFrame:
		"""Apply log10 transformation to time series values"""
		import math

		if df.empty:
			return df

		result_df = df.copy()
		value_col = result_df.columns[1]  # Assuming [date, close_price, ...]

		# Apply log10 to positive values
		result_df[value_col] = result_df[value_col].apply(
			lambda x: math.log10(x) if x is not None and x > 0 else None
		)

		# Set data type for plotting
		result_df.attrs['type'] = 'log'
		# Keep original title but indicate it's Log transformed
		if 'title' in df.attrs:
			result_df.attrs['title'] = df.attrs['title'] + ' (Log)'

		return result_df

	def transform_alias(self, original_alias: str) -> str:
		"""Add Log suffix to the alias."""
		return f"{original_alias}Log"


class SeriesPlugin(Plugin):

	def __init__(self, alias: Optional[str] = None):
		super().__init__(alias)
		self._operators = []  # List of SeriesOperator instances

	@abstractmethod
	def field_value(self, item: BasketItem) -> pd.DataFrame:
		pass

	def field_type(self) -> type:
		return pd.DataFrame

	def yoy(self) -> 'SeriesPlugin':
		"""Transform time series to Year-over-Year changes: series.yoy()"""
		yoy_op = YoyOperator()
		self._operators.append(yoy_op)
		
		# Transform the alias
		self.alias = yoy_op.transform_alias(self.alias)
		
		return self

	def log(self) -> 'SeriesPlugin':
		log_op = LogOperator()
		self._operators.append(log_op)
		self.alias = log_op.transform_alias(self.alias)
		return self

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
			base_str = f"{class_name}()"
		else:
			args_str = ", ".join(all_args)
			base_str = f"{class_name}({args_str})"
		
		# Add operator calls
		for operator in self._operators:
			base_str += operator.to_method_call()
		
		return base_str

	def _apply_series_transformations(self, df: pd.DataFrame) -> pd.DataFrame:
		"""Apply transformations to time series DataFrame"""
		if df.empty:
			return df

		# Make a copy to avoid modifying original
		result_df = df.copy()

		# Apply each operator transformation in sequence
		for operator in self._operators:
			result_df = operator.apply_transformation(result_df)

		return result_df

	def run(self, runtime: 'BasketRuntime'):
		"""Run series plugin to generate time series data"""
		# Register the field as a DataFrame type
		runtime.register_field(self.alias, self.field_type())

		basket_items = runtime.basket_items()
		for idx, basket_item in enumerate(basket_items):
			try:
				# Get the raw time series data
				series_data = self.field_value(basket_item)

				# Apply transformations
				if self._operators:
					series_data = self._apply_series_transformations(series_data)

				# Store the transformed series data
				runtime.set_field_value(idx, self.alias, series_data)
			except Exception as e:
				raise Exception(f"Failed to compute {self.alias} for {basket_item.ticker}: {e}") from e

