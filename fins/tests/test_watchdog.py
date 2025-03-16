#!/usr/bin/env python
"""
Tests for the watchdog module.

This module contains unit tests for the watchdog module, testing the
timeout and retry functionality for long-running operations.
"""

import unittest
import sys
import time
import threading
from pathlib import Path
from unittest import mock

# Add the parent directory to the path to allow imports from the fins package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fins.data_sources import watchdog
from fins.data_sources.watchdog import WatchdogTimeoutError


class TestWatchdog(unittest.TestCase):
    """Test cases for the watchdog module."""

    def test_watchdog_successful_execution(self):
        """Test that a function completes successfully within the timeout."""
        # Define a test function that completes quickly
        @watchdog.watchdog(timeout=1, retries=0)
        def quick_function():
            return "success"
        
        # Call the function
        result = quick_function()
        
        # Verify the result
        self.assertEqual(result, "success")

    def test_watchdog_timeout(self):
        """Test that a function that exceeds the timeout raises an exception."""
        # Define a test function that takes longer than the timeout
        @watchdog.watchdog(timeout=0.1, retries=0)
        def slow_function():
            time.sleep(1)
            return "success"
        
        # Call the function and verify it raises a WatchdogTimeoutError
        with self.assertRaises(WatchdogTimeoutError):
            slow_function()

    def test_watchdog_retry_success(self):
        """Test that a function that fails initially but succeeds on retry works."""
        # Use a counter to track the number of attempts
        attempts = [0]
        
        @watchdog.watchdog(timeout=0.5, retries=2)
        def failing_then_succeeding_function():
            attempts[0] += 1
            if attempts[0] < 2:
                time.sleep(1)  # Exceed the timeout on the first attempt
            return "success"
        
        # Call the function
        result = failing_then_succeeding_function()
        
        # Verify the result and the number of attempts
        self.assertEqual(result, "success")
        self.assertEqual(attempts[0], 2)

    def test_watchdog_exception_propagation(self):
        """Test that exceptions raised by the function are propagated."""
        # Define a test function that raises an exception
        @watchdog.watchdog(timeout=1, retries=0)
        def exception_function():
            raise ValueError("Test exception")
        
        # Call the function and verify it raises the original exception
        with self.assertRaises(ValueError) as context:
            exception_function()
        
        self.assertEqual(str(context.exception), "Test exception")

    @mock.patch('fins.data_sources.watchdog.threading.Thread')
    def test_watchdog_thread_creation(self, mock_thread):
        """Test that the watchdog creates a thread to run the function."""
        # Mock the thread instance
        mock_thread_instance = mock.MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Make thread.is_alive() return False to simulate successful completion
        mock_thread_instance.is_alive.return_value = False
        
        # Define a test function
        @watchdog.watchdog(timeout=1, retries=0)
        def test_function():
            return "success"
        
        # Set up the mock to execute the target function when Thread is created
        def side_effect(**kwargs):
            # When Thread is instantiated, execute the target function
            if 'target' in kwargs:
                kwargs['target']()
            return mock_thread_instance
        
        # Configure the mock to call our side effect
        mock_thread.side_effect = side_effect
        
        # Call the function
        result = test_function()
        
        # Verify a thread was created and started
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        
        # Verify the function returned the expected result
        self.assertEqual(result, "success")


if __name__ == "__main__":
    unittest.main() 