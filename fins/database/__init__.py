"""
PostgreSQL database setup for FINS.

This module provides the PostgreSQL SQLAlchemy setup used by both financial and notebook modules.
"""

import os
from datetime import datetime
from contextlib import contextmanager
from sqlalchemy import create_engine, event, Column, String, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import QueuePool
from pathlib import Path

from fins.config import DIR_DB

# Create declarative base
Base = declarative_base()

# Database engines and session factories
_engines = {}
_sessions = {}

# Database configuration
def load_db_config():
    """Load database configuration from ~/.fins/config/db.env"""
    config_path = Path.home() / '.fins' / 'config' / 'db.env'
    
    if not config_path.exists():
        raise FileNotFoundError(f"Database config file not found: {config_path}")
    
    password = None
    with open(config_path, 'r') as f:
        for line in f:
            if line.startswith('POSTGRES_PASSWORD='):
                password = line.split('=', 1)[1].strip()
                break
    
    if not password:
        raise ValueError(f"No POSTGRES_PASSWORD found in {config_path}")
    
    return {
        'host': 'localhost',
        'port': 5432,
        'database': 'fins',
        'user': 'fins',
        'password': password
    }

def get_connection_string(db_name: str = "symbols") -> str:
    """Get PostgreSQL connection string."""
    config = load_db_config()
    return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"

def init_db(db_name: str = "symbols"):
    """Initialize a PostgreSQL database connection and ensure schema is up to date."""
    if db_name not in _engines:
        connection_string = get_connection_string(db_name)
        
        _engines[db_name] = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=5,  # Optimized for single user
            max_overflow=10,  # Reduced for single user
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
        
        _sessions[db_name] = scoped_session(sessionmaker(bind=_engines[db_name]))
        
        # Create all tables for this database
        Base.metadata.create_all(_engines[db_name])

@contextmanager
def session_scope(db_name: str = "symbols"):
    """Provide a transactional scope around a series of operations."""
    if db_name not in _sessions:
        init_db(db_name)
    
    session = _sessions[db_name]()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def get_db_info() -> dict:
    """Get information about the current database configuration."""
    try:
        config = load_db_config()
        return {
            'backend': 'postgresql',
            'connection_string': get_connection_string('symbols').replace(config['password'], '***'),
            'engines_initialized': list(_engines.keys())
        }
    except Exception as e:
        return {
            'backend': 'postgresql',
            'error': str(e),
            'engines_initialized': list(_engines.keys())
        }

__all__ = ['Base', 'session_scope', 'init_db', 'get_db_info'] 