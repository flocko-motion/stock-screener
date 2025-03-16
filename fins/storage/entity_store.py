"""
Entity Store

This module defines the EntityStore class, which provides file system-based
storage and retrieval for entities using JSONL format.
"""

import os
import json
from typing import Dict, List, Type, TypeVar, Optional, Iterator, Any
from datetime import datetime
import logging
from pathlib import Path
import sys

# Add the parent directory to the path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fins.entities.entity import Entity
from .storage import Storage, StorageValue

# Type variable for generic entity types
T = TypeVar('T', bound=Entity)

class EntityStore:
    """
    Provides file system-based storage and retrieval for entities using JSONL format.
    
    This class handles:
    - Saving entities to JSONL files
    - Loading entities from JSONL files
    - Querying entities by ID, tags, and other criteria
    - Managing entity collections
    
    Attributes:
        storage (Storage): The unified storage system
        entity_class (Type[Entity]): The entity class this store manages
        entities (Dict[str, Entity]): In-memory cache of loaded entities
        storage_path (str): Path in the storage system for this entity type
    """
    
    def __init__(self, entity_class: Type[T], storage: Optional[Storage] = None):
        """
        Initialize an entity store.
        
        Args:
            entity_class: The entity class this store will manage
            storage: The storage system to use (creates a new one if None)
        """
        self.entity_class = entity_class
        
        # Set up storage
        self.storage = storage or Storage()
        
        # Set up storage path for this entity type
        self.storage_path = f"/entities/{entity_class.storage_dir}/{entity_class.entity_type}s"
        
        # Initialize in-memory cache
        self.entities: Dict[str, T] = {}
        
        # Load existing entities
        self._load_entities()
    
    def _load_entities(self) -> None:
        """Load all entities from storage into memory."""
        # Get the JSONL data from storage
        jsonl_data = self.storage.get(self.storage_path)
        
        if not jsonl_data:
            # Create an empty JSONL file in storage
            self.storage.set(self.storage_path, "")
            return
        
        # Parse each line as a JSON object
        for line in jsonl_data.splitlines():
            line = line.strip()
            if not line:
                continue
            
            try:
                entity = self.entity_class.from_json(line)
                self.entities[entity.id] = entity
            except Exception as e:
                logging.error(f"Error loading entity: {e}")
    
    def save(self, entity: T) -> bool:
        """
        Save an entity to the store.
        
        This will:
        1. Update the entity's updated_at timestamp
        2. Add it to the in-memory cache
        3. Update the JSONL data in storage
        
        Args:
            entity: The entity to save
            
        Returns:
            True if the entity was saved successfully, False otherwise
        """
        try:
            # Update the timestamp
            entity.update()
            
            # Check if this is a new entity or an update
            is_new = entity.id not in self.entities
            
            # Add to in-memory cache
            self.entities[entity.id] = entity
            
            # Update the JSONL data in storage
            if is_new:
                # Append to the JSONL data
                jsonl_data = self.storage.get(self.storage_path) or ""
                jsonl_data += entity.to_json() + '\n'
                self.storage.set(self.storage_path, jsonl_data)
            else:
                # Rewrite the entire JSONL data
                self._rewrite_jsonl_data()
            
            return True
        except Exception as e:
            logging.error(f"Error saving entity {entity.id}: {e}")
            return False
    
    def _rewrite_jsonl_data(self) -> None:
        """Rewrite the entire JSONL data with the current in-memory entities."""
        try:
            jsonl_data = ""
            for entity in self.entities.values():
                jsonl_data += entity.to_json() + '\n'
            
            self.storage.set(self.storage_path, jsonl_data)
        except Exception as e:
            logging.error(f"Error rewriting JSONL data for {self.storage_path}: {e}")
    
    def get(self, entity_id: str) -> Optional[T]:
        """
        Get an entity by ID.
        
        Args:
            entity_id: The ID of the entity to get
            
        Returns:
            The entity if found, None otherwise
        """
        return self.entities.get(entity_id)
    
    def delete(self, entity_id: str) -> bool:
        """
        Delete an entity by ID.
        
        Args:
            entity_id: The ID of the entity to delete
            
        Returns:
            True if the entity was deleted, False if it wasn't found
        """
        if entity_id in self.entities:
            del self.entities[entity_id]
            self._rewrite_jsonl_data()
            return True
        return False
    
    def find_by_tag(self, tag: str) -> List[T]:
        """
        Find entities with a specific tag.
        
        Args:
            tag: The tag to search for
            
        Returns:
            A list of entities with the specified tag
        """
        return [entity for entity in self.entities.values() if tag in entity.tags]
    
    def find_by_created_after(self, date: datetime) -> List[T]:
        """
        Find entities created after a specific date.
        
        Args:
            date: The date to compare against
            
        Returns:
            A list of entities created after the specified date
        """
        return [entity for entity in self.entities.values() if entity.created_at > date]
    
    def find_by_updated_after(self, date: datetime) -> List[T]:
        """
        Find entities updated after a specific date.
        
        Args:
            date: The date to compare against
            
        Returns:
            A list of entities updated after the specified date
        """
        return [entity for entity in self.entities.values() if entity.updated_at > date]
    
    def find_by_metadata(self, key: str, value: Any) -> List[T]:
        """
        Find entities with a specific metadata key-value pair.
        
        Args:
            key: The metadata key to search for
            value: The metadata value to match
            
        Returns:
            A list of entities with the specified metadata
        """
        return [
            entity for entity in self.entities.values() 
            if key in entity.metadata and entity.metadata[key] == value
        ]
    
    def all(self) -> List[T]:
        """
        Get all entities in the store.
        
        Returns:
            A list of all entities
        """
        return list(self.entities.values())
    
    def count(self) -> int:
        """
        Get the number of entities in the store.
        
        Returns:
            The number of entities
        """
        return len(self.entities)
    
    def clear(self) -> None:
        """Clear all entities from memory and storage."""
        self.entities.clear()
        self.storage.set(self.storage_path, "")
    
    def __iter__(self) -> Iterator[T]:
        """Return an iterator over all entities."""
        return iter(self.entities.values())
    
    def __len__(self) -> int:
        """Return the number of entities."""
        return len(self.entities)
    
    def __contains__(self, entity_id: str) -> bool:
        """Check if an entity with the given ID exists."""
        return entity_id in self.entities 