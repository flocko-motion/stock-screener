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
from typing import Any, Optional, Dict, Union, List
from ..entities.basket import Basket

class Output:
    """
    Wrapper class for FINS command outputs.
    
    Attributes:
        data: The actual output data (Basket, value, etc.)
        output_type: Type of the output (basket, value, error, etc.)
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
        self.output_type = output_type or self._infer_type()
        self.metadata = metadata or {}
        self.log = log or []
        
        # If data is a string and output_type is not error, add it to the log
        if isinstance(data, str) and self.output_type != "error":
            self.add_log(data)

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
        return self.output_type == "error"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the output to a dictionary representation."""
        return {
            "type": self.output_type,
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
        if self.output_type == "error":
            return f"Error: {str(self.data)}"
        elif self.output_type == "void":
            return ""
            
        # If we have log messages, show them
        if self.log:
            return "\n".join(self.log)
            
        return json.dumps(self.to_dict(), indent=2)
        
    def __repr__(self) -> str:
        """Return a detailed string representation."""
        return f"Output(type={self.output_type}, data={self.data}, metadata={self.metadata}, log={self.log})"

