"""
Financial Classes

This package contains the core financial classes used throughout the FINS system. These classes contain
the core logic for managing financial data and performing financial calculations.

For each ticker, we need only a single Symbol object, which contains the data for that ticker and provides
methods for calculating various financial metrics.

Symbols don't need to be persisted - they are created on-the-fly from data retrieved from the data_sources module.
"""

from .symbol import Symbol

__all__ = [
	Symbol,
]