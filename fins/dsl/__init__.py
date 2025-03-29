"""
FINS DSL (Domain Specific Language) module

This module contains the parser, transformer, and command functions for the FINS DSL.
"""
import importlib
import os
import pkgutil

__all__ = [
	"Output",
	"Command",
	"CommandArgs",
]

from .output import Output
from .command import Command, CommandArgs
from .command_column import ColumnCommand
from .parser import FinsParser


# Dynamically import all modules from the commands subdirectory
commands_dir = os.path.join(os.path.dirname(__file__), "commands")
for _, name, is_pkg in pkgutil.iter_modules([commands_dir]):
	if not is_pkg and name != "__init__":
		importlib.import_module(f"fins.dsl.commands.{name}")


