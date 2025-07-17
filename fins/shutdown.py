"""
Global shutdown mechanism for FINS application.

This module provides a centralized way to signal shutdown across all threads
and components of the application.
"""

import threading
import time
import signal
import sys
import atexit
from typing import Callable, List

# Global shutdown event
_shutdown_event = threading.Event()
_cleanup_handlers: List[Callable] = []

def set_shutdown_event():
    """Set the global shutdown event to signal all threads to stop."""
    _shutdown_event.set()

def is_shutdown_requested():
    """Check if shutdown has been requested."""
    return _shutdown_event.is_set()

def register_cleanup_handler(handler: Callable):
    """Register a cleanup function to be called during shutdown."""
    _cleanup_handlers.append(handler)

def unregister_cleanup_handler(handler: Callable):
    """Unregister a cleanup function."""
    if handler in _cleanup_handlers:
        _cleanup_handlers.remove(handler)

def _perform_cleanup():
    """Execute all registered cleanup handlers."""
    print("🧹 Performing cleanup...")
    for handler in _cleanup_handlers:
        try:
            handler()
        except Exception as e:
            print(f"⚠️  Cleanup handler failed: {e}")

def shutdown_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\n🛑 Shutdown requested (signal {signum})...")
    
    # Set shutdown event
    set_shutdown_event()
    
    # Perform cleanup
    _perform_cleanup()
    
    # Give threads a moment to clean up
    time.sleep(0.5)
    print("✅ Shutdown complete")
    sys.exit(0)

def setup_shutdown_handlers():
    """Setup signal handlers for graceful shutdown."""
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    atexit.register(_perform_cleanup)

def wait_for_shutdown(timeout: float = None):
    """Wait for shutdown to be requested, with optional timeout."""
    if timeout is None:
        while not is_shutdown_requested():
            time.sleep(0.5)
    else:
        start_time = time.time()
        while not is_shutdown_requested() and (time.time() - start_time) < timeout:
            time.sleep(0.5)

# Auto-setup shutdown handlers when module is imported
setup_shutdown_handlers() 