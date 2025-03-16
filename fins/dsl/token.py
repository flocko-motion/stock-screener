"""
Token entity for FINS command line tokens.

This module provides the Token entity which represents a single command line token.
Tokens can be literals (strings, numbers) or references to other entities.
"""

from typing import Any, Union
from ..storage.entity import Entity

class Token(Entity):
    """
    Entity representing a single command line token.
    
    A token can be:
    - A literal string ("asc", "desc", etc.)
    - A number (1, 3.14, etc.)
    - A reference to another entity ($var, etc.)
    """
    
    def __init__(self, value: Any):
        """
        Initialize a token.
        
        Args:
            value: The token's value
        """
        self.value = value
        
    def __str__(self) -> str:
        return str(self.value)
        
    def __repr__(self) -> str:
        return f"Token({self.value!r})"
        
    def to_dict(self) -> dict:
        """Convert token to dictionary representation."""
        return {
            "type": "token",
            "value": self.value
        }
        
    @property
    def is_literal(self) -> bool:
        """Whether this token represents a literal value."""
        return isinstance(self.value, (str, int, float, bool))
        
    @property
    def is_reference(self) -> bool:
        """Whether this token represents a reference to another entity."""
        return isinstance(self.value, str) and self.value.startswith("$")
        
    def as_literal(self) -> Union[str, int, float, bool]:
        """
        Convert token to a literal value.
        
        Returns:
            The literal value
            
        Raises:
            ValueError: If token is not a literal
        """
        if not self.is_literal:
            raise ValueError(f"Token {self} is not a literal")
        return self.value
        
    def as_reference(self) -> str:
        """
        Get the name of the referenced entity.
        
        Returns:
            The referenced entity name without the $ prefix
            
        Raises:
            ValueError: If token is not a reference
        """
        if not self.is_reference:
            raise ValueError(f"Token {self} is not a reference")
        return self.value[1:]  # Remove $ prefix 