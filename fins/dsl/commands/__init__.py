"""Command module initialization."""

# Import all commands to trigger registration
from .sort import SortColumnCommand
from .filter import FilterCommand
from .union import UnionCommand
from .subtraction import SubtractionCommand
from .intersection import IntersectionCommand
from .spread import SpreadCommand
from .create import CreateBasketCommand
from .variable import VariableCommand
from .column import AddColumnCommand
from .info import InfoCommand
from .define import DefineFunctionCommand
from .syntax_operation import OperationCommand
from .syntax_sequence import SequenceCommand
from .syntax_basket import BasketCommand
from .syntax_function_definition import FunctionDefinitionCommand
from .syntax_operand_group import OperandGroupCommand
from .syntax_command_chain import CommandChainCommand 