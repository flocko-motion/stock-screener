"""
Configuration module for the application.
"""

from pathlib import Path

# Directory paths
DIR_DATA = Path.home() / ".fins"
DIR_DB = DIR_DATA / "db"

# File paths
PATH_DB = DIR_DB / "symbols.db"

# Create required directories
for path in [DIR_DATA, DIR_DB]:
    path.mkdir(parents=True, exist_ok=True) 