"""
Configuration module for the application.
"""

from pathlib import Path

# Directory paths
DIR_DATA = Path.home() / ".fins"
DIR_DB = DIR_DATA / "db"
DIR_CONFIG = DIR_DATA / "config"
DIR_PERSISTENCE = DIR_DATA / "persistence"

# File paths
PATH_DB = DIR_DB / "symbols.db"
PATH_ASSISTANT_CONFIG = DIR_CONFIG / "assistant.yaml"

# Create required directories
for path in [DIR_DATA, DIR_DB, DIR_CONFIG, DIR_PERSISTENCE]:
    path.mkdir(parents=True, exist_ok=True) 