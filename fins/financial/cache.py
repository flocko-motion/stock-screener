"""
Database cache management.
"""

from datetime import datetime, timedelta
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from fins.config import PATH_DB

# Database engine and session factory
_engine = None
_Session = None

def get_expiration_time() -> datetime:
    """Get the expiration time for cached data (noon on first day of next month)."""
    now = datetime.now()
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime(now.year, now.month + 1, 1)
    return next_month + timedelta(hours=12)

def init_db():
    """Initialize the database connection."""
    global _engine, _Session
    if _engine is None:
        _engine = create_engine(
            f'sqlite:///{PATH_DB}',
            connect_args={
                'check_same_thread': False,
                'timeout': 30,  # Wait up to 30 seconds for locks
            },
            poolclass=StaticPool
        )
        
        # Configure SQLite for maximum durability
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=DELETE")  # Traditional rollback journal
            cursor.execute("PRAGMA synchronous=FULL")     # Maximum durability
            cursor.execute("PRAGMA busy_timeout=30000")   # 30 second timeout
            cursor.close()
        
        _Session = sessionmaker(bind=_engine)

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