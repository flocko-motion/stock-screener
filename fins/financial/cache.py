"""
Database caching and migration functionality
"""

# Re-export shared database functionality for backward compatibility
from fins.database import Base, session_scope, init_db

# Initialize the symbols database
init_db("symbols")


