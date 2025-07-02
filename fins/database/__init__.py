"""
Shared database setup for FINS.

This module provides the common SQLAlchemy setup used by both financial and notebook modules.
"""

from datetime import datetime, timedelta
from contextlib import contextmanager
from sqlalchemy import create_engine, event, Column, String, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import StaticPool, QueuePool

from fins.config import DIR_DB

# Create declarative base
Base = declarative_base()

# Database engines and session factories
_engines = {}
_sessions = {}


def init_db(db_name: str = "symbols"):
    """Initialize a database connection and ensure schema is up to date."""
    if db_name not in _engines:
        db_path = DIR_DB / f"{db_name}.db"
        
        _engines[db_name] = create_engine(
            f'sqlite:///{db_path}',
            connect_args={
                'check_same_thread': False,
                'timeout': 30,  # Wait up to 30 seconds for locks
            },
            poolclass=QueuePool,
            pool_size=10,  # Allow up to 10 concurrent connections
            max_overflow=20,  # Allow 20 additional connections if needed
            pool_pre_ping=True  # Verify connections before use
        )
        
        # Configure SQLite for maximum durability
        @event.listens_for(_engines[db_name], "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=DELETE")  # Traditional rollback journal
            cursor.execute("PRAGMA synchronous=FULL")     # Maximum durability
            cursor.execute("PRAGMA busy_timeout=30000")   # 30 second timeout
            cursor.close()
        
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


__all__ = ['Base', 'session_scope', 'init_db'] 