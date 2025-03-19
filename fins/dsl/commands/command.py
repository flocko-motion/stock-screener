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
from typing import Type, Optional, Any, NamedTuple, Sequence

from lark import Tree

from ...entities import Entity
from ..output import Output
from collections.abc import Sequence
from typing import get_origin

class CommandArgs(NamedTuple):
    tree: Tree
    

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
    def input_type(self):
        """
        The type of Entity this command expects as input.
        """
        pass
        
    @property
    @abstractmethod
    def output_type(self)  -> Type[Entity] | Type[Sequence[Entity]] | Type[Sequence[Entity]] | Type[Optional[Entity]] | None:
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
    def right_tokens(self) -> dict[str, str]:
        """Description of right-hand tokens."""
        return {}
        
    @property
    def examples(self) -> dict[str, str]:
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

        TODO: Implement a generic input types checking system. This could be based on a type-checking class
        that contains a list of types and alternatives and allowed repetitions and omissions..
        As this is not crucial to the functionality of this program, we might just never need it and
        rely on the functions execution block to throw errors where invalid values are found.
        """
        return

    def validate_output(self, output):
        if isinstance(output, self.output_type):
            return
        else:
            raise ValueError(f"output '{output}' is not of expected type '{self.output_type}'")

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
        self.validate_input(args)
        result = self.execute(args)
        self.validate_output(result)
        
        command_name = self.__class__.__name__.replace('Command', '').lower()
        log_message = f"Executed {command_name} command"
        
        # Create output with log message and metadata
        output = Output(result, "basket", metadata={"command": command_name})
        output.add_log(log_message)
        
        return output 