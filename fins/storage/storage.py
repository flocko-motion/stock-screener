"""
Unified Storage System

This module provides a unified storage system for the FINS application,
handling both in-memory and persistent storage based on path format.

Path formats:
- $name: In-memory variable
- /name: Persistent variable in the default location (~/.fins/variables)
- /path/to/name: Persistent variable in a specific location
"""

import os
import json
import tempfile
from typing import Dict, Any, Optional, List, Protocol, runtime_checkable
from pathlib import Path
from abc import ABC, abstractmethod


class StorageValue:
    """
    Represents a value stored in the storage system.
    
    Attributes:
        path (str): The path where the value is stored
        value (Any): The actual value
        is_locked (bool): Whether the value is locked (cannot be modified)
        metadata (Dict[str, Any]): Additional metadata for the value
    """
    
    def __init__(self, 
                 path: str, 
                 value: Any = None, 
                 is_locked: bool = False, 
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a storage value.
        
        Args:
            path: The path where the value is stored
            value: The actual value (default: None)
            is_locked: Whether the value is locked (default: False)
            metadata: Additional metadata (default: {})
        """
        self.path = path
        self.value = value
        self.is_locked = is_locked
        self.metadata = metadata or {}
    
    def __str__(self) -> str:
        """Return the string representation of the storage value."""
        lock_indicator = " [LOCKED]" if self.is_locked else ""
        return f"{self.path}{lock_indicator}"
    
    def lock(self) -> None:
        """Lock the value to prevent modification."""
        self.is_locked = True
    
    def unlock(self) -> None:
        """Unlock the value to allow modification."""
        self.is_locked = False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the storage value to a dictionary.
        
        Returns:
            A dictionary representation of the storage value
        """
        result = {
            'path': self.path,
            'is_locked': self.is_locked
        }
        
        # Handle different types of values
        if hasattr(self.value, 'to_dict'):
            result['value'] = self.value.to_dict()
            result['value_type'] = self.value.__class__.__name__
        else:
            result['value'] = self.value
            result['value_type'] = type(self.value).__name__
            
        if self.metadata:
            result['metadata'] = self.metadata
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StorageValue':
        """
        Create a storage value from a dictionary.
        
        Args:
            data: The dictionary containing storage value data
            
        Returns:
            A new StorageValue instance
        """
        from fins.entities import entity_from_dict
        return cls(
            path=data.get('path', ''),
            value=entity_from_dict(data.get('value')),
            is_locked=data.get('is_locked', False),
            metadata=data.get('metadata', {})
        )


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def get(self, path: str) -> Optional[StorageValue]:
        """
        Get a value by path.
        
        Args:
            path: The path to retrieve
            
        Returns:
            The value if found, None otherwise
        """
        pass
    
    @abstractmethod
    def set(self, path: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Set a value at the specified path.
        
        Args:
            path: The path to set
            value: The value to store
            metadata: Optional metadata
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, path: str) -> bool:
        """
        Delete a value at the specified path.
        
        Args:
            path: The path to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def list(self, prefix: str = "") -> List[str]:
        """
        List all paths with the specified prefix.
        
        Args:
            prefix: The prefix to filter by
            
        Returns:
            A list of paths
        """
        pass


class MemoryStorage(StorageBackend):
    """In-memory storage backend."""
    
    def __init__(self):
        """Initialize an empty in-memory storage."""
        self.values: Dict[str, StorageValue] = {}
    
    def get(self, path: str) -> Optional[StorageValue]:
        """
        Get a value by path.
        
        Args:
            path: The path to retrieve
            
        Returns:
            The value if found, None otherwise
        """
        return self.values.get(path)
    
    def set(self, path: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Set a value at the specified path.
        
        Args:
            path: The path to set
            value: The value to store
            metadata: Optional metadata
            
        Returns:
            True if successful, False otherwise
        """
        # Check if the value exists and is locked
        if path in self.values and self.values[path].is_locked:
            return False
        
        # Create or update the value
        if path in self.values:
            self.values[path].value = value
            if metadata:
                self.values[path].metadata.update(metadata)
        else:
            self.values[path] = StorageValue(path, value, metadata=metadata)
        
        return True
    
    def delete(self, path: str) -> bool:
        """
        Delete a value at the specified path.
        
        Args:
            path: The path to delete
            
        Returns:
            True if successful, False otherwise
        """
        if path in self.values:
            del self.values[path]
            return True
        return False
    
    def list(self, prefix: str = "") -> List[str]:
        """
        List all paths with the specified prefix.
        
        Args:
            prefix: The prefix to filter by
            
        Returns:
            A list of paths
        """
        return [path for path in self.values.keys() if path.startswith(prefix)]


class DiskStorage(StorageBackend):
    """Disk-based storage backend."""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize the disk storage.
        
        Args:
            base_dir: The base directory for storage (defaults to ~/.fins/variables)
        """
        if base_dir is None:
            home_dir = str(Path.home())
            base_dir = os.path.join(home_dir, ".fins", "variables")
        
        self.base_dir = base_dir
        
        # Create the base directory if it doesn't exist
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Cache of loaded values
        self.cache: Dict[str, StorageValue] = {}
    
    def _path_to_file_path(self, path: str) -> str:
        """
        Convert a storage path to a file path.
        
        Args:
            path: The storage path
            
        Returns:
            The file path
        """
        # Remove the leading slash
        if path.startswith('/'):
            path = path[1:]
        
        # Handle absolute paths
        if '/' in path:
            # Create directories as needed
            dir_path = os.path.join(self.base_dir, os.path.dirname(path))
            os.makedirs(dir_path, exist_ok=True)
        
        return os.path.join(self.base_dir, f"{path}.json")
    
    def get(self, path: str) -> Optional[StorageValue]:
        """
        Get a value by path.
        
        Args:
            path: The path to retrieve
            
        Returns:
            The value if found, None otherwise
        """
        # Check the cache first
        if path in self.cache:
            return self.cache[path]
        
        # Try to load from disk
        file_path = self._path_to_file_path(path)
        
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            value = StorageValue.from_dict(data)

            # Update the cache
            self.cache[path] = value
            
            return value
        except Exception as e:
            print(f"Error loading value from {file_path}: {e}")
            return None
    
    def set(self, path: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Set a value at the specified path.
        
        Args:
            path: The path to set
            value: The value to store
            metadata: Optional metadata
            
        Returns:
            True if successful, False otherwise
        """
        # Check if the value exists and is locked
        existing = self.get(path)
        if existing and existing.is_locked:
            return False
        
        # Create the storage value
        storage_value = StorageValue(path, value, metadata=metadata)
        
        # Update the cache
        self.cache[path] = storage_value
        
        # Save to disk
        file_path = self._path_to_file_path(path)
        
        try:
            with open(file_path, 'w') as f:
                json.dump(storage_value.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving value to {file_path}: {e}")
            return False
    
    def delete(self, path: str) -> bool:
        """
        Delete a value at the specified path.
        
        Args:
            path: The path to delete
            
        Returns:
            True if successful, False otherwise
        """
        # Remove from cache
        if path in self.cache:
            del self.cache[path]
        
        # Remove from disk
        file_path = self._path_to_file_path(path)
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except Exception as e:
                print(f"Error deleting value at {file_path}: {e}")
                return False
        
        return True  # If it doesn't exist, consider it a success
    
    def list(self, prefix: str = "") -> List[str]:
        """
        List all paths with the specified prefix.
        
        Args:
            prefix: The prefix to filter by
            
        Returns:
            A list of paths
        """
        result = []
        
        # Remove the leading slash from the prefix for file matching
        file_prefix = prefix[1:] if prefix.startswith('/') else prefix
        
        for root, _, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith('.json'):
                    # Get the relative path from the base directory
                    rel_path = os.path.relpath(os.path.join(root, file), self.base_dir)
                    
                    # Remove the .json extension
                    path = '/' + rel_path[:-5]
                    
                    # Check if it matches the prefix
                    if path.startswith(prefix):
                        result.append(path)
        
        return result


class Storage:
    """
    Unified storage system that routes requests based on path format.
    
    Path formats:
    - $name: In-memory variable
    - /name: Persistent variable in the default location
    - /path/to/name: Persistent variable in a specific location
    """
    
    def __init__(self, disk_base_dir: Optional[str] = None):
        """
        Initialize the storage system.
        
        Args:
            disk_base_dir: The base directory for disk storage
        """
        self.memory_storage = MemoryStorage()
        self.disk_storage = DiskStorage(disk_base_dir)
    
    def _get_backend(self, path: str) -> StorageBackend:
        """
        Get the appropriate backend for the given path.
        
        Args:
            path: The path to route
            
        Returns:
            The appropriate storage backend
        """
        if path.startswith('$'):
            return self.memory_storage
        elif path.startswith('/'):
            return self.disk_storage
        else:
            raise ValueError(f"Invalid path format: {path}. Path must start with $ or /")
    
    def get(self, path: str) -> Any:
        """
        Get a value by path.
        
        Args:
            path: The path to retrieve
            
        Returns:
            The value if found, None otherwise
        """
        backend = self._get_backend(path)
        storage_value = backend.get(path)
        return storage_value.value if storage_value else None
    
    def get_storage_value(self, path: str) -> Optional[StorageValue]:
        """
        Get the storage value object by path.
        
        Args:
            path: The path to retrieve
            
        Returns:
            The storage value if found, None otherwise
        """
        backend = self._get_backend(path)
        return backend.get(path)
    
    def set(self, path: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Set a value at the specified path.
        
        Args:
            path: The path to set
            value: The value to store
            metadata: Optional metadata
            
        Returns:
            True if successful, False otherwise
        """
        backend = self._get_backend(path)
        return backend.set(path, value, metadata)
    
    def delete(self, path: str) -> bool:
        """
        Delete a value at the specified path.
        
        Args:
            path: The path to delete
            
        Returns:
            True if successful, False otherwise
        """
        backend = self._get_backend(path)
        return backend.delete(path)
    
    def list(self, prefix: str = "") -> List[str]:
        """
        List all paths with the specified prefix.
        
        Args:
            prefix: The prefix to filter by
            
        Returns:
            A list of paths
        """
        if not prefix:
            # List both memory and disk paths
            return self.memory_storage.list() + self.disk_storage.list()
        
        if prefix.startswith('$'):
            return self.memory_storage.list(prefix)
        elif prefix.startswith('/'):
            return self.disk_storage.list(prefix)
        else:
            raise ValueError(f"Invalid prefix format: {prefix}. Prefix must start with $ or /")
    
    def lock(self, path: str) -> bool:
        """
        Lock a value at the specified path.
        
        Args:
            path: The path to lock
            
        Returns:
            True if successful, False otherwise
        """
        storage_value = self.get_storage_value(path)
        if storage_value:
            storage_value.lock()
            
            # For persistent storage, we need to save the updated value
            if path.startswith('/'):
                return self.disk_storage.set(path, storage_value.value, storage_value.metadata)
            
            return True
        
        return False
    
    def unlock(self, path: str) -> bool:
        """
        Unlock a value at the specified path.
        
        Args:
            path: The path to unlock
            
        Returns:
            True if successful, False otherwise
        """
        storage_value = self.get_storage_value(path)
        if storage_value:
            storage_value.unlock()
            
            # For persistent storage, we need to save the updated value
            if path.startswith('/'):
                return self.disk_storage.set(path, storage_value.value, storage_value.metadata)
            
            return True
        
        return False
    
    def is_locked(self, path: str) -> bool:
        """
        Check if a value is locked.
        
        Args:
            path: The path to check
            
        Returns:
            True if the value is locked, False otherwise
        """
        storage_value = self.get_storage_value(path)
        return storage_value.is_locked if storage_value else False

    @classmethod
    def temp(cls):
        """Create a new storage instance with a temporary directory."""
        temp_dir = tempfile.mkdtemp()
        return cls(temp_dir)