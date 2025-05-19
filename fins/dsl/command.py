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

from abc import ABC, abstractmethod, abstractclassmethod
from distutils.cmd import Command
from typing import Type, Optional, Any, NamedTuple, Sequence, Dict, ClassVar, List
from dataclasses import dataclass
from lark import Tree, Token

from fins.entities import Entity, Basket, Column
from fins.storage import Storage

from . import Output



@dataclass
class CommandArgs:
    """Arguments for command execution."""
    tree: Tree
    previous_output: Output | None
    storage: Storage

    def __init__(self, tree: Tree, storage: Storage, previous_output: Output | None = None):
        self.tree = tree
        self.storage = storage
        self.previous_output = previous_output
        if self.previous_output is None:
            self.previous_output = Output(None)

    def has_previous_output(self, type: Type = None) -> bool:
        res: bool = self.previous_output is not None and not self.previous_output.is_void()
        if type is not None:
            return res and self.previous_output.is_type(type)
        return res

    def get_previous_basket(self) -> Basket:
        if self.has_previous_output(Basket):
            return self.previous_output.data
        raise SyntaxError("Expected a basket as previous output")


class Command(ABC):
    """
    Abstract base class for all FINS commands.
    
    Each command must specify:
    - The required input types (what kinds of Entities it expects)
    - The output type (what kind of Entity it produces)
    - Help text describing its usage
    """
    
    # Class-level registry of all commands
    _registry: ClassVar[Dict[str, Type['Command']]] = {}
    
    # Instance-level command cache
    _instances: ClassVar[Dict[str, 'Command']] = {}
    
    def __init__(self):
        pass

    @classmethod
    def register(cls, command_type: str):
        """Class decorator to register a command type."""
        def decorator(command_cls: Type['Command']):
            cls._registry[command_type] = command_cls
            return command_cls
        return decorator

    @classmethod
    def register_command(cls, name: str, command_cls: Type['Command']) -> None:
        """Register a command with the given name."""
        cls._registry[name] = command_cls

    @classmethod
    def get_command(cls, command_name: str) -> 'Command':
        if not isinstance(command_name, str):
            raise ValueError(f"command_type must be a string, not {type(command_name)}")

        if command_name not in cls._instances:
            if command_name not in cls._registry:
                raise SyntaxError(f"Unknown command type: {command_name}")
            cls._instances[command_name] = cls._registry[command_name]()
        return cls._instances[command_name]

    @classmethod
    def get_name_of_command(cls, command: type[Command]) -> str | None:
        return next((key for key, value in Command._registry.items() if value == command), None)

    @classmethod
    def get_commands(cls) -> Dict[str, type[Command]]:
        return cls._registry

    @property
    @abstractmethod
    def input_type(self) -> str:
        """Get the type of input this command expects."""
        pass
        
    @property
    @abstractmethod
    def output_type(self) -> str:
        """Get the type of output this command produces."""
        pass
        
    @property
    def allows_explicit_left_hand(self) -> bool:
        """Whether this command supports explicit left-hand syntax (e.g. '$a + NFLX')."""
        return True

    @classmethod
    @abstractmethod
    def category(cls) -> str | None:
        pass

    @classmethod
    @abstractmethod
    def description(cls) -> str:
        """Get a description of what this command does."""
        pass
        
    @property
    def right_tokens(self) -> dict[str, str]:
        """Description of right-hand tokens."""
        return {}
        
    @property
    def examples(self) -> dict[str, str]:
        """Example usages of this command."""
        return {}

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
    def execute(self, args: CommandArgs) -> Optional['Output']:
        """Execute the command with the given arguments."""
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

    @classmethod
    def execute_tree(cls, args: CommandArgs) -> 'Output':
        """Evaluate a tree."""
        command_type = args.tree.data
        handler = cls.get_command(command_type)
        return handler.execute(args)


    @staticmethod
    def _parse_weight(value):
        if value.endswith("x"):
            return float(value.rstrip("x"))
        return float(value)

