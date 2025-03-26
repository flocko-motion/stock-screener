"""
Table Formatters

This module defines formatters for converting Table objects into various output formats.
Each formatter follows the Strategy pattern, allowing easy addition of new output formats.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, NamedTuple

from .table import Table, Column, ColumnType
from ..entities.basket import Basket


@dataclass
class Column:
    name: str
    width: int = 0


class Row:
    def __init__(self, values: Dict[str, Any]):
        self.values = values


class Table:
    def __init__(self, columns: List[Column]):
        self.columns = columns
        self.rows: List[Row] = []

    def add_row(self, values: Dict[str, Any]) -> None:
        self.rows.append(Row(values))


class BasketFormatter(ABC):
    """Base class for all basket formatters."""
    
    def format(self, basket: Basket) -> str:
        """
        Format a basket into a specific output format.
        
        Args:
            basket: The basket to format
            
        Returns:
            The formatted output as a string
        """
        if not basket.items:
            return ""
            
        table = self._build_table(basket)
        return self._format_table(table)

    def _build_table(self, basket: Basket) -> Table:
        """Convert a basket into a table structure with computed column widths."""
        # Define columns
        columns = [
            Column("Weight"),
            Column("Symbol")
        ]
        columns.extend(Column(name) for name in basket.columns)

        # Create table
        table = Table(columns)

        # Calculate column widths and build rows
        for item in self._sort_items(basket):
            # Build row values
            values = {
                "Weight": str(item.amount),
                "Symbol": item.ticker
            }
            for col_name in basket.columns:
                values[col_name] = str(basket.columns[col_name].get(item))

            # Update column widths
            for col in columns:
                col.width = max(col.width, len(col.name), len(values[col.name]))

            table.add_row(values)

        return table

    def _sort_items(self, basket: Basket) -> List[Any]:
        """Sort basket items by weight (descending) or symbol if weights are equal."""
        if all(item.amount == 1 for item in basket.items):
            return sorted(basket.items, key=lambda item: item.ticker)
        return sorted(basket.items, key=lambda item: (-item.amount, item.ticker))

    @abstractmethod
    def _format_table(self, table: Table) -> str:
        """
        Format the table into the specific output format.
        
        Args:
            table: The table to format
            
        Returns:
            The formatted output as a string
        """
        pass


class TextBasketFormatter(BasketFormatter):
    """Formats baskets as plain text with aligned columns."""
    
    def __init__(self, show_header: bool = True):
        self.show_header = show_header
    
    def _format_table(self, table: Table) -> str:
        """Format the table as aligned text columns."""
        lines = []

        # Format header
        if self.show_header:
            header = " | ".join(
                col.name.ljust(col.width)
                for col in table.columns
            )
            separator = "-+-".join("-" * col.width for col in table.columns)
            lines.extend([header, separator])

        # Format rows
        for row in table.rows:
            line = " | ".join(
                str(row.values[col.name]).ljust(col.width)
                for col in table.columns
            )
            lines.append(line)

        return "\n".join(lines)
