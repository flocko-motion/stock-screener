"""
Table data structure for formatting.

This module provides a simple table abstraction used by formatters.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Any, List


class ColumnType(Enum):
    STRING = auto()
    FLOAT = auto()
    WEIGHT = auto()


@dataclass
class Column:
    name: str
    type: ColumnType


class Row:
    def __init__(self, values: Dict[str, Any]):
        self.values = values

    def __getitem__(self, key: str) -> Any:
        return self.values[key]


class Table:
    def __init__(self, columns: List[Column]):
        self.columns = columns
        self.rows: List[Row] = []
        self._widths: Dict[str, int] = {col.name: len(col.name) for col in columns}

    def add_row(self, values: Dict[str, Any]) -> None:
        """Add a row and update column widths."""
        row = Row(values)
        self.rows.append(row)
        
        # Update column widths
        for col in self.columns:
            width = len(str(values[col.name]))
            self._widths[col.name] = max(self._widths[col.name], width)

    def get_column_width(self, name: str) -> int:
        """Get the width needed for a column."""
        return self._widths[name] 