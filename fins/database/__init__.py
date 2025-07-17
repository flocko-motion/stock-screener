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

# Create shared declarative base for all modules
Base = declarative_base()

# Database engine and session factory
_engine = None
_session_factory = None

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

def get_connection_string() -> str:
    """Get PostgreSQL connection string."""
    config = load_db_config()
    return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"

def init_db():
    """Initialize PostgreSQL database connection and ensure schema is up to date."""
    global _engine, _session_factory
    
    if _engine is None:
        connection_string = get_connection_string()
        
        _engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=5,  # Optimized for single user
            max_overflow=10,  # Reduced for single user
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
        
        _session_factory = scoped_session(sessionmaker(bind=_engine))
        
        # Import all models to ensure they are registered with Base.metadata
        from fins.financial.symbol import Symbol, WeeklyPrice, MonthlyPrice
        from fins.notebook.notebook import NoteModel
        
        # Create all tables for this database
        Base.metadata.create_all(_engine)

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    # Ensure database is initialized
    if _session_factory is None:
        init_db()
    
    session = _session_factory()
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
            'connection_string': get_connection_string().replace(config['password'], '***'),
            'initialized': _engine is not None
        }
    except Exception as e:
        return {
            'backend': 'postgresql',
            'error': str(e),
            'initialized': _engine is not None
        }

__all__ = ['session_scope', 'Base'] 