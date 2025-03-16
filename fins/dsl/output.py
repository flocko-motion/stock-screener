"""
Output class for FINS commands.

This module provides a standardized way to represent command outputs in FINS.
Each command's result is wrapped in an Output instance that contains:
- The actual result data (Basket, value, etc.)
- Metadata about the output type
- Pretty printing capabilities
"""

import json
from typing import Any, Optional, Dict, Union
from ..entities.basket import Basket

class Output:
    """
    Wrapper class for FINS command outputs.
    
    Attributes:
        data: The actual output data (Basket, value, etc.)
        output_type: Type of the output (basket, value, error, etc.)
        metadata: Optional metadata about the output
    """
    
    def __init__(self, 
                 data: Any, 
                 output_type: str = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize an Output instance.
        
        Args:
            data: The actual output data
            output_type: Type of the output. If None, will be inferred from data
            metadata: Optional metadata about the output
        """
        self.data = data
        self.output_type = output_type or self._infer_type()
        self.metadata = metadata or {}
        
    def _infer_type(self) -> str:
        """Infer the output type from the data."""
        if isinstance(self.data, Basket):
            return "basket"
        elif isinstance(self.data, (int, float)):
            return "number"
        elif isinstance(self.data, str):
            return "text"
        elif isinstance(self.data, bool):
            return "boolean"
        elif isinstance(self.data, Exception):
            return "error"
        elif self.data is None:
            return "void"
        else:
            return "unknown"
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert the output to a dictionary representation."""
        return {
            "type": self.output_type,
            "data": self._serialize_data(),
            "metadata": self.metadata
        }
        
    def _serialize_data(self) -> Any:
        """Serialize the data for JSON output."""
        if isinstance(self.data, Basket):
            return self.data.to_dict()
        elif isinstance(self.data, Exception):
            return str(self.data)
        return self.data
        
    def __str__(self) -> str:
        """Return a string representation of the output."""
        if self.output_type == "error":
            return f"Error: {str(self.data)}"
        elif self.output_type == "void":
            return ""
        return json.dumps(self.to_dict(), indent=2)
        
    def __repr__(self) -> str:
        """Return a detailed string representation."""
        return f"Output(type={self.output_type}, data={self.data}, metadata={self.metadata})" 