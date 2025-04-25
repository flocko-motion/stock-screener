"""
Column Entity

Base class for all column types in FINS.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Type, ClassVar
import inspect
import importlib
import pkgutil
from pathlib import Path


class Column(ABC):
    """Base class for all column types."""

    # Class-level registry of all column types
    _registry: ClassVar[Dict[str, Type['Column']]] = {}

    @classmethod
    def register(cls, column_class: Type['Column']) -> None:
        """Register a column type."""
        name = str(column_class())  # Use the __str__ representation as key
        cls._registry[name] = column_class

    @classmethod
    def get(cls, name: str) -> Type['Column']:
        """Get a column type by name."""
        if name not in cls._registry:
            raise ValueError(f"Unknown column type: {name}")
        return cls._registry[name]

    @classmethod
    def list(cls) -> list[Type['Column']]:
        """Get all available column types, sorted by name."""
        return sorted(cls._registry.values(), key=lambda c: str(c()))

    @classmethod
    def scan(cls) -> None:
        """
        Scan the columns directory for Column subclasses and register them.
        This is called automatically when the module is imported.
        """
        # Get the directory containing column implementations
        columns_dir = Path(__file__).parent / 'columns'
        
        # Calculate the package prefix from the current file's location
        package_parts = Path(__file__).relative_to(Path(__file__).parents[2]).with_suffix('').parts[:-1]
        package_prefix = '.'.join(package_parts)
        
        # Import all modules in the columns directory
        for module_info in pkgutil.iter_modules([str(columns_dir)]):
            if not module_info.name.startswith('_'):  # Skip __init__ etc
                # Use absolute import path
                module_path = f"{package_prefix}.columns.{module_info.name}"
                try:
                    module = importlib.import_module(module_path)
                    
                    # Find and register Column subclasses
                    for item_name in dir(module):
                        item = getattr(module, item_name)
                        if (isinstance(item, type) and 
                            issubclass(item, Column) and 
                            item != Column):
                            cls.register(item)
                except ImportError as e:
                    print(f"Warning: Failed to import {module_path}: {e}")

    @abstractmethod
    def value(self, ticker: str) -> Any:
        """
        Get the column value for a ticker.
        Must be implemented by each column type.
        
        The actual data fetching/symbol resolution happens in a deeper layer.
        """
        pass

    def __str__(self) -> str:
        """String representation of the column."""
        return self.__class__.__name__.lower().replace('column', '')

    @classmethod
    def help(cls) -> Dict[str, Any]:
        """
        Get column usage information through reflection.
        Returns dict with name, description, parameters and their types.
        """
        sig = inspect.signature(cls.__init__)
        doc = inspect.getdoc(cls)
        
        # Get parameter info from constructor
        params = {
            name: {
                'type': param.annotation,
                'default': param.default if param.default != param.empty else None,
                'required': param.default == param.empty
            }
            for name, param in sig.parameters.items()
            if name != 'self'
        }
        
        # Extract parameter docs from constructor docstring
        if cls.__init__.__doc__:
            param_docs = {}
            current_param = None
            for line in cls.__init__.__doc__.split('\n'):
                if ':param' in line:
                    current_param = line.split(':param')[1].split(':')[0].strip()
                    param_docs[current_param] = line.split(':', 2)[2].strip()
                elif current_param and line.strip():
                    param_docs[current_param] += ' ' + line.strip()
            
            # Add docs to params
            for name, param_doc in param_docs.items():
                if name in params:
                    params[name]['doc'] = param_doc

        return {
            'name': str(cls()),  # Use __str__ to get name
            'description': doc,
            'parameters': params
        }

    def __init__(self, alias: str = None, args: Dict[str, str] = None):
        """Initialize column with optional alias."""
        self._alias = alias

    def alias(self) -> str:
        """Get column name/alias."""
        return self._alias or str(self)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "class": self.__class__.__name__,
            "alias": self._alias
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Column':
        """Create from dictionary."""
        return cls(alias=data.get('alias'))


# Scan for column implementations when this module is imported
Column.scan() 