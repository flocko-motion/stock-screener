"""
Output class for FINS commands.

This module provides a standardized way to represent command outputs in FINS.
Each command's result is wrapped in an Output instance that contains:
- The actual result data (Basket, value, etc.)
- Metadata about the output type
- Log messages describing what happened during execution
- Pretty printing capabilities
"""

import json
import traceback
from types import NoneType
from typing import Any, Optional, Dict, Union, List

from fins.entities.basket import Basket

class Output:
    """
    Wrapper class for FINS command outputs.
    
    Attributes:
        data: The actual output data (Basket, value, etc.)
        metadata: Optional metadata about the output
        log: List of log messages describing what happened during execution
    """
    
    def __init__(self,
                 data: Any,
                 metadata: Optional[Dict[str, Any]] = None,
                 log: Optional[List[str]] = None,
                 previous: Optional['Output'] = None):
        """
        Initialize an Output instance.
        
        Args:
            data: The actual output data
            output_type: Type of the output. If None, will be inferred from data
            metadata: Optional metadata about the output
            log: Optional list of log messages
        """
        self.data = data
        self.metadata = metadata or {}
        self.log = log or []
        
        if isinstance(data, str) and  not isinstance(data, Exception):
            self.add_log(data)

    def has_data(self):
        return not self.is_void() and not self.has_error()

    def add_log(self, message: str) -> None:
        """
        Add a log message to the output.
        
        Args:
            message: The log message to add
        """
        self.log.append(message)
        
    def merge_logs(self, other_output: 'Output') -> None:
        """
        Merge logs from another output into this one.
        
        Args:
            other_output: The output to merge logs from
        """
        if other_output and hasattr(other_output, 'log'):
            self.log.extend(other_output.log)

    def has_error(self) -> bool:
        return isinstance(self.data, Exception)

    def is_void(self) -> bool:
        return isinstance(self.data, NoneType)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the output to a dictionary representation."""
        return {
            "type": type(self.data),
            "data": self._serialize_data(),
            "metadata": self.metadata,
            "log": self.log
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
        if self.has_error():
            return f"Error: {str(self.data)}"
        elif self.is_void() == "void":
            return ""
            
        # If we have log messages, show them
        if self.log:
            return "\n".join(self.log)
            
        return json.dumps(self.to_dict(), indent=2)
        
    def __repr__(self) -> str:
        """Return a detailed string representation."""
        return f"Output(type={type(self.data)}, data={self.data}, metadata={self.metadata}, log={self.log})"

    def is_type(self, output_type: type) -> bool:
        return isinstance(self.data, output_type)

    def assert_type(self, output_type) -> bool:
        if not self.is_type(output_type):
            raise TypeError(f"Expected output type '{output_type}', got '{type(self.data)}'")
        return True





