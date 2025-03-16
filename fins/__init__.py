"""
FINS - Financial Insights and Notation System

A powerful terminal-based tool for filtering, sorting, and analyzing financial baskets
through an intuitive command syntax.
"""

__version__ = "0.1.0"

# Import and expose key modules
from fins.data_sources import fmp
from fins.data_sources import watchdog
from fins.data_sources import cache

# Import and expose the DSL parser
from fins.dsl import FinsParser

# Import and expose the storage module
from fins.storage import Storage, EntityStore

__all__ = ['FinsParser', 'Storage', 'EntityStore']
