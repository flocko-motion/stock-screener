"""
Base class for FINS flow commands.

This module provides the foundation for implementing type-safe command flows in FINS.
Each command is implemented as a class that inherits from FlowCommand, specifying:
- Input type requirements
- Output type guarantees
- Help text and documentation
"""

from abc import ABC, abstractmethod
from typing import Type, Optional, Dict, Any
from ..storage.entity import Entity

class FlowCommand(ABC):
    """
    Abstract base class for all FINS flow commands.
    
    Each command must specify:
    - The required input type (what kind of Entity it expects)
    - The output type (what kind of Entity it produces)
    - Help text describing its usage
    """
    
    def __init__(self, **kwargs):
        """
        Initialize a flow command with its parameters.
        
        Args:
            **kwargs: Command-specific parameters
        """
        self.params = kwargs
        
    @property
    @abstractmethod
    def input_type(self) -> Type[Entity]:
        """The type of Entity this command expects as input."""
        pass
        
    @property
    @abstractmethod
    def output_type(self) -> Type[Entity]:
        """The type of Entity this command produces as output."""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """A short description of what this command does."""
        pass
        
    @property
    def parameters(self) -> Dict[str, str]:
        """
        A dictionary describing the command's parameters.
        
        Returns:
            Dict mapping parameter names to their descriptions
        """
        return {}
        
    @property
    def examples(self) -> Dict[str, str]:
        """
        Example usages of this command.
        
        Returns:
            Dict mapping example commands to their descriptions
        """
        return {}
        
    def help(self) -> str:
        """Generate help text for this command."""
        lines = [
            f"Command: {self.__class__.__name__}",
            "",
            self.description,
            "",
            f"Input: {self.input_type.__name__}",
            f"Output: {self.output_type.__name__}",
            ""
        ]
        
        if self.parameters:
            lines.extend([
                "Parameters:",
                *[f"  {name}: {desc}" for name, desc in self.parameters.items()],
                ""
            ])
            
        if self.examples:
            lines.extend([
                "Examples:",
                *[f"  {cmd}\n    {desc}" for cmd, desc in self.examples.items()],
                ""
            ])
            
        return "\n".join(lines)
        
    def validate_input(self, input_entity: Entity) -> None:
        """
        Validate that the input entity matches the required type.
        
        Args:
            input_entity: The input entity to validate
            
        Raises:
            TypeError: If input_entity is not of the required type
        """
        if not isinstance(input_entity, self.input_type):
            raise TypeError(
                f"{self.__class__.__name__} requires {self.input_type.__name__} input, "
                f"got {type(input_entity).__name__}"
            )
            
    @abstractmethod
    def execute(self, input_entity: Entity) -> Entity:
        """
        Execute the command on the input entity.
        
        Args:
            input_entity: The input entity to process
            
        Returns:
            The output entity
            
        Raises:
            TypeError: If input_entity is not of the required type
        """
        pass 