"""
JSON Serializable Entity

This module defines the JsonSerializable abstract base class, which provides a common interface
for entities that can be serialized to JSON.
"""

from abc import ABC, abstractmethod


class JsonSerializable(ABC):
    """
    Abstract base class for entities that can be serialized to JSON.
    
    All entities that need to be serialized to JSON should inherit from this class
    and implement the to_dict method.
    """
    
    @abstractmethod
    def to_dict(self):
        """
        Convert the entity to a dictionary that can be serialized to JSON.
        
        Returns:
            A dictionary representation of the entity
        """
        pass 