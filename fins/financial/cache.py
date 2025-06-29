"""
Database caching and migration functionality
"""

from datetime import datetime, timedelta
from contextlib import contextmanager
from sqlalchemy import create_engine, event, Column, String, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import StaticPool, QueuePool

from fins.config import PATH_DB

# Create declarative base
Base = declarative_base()

# Database engine and session factory
_engine = None
_Session = None



def init_db():
    """Initialize the database connection and ensure schema is up to date."""
    global _engine, _Session
    if _engine is None:
        _engine = create_engine(
            f'sqlite:///{PATH_DB}',
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
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=DELETE")  # Traditional rollback journal
            cursor.execute("PRAGMA synchronous=FULL")     # Maximum durability
            cursor.execute("PRAGMA busy_timeout=30000")   # 30 second timeout
            cursor.close()
        
        _Session = scoped_session(sessionmaker(bind=_engine))
        
        Base.metadata.create_all(_engine)

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    if _Session is None:
        init_db()
    session = _Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
