"""
Entity Persistence Functions for Terminal

This module provides persistence functions for entities in the terminal environment.
Functions handle any Entity type and automatically add appropriate file extensions.

Functions:
- Get(path): Load an entity from persistence
- Put(entity, path): Save an entity to persistence  
- Dir(path): List entities/directories in persistence
- Delete(path, force=False): Delete entity or directory from persistence
"""

import os
import shutil
from pathlib import Path
from typing import Any, List, Optional, Union
from fins.storage import Storage
from fins.entities import Entity, entity_from_dict, BasketRuntime
from fins.config import DIR_DATA


# Default persistence directory
PERSISTENCE_DIR = DIR_DATA / "persistence"
PERSISTENCE_DIR.mkdir(parents=True, exist_ok=True)

# Global storage instance
_storage = Storage(str(PERSISTENCE_DIR))


def Get(path: str, silent: bool = False) -> Optional[Entity]:
    """
    Load an entity from persistence.
    
    Args:
        path: Relative path in persistence directory
        silent: If True, return result; if False, print status and return result
        
    Returns:
        The loaded entity or None if not found
        
    Examples:
        basket = Get("portfolios/tech_stocks")
        note = Get("research/apple_analysis")
        Get("portfolios/tech_stocks", silent=True)  # For testing
    """
    if not path.startswith('/'):
        path = '/' + path
    
    storage_value = _storage.get_storage_value(path)
    if storage_value and isinstance(storage_value.value, Entity):
        entity = storage_value.value
        if not silent:
            entity_type = entity.__class__.__name__
            print(f"Loaded {entity_type}: {path}")
        return entity
    else:
        if not silent:
            print(f"Entity not found: {path}")
        return None


def Put(entity: Entity, path: str, overwrite: bool = False, silent: bool = False) -> bool | None:
    """
    Save an entity to persistence with automatic file extension.
    
    Args:
        entity: The entity to save
        path: Relative path in persistence directory (extension added automatically)
        overwrite: If True, allow overwriting existing entities; if False, prevent overwrite
        silent: If True, return result only; if False, print status and return result
        
    Returns:
        True if successful, False otherwise
        
    Examples:
        Put(my_basket, "portfolios/tech_stocks")  # Saves as tech_stocks.Basket
        Put(my_note, "research/apple_analysis")   # Saves as apple_analysis.Note
        Put(my_basket, "portfolios/tech_stocks", overwrite=True)  # Force overwrite
        Put(my_basket, "test/basket", silent=True)  # For testing
    """
    if isinstance(entity, BasketRuntime):
        entity = entity.basket()

    if not isinstance(entity, Entity):
        raise TypeError(f"Expected Entity, got {type(entity)}")
    
    # Add entity class name as extension
    class_name = entity.__class__.__name__
    if not path.endswith(f'.{class_name}'):
        path = f"{path}.{class_name}"
    
    if not path.startswith('/'):
        path = '/' + path
    
    # Check if entity already exists
    existing = _storage.get_storage_value(path)
    if existing and not overwrite:
        error_msg = f"Entity already exists at '{path}'. Use overwrite=True to replace it."
        if not silent:
            print(f"Warning: {error_msg}")
        return False
    
    success = _storage.set(path, entity)
    if silent:
        return success
    if success:
        action = "Overwritten" if existing else "Saved"
        print(f"{action} {class_name}: {path}")
    else:
        print(f"Failed to save {class_name}: {path}")
    return None


def Dir(path: str = "/", recursive: bool = False, silent: bool = False) -> Optional[List[str]]:
    """
    List entities and directories in persistence.
    
    Args:
        path: Path to list (default: root)
        recursive: If True, list all files recursively (default: False)
        silent: If True, return result; if False, print listing and return result
        
    Returns:
        List of paths in the directory (only when silent=True)
        
    Examples:
        Dir()                        # List root directory
        Dir("portfolios")            # List portfolios directory
        Dir(recursive=True)          # List all files recursively
        Dir("portfolios", recursive=True)  # List portfolios recursively
        Dir("portfolios", silent=True)     # For testing
    """
    if not path.startswith('/'):
        path = '/' + path
    
    # Ensure path ends with / for directory listing
    if not path.endswith('/'):
        path = path + '/'
    
    all_paths = _storage.list(path)
    
    if recursive:
        # Return all paths relative to the requested path
        result = []
        path_len = len(path)
        
        for full_path in all_paths:
            if full_path.startswith(path) and len(full_path) > path_len:
                relative = full_path[path_len:]
                result.append(relative)
        
        result = sorted(result)
    else:
        # Extract just the names relative to the requested path (non-recursive)
        result = set()
        path_len = len(path)
        
        for full_path in all_paths:
            if full_path.startswith(path) and len(full_path) > path_len:
                relative = full_path[path_len:]
                # Get just the first component (file or directory name)
                if '/' in relative:
                    dir_name = relative.split('/')[0]
                    result.add(dir_name + '/')
                else:
                    result.add(relative)
        
        result = sorted(result)
    
    if not silent:
        display_path = path.rstrip('/') or '/'
        recursive_str = " (recursive)" if recursive else ""
        print(f"Contents of {display_path}{recursive_str}:")
        if result:
            for item in result:
                print(f"  {item}")
        else:
            print("  (empty)")
        return None
    else:
        return result


def Delete(path: str, force: bool = False, silent: bool = False) -> bool:
    """
    Delete entity or directory from persistence.
    
    Args:
        path: Path to delete
        force: Required to delete directories with contents
        silent: If True, return result only; if False, print status and return result
        
    Returns:
        True if successful, False otherwise
        
    Examples:
        Delete("portfolios/old_basket.Basket")     # Delete single entity
        Delete("temp", force=True)                 # Delete directory with contents
        Delete("test/entity", silent=True)         # For testing
    """
    if not path.startswith('/'):
        path = '/' + path
    
    # Check if it's a directory by looking for items with this path as prefix
    dir_path = path if path.endswith('/') else path + '/'
    items_in_dir = _storage.list(dir_path)
    
    if items_in_dir:
        # It's a directory with contents
        if not force:
            error_msg = f"Directory '{path}' contains items. Use force=True to delete recursively."
            if not silent:
                print(f"Error: {error_msg}")
            raise ValueError(error_msg)
        
        # Delete all items in directory
        deleted_count = 0
        for item_path in items_in_dir:
            if _storage.delete(item_path):
                deleted_count += 1
        
        if not silent:
            print(f"Deleted directory '{path}' and {deleted_count} items")
        return True
    else:
        # It's a single entity
        success = _storage.delete(path)
        if not silent:
            if success:
                print(f"Deleted: {path}")
            else:
                print(f"Failed to delete (not found): {path}")
        return success


def _get_entity_info(path: str) -> tuple[str, int]:
    """
    Get information about an entity file.
    
    Args:
        path: Path to the entity
        
    Returns:
        Tuple of (entity_type, item_count)
    """
    try:
        return _storage.info(path)
    except Exception:
        return ("Unknown", 0) 