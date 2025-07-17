#!/usr/bin/env python3
"""
Test script to verify shutdown mechanism works properly.
"""

import time
import threading
import signal
import sys

# Import the centralized shutdown functions
from fins.shutdown import set_shutdown_event, is_shutdown_requested


def test_worker():
    """Test worker that runs until shutdown is requested."""
    print("🔄 Worker thread started")
    counter = 0
    while not is_shutdown_requested():
        counter += 1
        print(f"  Worker iteration {counter}")
        time.sleep(1)
    print("🛑 Worker thread stopped")


def test_shutdown():
    """Test the shutdown mechanism."""
    print("🧪 Testing shutdown mechanism...")
    
    # Start worker thread
    worker = threading.Thread(target=test_worker, daemon=True)
    worker.start()
    
    # Let it run for a few seconds
    time.sleep(3)
    
    print("🛑 Triggering shutdown...")
    set_shutdown_event()
    
    # Wait for worker to stop
    worker.join(timeout=2)
    
    if worker.is_alive():
        print("❌ Worker thread did not stop properly")
        return False
    else:
        print("✅ Worker thread stopped properly")
        return True


if __name__ == "__main__":
    success = test_shutdown()
    sys.exit(0 if success else 1) 