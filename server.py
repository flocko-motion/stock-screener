#!/usr/bin/env python
"""
FINS Server - Server entry point for the Financial Insights and Notation System.
"""

import sys
import time
from pathlib import Path

# Add the parent directory to the path to allow imports from the fins package
sys.path.insert(0, str(Path(__file__).parent))

from fins.server import start_jupyter_server, start_api_server, start_websocket_server

from fins.shutdown import setup_shutdown_handlers, register_cleanup_handler


def main():
    """Start all FINS servers."""
    # Setup shutdown handlers
    setup_shutdown_handlers()

    # Register database cleanup
    try:
        from fins.database import shutdown_db
        register_cleanup_handler(shutdown_db)
    except ImportError:
        pass

    print("🚀 Starting FINS servers...")
    
    # Start all servers
    # start_jupyter_server()
    start_api_server()
    start_websocket_server()

    print("\nPress Ctrl+C to stop")

    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        return 0


if __name__ == "__main__":
    sys.exit(main()) 