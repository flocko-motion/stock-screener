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

class CommandArg:
    """ definition of an argument for a command"""
    def __init__(self,name: str | None = None, description: str = "", optional: bool = True, default: str = ""):
        self.name = name
        self.description = description
        self.optional = optional
        self.default = default

@dataclass
class CommandArgs:
    """Arguments for command execution."""
    tree: Tree
    previous_output: Output | None
    storage: Storage
    cmd: Command | None

    def __init__(self, tree: Tree, storage: Storage, previous_output: Output | None = None, cmd: Command | None = None):
        self.tree = tree
        self.storage = storage
        self.previous_output = previous_output
        if self.previous_output is None:
            self.previous_output = Output(None)
        self.cmd = cmd

    def has_previous_output(self, type: Type = None) -> bool:
        res: bool = self.previous_output is not None and not self.previous_output.is_void()
        if type is not None:
            return res and self.previous_output.is_type(type)
        return res

    def get_previous_basket(self) -> Basket:
        if self.has_previous_output(Basket):
            return self.previous_output.data
        raise SyntaxError("Expected a basket as previous output")

    def validate(self):
        named_args: list[CommandArg] = self.cmd.__class__.named_args()
        for named_arg in named_args:
            if not named_arg.optional and self.get_named_arg(named_arg.name) is None:
                raise SyntaxError(f"Missing required argument '{named_arg.name}'")


    def get_named_arg(self, name):
        if self.cmd is None:
            raise Exception("implementation error: self.cmd should not be None when using named args")
        named_args: list[CommandArg] = self.cmd.__class__.named_args()
        for named_arg in named_args:
            if named_arg.name != name:
                continue

            if not (self.tree is None):
                for c in self.tree.children:
                    if isinstance(c, Tree):
                        if str(c.data) == "named_arg":
                            if name == str(c.children[0]):
                                v = str(c.children[1].children[0])
                                if v.startswith('"') and v.endswith('"'):
                                    v = v[1:-1]
                                return v
            return named_arg.default
        return None



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

    _name = "<filled_by_register_decorator>"
    @classmethod
    def name(cls):
        return cls._name

    @classmethod
    @abstractmethod
    def named_args(cls) -> list[CommandArg]:
        """Define named arguments available for this command and their descriptions."""
        return []

    @classmethod
    @abstractmethod
    def input_type(cls) -> type:
        """Get the type of input this command expects."""
        pass

    @classmethod
    @abstractmethod
    def output_type(cls) -> type:
        """Get the type of output this command produces."""
        pass

    @classmethod
    @abstractmethod
    def category(cls) -> str | None:
        pass

    @classmethod
    @abstractmethod
    def description(cls) -> str:
        """Get a description of what this command does."""
        pass

    @classmethod
    @abstractmethod
    def examples(cls) -> str | None:
        """Example usages of this command."""
        return None

    @abstractmethod
    def execute(self, args: CommandArgs) -> Optional['Output']:
        """Execute the command with the given arguments."""
        pass

    @classmethod
    def register(cls, name: str):
        """Class decorator to register a command type."""
        def decorator(command_cls: Type['Command']):
            cls._registry[name] = command_cls
            command_cls._name = name
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
    def allows_explicit_left_hand(self) -> bool:
        """Whether this command supports explicit left-hand syntax (e.g. '$a + NFLX')."""
        return True



    @property
    def right_tokens(self) -> dict[str, str]:
        """Description of right-hand tokens."""
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

