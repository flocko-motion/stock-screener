"""
Base class for FINS commands.

This module provides the foundation for implementing type-safe commands in FINS.
Each command is implemented as a class that inherits from Command, specifying:
- Input type requirements (what kinds of Entities it expects)
- Output type guarantees (what kind of Entity it produces)
- Help text and documentation

Command Execution Flow:
---------------------
1. Commands can be invoked in two ways:
   a) Explicit left-hand: "$a + NFLX"  (left_input=$a, operator=+, right_input=NFLX)
   b) Implicit left-hand: "$a -> + NFLX"  (implicit_input=$a, operator=+, right_input=NFLX)

2. Every command:
   - Processes its inputs
   - Performs its operation
   - Returns its (possibly modified) input to allow chaining

Example:
-------
"$tech_stocks + NFLX -> sort mcap"
- First command: add NFLX to $tech_stocks basket
- Second command: sort the resulting basket
"""

from abc import ABC, abstractmethod
from typing import Type, Optional, Dict, Any, NamedTuple, List, Sequence
from ...entities.entity import Entity
from ..token import Token
from ..output import Output

class CommandArgs(NamedTuple):
    """
    Container for command arguments.
    
    Attributes:
        implicit_input: Input from previous command (if using -> syntax)
        left_input: Explicit left-hand input (if using direct syntax)
        right_input: Right-hand tokens after the command
    """
    implicit_input: Optional[Entity]
    left_input: Optional[Entity]
    right_input: Sequence[Entity]
    
    @property
    def effective_input(self) -> Optional[Entity]:
        """Returns the effective input (explicit takes precedence over implicit)."""
        return self.left_input if self.left_input is not None else self.implicit_input

class Command(ABC):
    """
    Abstract base class for all FINS commands.
    
    Each command must specify:
    - The required input types (what kinds of Entities it expects)
    - The output type (what kind of Entity it produces)
    - Help text describing its usage
    """
    
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
    def allows_explicit_left_hand(self) -> bool:
        """Whether this command supports explicit left-hand syntax (e.g. '$a + NFLX')."""
        return True
        
    @property
    @abstractmethod
    def description(self) -> str:
        """A short description of what this command does."""
        pass
        
    @property
    def right_tokens(self) -> Dict[str, str]:
        """Description of right-hand tokens."""
        return {}
        
    @property
    def examples(self) -> Dict[str, str]:
        """Example usages of this command."""
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
            "",
            "Syntax:",
            f"  {self.__class__.__name__.lower()} [right_tokens]  # Implicit input",
        ]
        
        if self.allows_explicit_left_hand:
            lines.append(f"  input {self.__class__.__name__.lower()} [right_tokens]  # Explicit input")
            
        if self.right_tokens:
            lines.extend([
                "",
                "Right Tokens:",
                *[f"  {name}: {desc}" for name, desc in self.right_tokens.items()]
            ])
            
        if self.examples:
            lines.extend([
                "",
                "Examples:",
                *[f"  {cmd}\n    {desc}" for cmd, desc in self.examples.items()]
            ])
            
        return "\n".join(lines)
        
    def validate_input(self, args: CommandArgs) -> None:
        """
        Validate command input and arguments.
        
        Args:
            args: The command arguments to validate
            
        Raises:
            TypeError: If input is not of the required type
            ValueError: If arguments are invalid
        """
        input_entity = args.effective_input
        if input_entity is not None and not isinstance(input_entity, self.input_type):
            raise TypeError(
                f"{self.__class__.__name__} requires input of type {self.input_type.__name__}, "
                f"got {type(input_entity).__name__}"
            )
            
    @abstractmethod
    def execute(self, args: CommandArgs) -> Entity:
        """
        Execute the command.
        
        Args:
            args: The command arguments
            
        Returns:
            The output entity (usually the modified input)
            
        Raises:
            TypeError: If input is not of the required type
            ValueError: If arguments are invalid
        """
        pass
        
    def execute_with_output(self, args: CommandArgs) -> Output:
        """
        Execute the command and wrap the result in an Output object.
        
        Args:
            args: The command arguments
            
        Returns:
            Output object containing the result of the command execution
        """
        result = self.execute(args)
        
        # Create a descriptive log message based on the command
        command_name = self.__class__.__name__.replace('Command', '').lower()
        log_message = f"Executed {command_name} command"
        
        # Create output with log message and metadata
        output = Output(result, "basket", metadata={"command": command_name})
        output.add_log(log_message)
        
        return output 