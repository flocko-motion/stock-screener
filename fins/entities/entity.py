"""
Entity Base Class

This module defines the Entity base class, which provides common functionality
for all entities in the FINS system, with a focus on persistence and metadata.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, ClassVar, Type

from .json_serializable import JsonSerializable


class Entity(JsonSerializable):
    """
    Base class for all entities in the FINS system.
    
    This class provides common functionality for entity persistence, including:
    - Unique ID generation
    - Creation and update timestamps
    - Tagging
    - JSON serialization and deserialization
    - File-based persistence
    
    Attributes:
        id (str): Unique identifier for the entity
        created_at (datetime): When the entity was created
        updated_at (datetime): When the entity was last updated
        tags (List[str]): List of tags associated with the entity
        metadata (Dict[str, Any]): Additional metadata for the entity
    """
    
    # Class variables to be overridden by subclasses
    entity_type: ClassVar[str] = "entity"
    storage_dir: ClassVar[str] = "entities"
    
    def __init__(self, 
                 id: Optional[str] = None, 
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 tags: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize an entity.
        
        Args:
            id: Unique identifier (generated if not provided)
            created_at: Creation timestamp (current time if not provided)
            updated_at: Update timestamp (same as created_at if not provided)
            tags: List of tags (empty list if not provided)
            metadata: Additional metadata (empty dict if not provided)
        """
        self.id = id or f"{self.entity_type}-{uuid.uuid4()}"
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or self.created_at
        self.tags = tags or []
        self.metadata = metadata or {}
    
    def update(self) -> None:
        """Update the entity's updated_at timestamp to the current time."""
        self.updated_at = datetime.now()
    
    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the entity if it doesn't already exist.
        
        Args:
            tag: The tag to add
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.update()
    
    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the entity if it exists.
        
        Args:
            tag: The tag to remove
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.update()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the entity to a dictionary.
        
        Returns:
            A dictionary representation of the entity
        """
        return {
            "id": self.id,
            "type": self.entity_type,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """
        Convert the entity to a JSON string.
        
        Returns:
            A JSON string representation of the entity
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entity':
        """
        Create an entity from a dictionary.
        
        Args:
            data: The dictionary containing entity data
            
        Returns:
            A new Entity instance
        """
        # Parse timestamps
        created_at = datetime.fromisoformat(data.get('created_at')) if data.get('created_at') else None
        updated_at = datetime.fromisoformat(data.get('updated_at')) if data.get('updated_at') else None
        
        return cls(
            id=data.get('id'),
            created_at=created_at,
            updated_at=updated_at,
            tags=data.get('tags', []),
            metadata=data.get('metadata', {})
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Entity':
        """
        Create an entity from a JSON string.
        
        Args:
            json_str: The JSON string containing entity data
            
        Returns:
            A new Entity instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data) 