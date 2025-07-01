
from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import Optional, List, Union, Any
import pandas as pd

from fins.entities import BasketItem, Basket, Plugin
from fins.financial import Symbol


class SeriesPlugin(Plugin):

	def __init__(self, alias: Optional[str] = None):
		super().__init__(alias)
		self._transformations = []  # List of transformation functions to apply in sequence

	@abstractmethod
	def field_value(self, item: BasketItem) -> pd.DataFrame:
		pass

	def field_type(self) -> type:
		return pd.DataFrame

	def yoy(self) -> 'SeriesPlugin':
		"""Transform time series to Year-over-Year changes: series.yoy()"""
		self._transformations.append(self._apply_yoy_transformation)
		return self

	def log(self) -> 'SeriesPlugin':
		"""Transform time series values to log10: series.log()"""
		self._transformations.append(self._apply_log_transformation)
		return self

	def _apply_series_transformations(self, df: pd.DataFrame) -> pd.DataFrame:
		"""Apply transformations to time series DataFrame"""
		if df.empty:
			return df

		# Make a copy to avoid modifying original
		result_df = df.copy()

		# Apply each transformation function in sequence
		for transform_func in self._transformations:
			result_df = transform_func(result_df)

		return result_df

	def _apply_yoy_transformation(self, df: pd.DataFrame) -> pd.DataFrame:
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

		return result_df

	def _apply_log_transformation(self, df: pd.DataFrame) -> pd.DataFrame:
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
				if self._transformations:
					series_data = self._apply_series_transformations(series_data)

				# Store the transformed series data
				runtime.set_field_value(idx, self.alias, series_data)
			except Exception as e:
				raise Exception(f"Failed to compute {self.alias} for {basket_item.ticker}: {e}") from e

