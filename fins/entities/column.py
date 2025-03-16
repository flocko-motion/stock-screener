"""
Column Entity

This module defines the Column class, which represents an analysis column in a basket.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable


@dataclass
class Column:
    """
    Represents an analysis column in a basket.
    
    Attributes:
        name (str): The name of the column
        column_type (str): The type of column (e.g., 'cagr', 'pe', 'dividend_yield')
        start_year (Optional[int]): The start year for time-based columns
        end_year (Optional[int]): The end year for time-based columns
        period (Optional[str]): The period for time-based columns (e.g., 'annual', 'quarterly')
        data_source (Optional[str]): The source of the data
        calculator (Optional[Callable]): A function to calculate the column values
        metadata (Dict[str, Any]): Additional metadata for the column
    """
    
    name: str
    column_type: str
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    period: Optional[str] = None
    data_source: Optional[str] = None
    calculator: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        """Return the string representation of the column."""
        if self.start_year and self.end_year:
            return f"{self.name} ({self.column_type} {self.start_year}-{self.end_year})"
        return f"{self.name} ({self.column_type})"
    
    def calculate(self, symbol_data: Dict[str, Any]) -> Any:
        """
        Calculate the column value for a symbol.
        
        Args:
            symbol_data: The data for the symbol
            
        Returns:
            The calculated value
        """
        if self.calculator:
            return self.calculator(symbol_data, self)
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the column to a dictionary.
        
        Returns:
            A dictionary representation of the column
        """
        result = {
            'name': self.name,
            'type': self.column_type
        }
        
        if self.start_year:
            result['start_year'] = self.start_year
        if self.end_year:
            result['end_year'] = self.end_year
        if self.period:
            result['period'] = self.period
        if self.data_source:
            result['data_source'] = self.data_source
        if self.metadata:
            result['metadata'] = self.metadata
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Column':
        """
        Create a column from a dictionary.
        
        Args:
            data: The dictionary containing column data
            
        Returns:
            A new Column instance
        """
        return cls(
            name=data.get('name'),
            column_type=data.get('type'),
            start_year=data.get('start_year'),
            end_year=data.get('end_year'),
            period=data.get('period'),
            data_source=data.get('data_source'),
            metadata=data.get('metadata', {})
        ) 