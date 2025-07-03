"""
Configuration module for the application.
"""

from pathlib import Path
from typing import Optional
import yaml

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


def get_openai_api_key() -> Optional[str]:
    """Get the OpenAI API key from assistant.yaml"""
    if not PATH_ASSISTANT_CONFIG.exists():
        return None
    
    try:
        with open(PATH_ASSISTANT_CONFIG, 'r') as f:
            config = yaml.safe_load(f) or {}
            return config.get('api_key')
    except Exception:
        return None


def get_assistant_id() -> Optional[str]:
    """Get the assistant ID from assistant.yaml"""
    if not PATH_ASSISTANT_CONFIG.exists():
        return None
    
    try:
        with open(PATH_ASSISTANT_CONFIG, 'r') as f:
            config = yaml.safe_load(f) or {}
            return config.get('assistant_id')
    except Exception:
        return None


def save_assistant_id(assistant_id: str) -> bool:
    """Save the assistant ID to assistant.yaml"""
    try:
        config = {}
        if PATH_ASSISTANT_CONFIG.exists():
            with open(PATH_ASSISTANT_CONFIG, 'r') as f:
                config = yaml.safe_load(f) or {}
        
        config['assistant_id'] = assistant_id
        
        with open(PATH_ASSISTANT_CONFIG, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        return True
    except Exception:
        return False 