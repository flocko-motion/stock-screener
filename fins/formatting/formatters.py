"""
Formatters for FINS

This module defines formatters for converting Table objects into various output formats.
Each formatter follows the Strategy pattern, allowing easy addition of new output formats.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .table import Table, Column, ColumnType
from ..entities.basket import Basket


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
            Column("Weight", ColumnType.WEIGHT),
            Column("Symbol", ColumnType.STRING)
        ]
        columns.extend(Column(name, ColumnType.FLOAT) for name in basket.columns)

        # Create table
        table = Table(columns)

        # Add rows sorted by weight
        sorted_items = sorted(basket.items, key=lambda x: (-x.amount, x.ticker))
        for item in sorted_items:
            values = {
                "Weight": f"{item.amount:.4f}",
                "Symbol": item.ticker
            }
            for col_name in basket.columns:
                values[col_name] = str(basket.columns[col_name].get(item))
            table.add_row(values)

        return table

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
    """Formats baskets as plain text with aligned columns and borders."""
    
    def __init__(self, show_header: bool = True):
        self.show_header = show_header
    
    def _format_table(self, table: Table) -> str:
        """Format the table as aligned text columns with borders."""
        lines = []
        
        # Get column widths
        widths = {col.name: table.get_column_width(col.name) for col in table.columns}
        
        # Create border line
        border = "+"
        for col in table.columns:
            border += "-" * (widths[col.name] + 2) + "+"
        
        # Add top border
        lines.append(border)
        
        # Format header
        if self.show_header:
            header = "|"
            for col in table.columns:
                header += f" {col.name.ljust(widths[col.name])} |"
            lines.extend([header, border])

        # Format rows
        for row in table.rows:
            line = "|"
            for col in table.columns:
                value = str(row[col.name])
                # Right-align numbers, left-align text
                if col.type in (ColumnType.FLOAT, ColumnType.WEIGHT):
                    value = value.rjust(widths[col.name])
                else:
                    value = value.ljust(widths[col.name])
                line += f" {value} |"
            lines.append(line)
        
        # Add bottom border
        lines.append(border)
        
        return "\n".join(lines)
