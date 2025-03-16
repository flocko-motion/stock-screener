#!/usr/bin/env python
"""
Tests for the cache module.

This module contains unit tests for the cache module, testing various
functions for caching and retrieving data.
"""

import unittest
import sys
import os
import time
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path to allow imports from the fins package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fins.data_sources import cache


class TestCache(unittest.TestCase):
    """Test cases for the cache module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a test directory for cache files
        self.test_dir = os.path.join(os.path.dirname(__file__), 'test_cache')
        os.makedirs(self.test_dir, exist_ok=True)
        # Store the original rootpath
        self.original_rootpath = cache.rootpath
        # Set the rootpath to the test directory
        cache.rootpath = self.test_dir

    def tearDown(self):
        """Tear down test fixtures."""
        # Restore the original rootpath
        cache.rootpath = self.original_rootpath
        # Clean up the test directory
        if os.path.exists(self.test_dir):
            for root, dirs, files in os.walk(self.test_dir, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir in dirs:
                    os.rmdir(os.path.join(root, dir))
            os.rmdir(self.test_dir)

    def test_get_cache_path(self):
        """Test the get_cache_path function."""
        # Call the function
        path = cache.get_cache_path("AAPL", "test", "json")
        
        # Verify the path is correct
        expected_path = os.path.join(self.test_dir, "cache", "test", "AAPL.json")
        self.assertEqual(path, expected_path)
        
        # Verify the directory was created
        cache_dir = os.path.join(self.test_dir, "cache", "test")
        self.assertTrue(os.path.exists(cache_dir))
        self.assertTrue(os.path.isdir(cache_dir))

    def test_delete_if_not_from_this_month(self):
        """Test the delete_if_not_from_this_month function."""
        # Create a test file
        test_file = os.path.join(self.test_dir, "test_file.txt")
        with open(test_file, "w") as f:
            f.write("test")
        
        # Set the file's modification time to last month
        now = datetime.now()
        if now.month == 1:
            last_month = datetime(now.year - 1, 12, 1)
        else:
            last_month = datetime(now.year, now.month - 1, 1)
        os.utime(test_file, (last_month.timestamp(), last_month.timestamp()))
        
        # Call the function
        cache.delete_if_not_from_this_month(test_file)
        
        # Verify the file was deleted
        self.assertFalse(os.path.exists(test_file))

    def test_delete_if_not_from_this_month_current_month(self):
        """Test the delete_if_not_from_this_month function with a file from the current month."""
        # Create a test file
        test_file = os.path.join(self.test_dir, "test_file.txt")
        with open(test_file, "w") as f:
            f.write("test")
        
        # Set the file's modification time to the current month
        now = datetime.now()
        current_month = datetime(now.year, now.month, 1)
        os.utime(test_file, (current_month.timestamp(), current_month.timestamp()))
        
        # Call the function
        cache.delete_if_not_from_this_month(test_file)
        
        # Verify the file was not deleted
        self.assertTrue(os.path.exists(test_file))

    def test_valid_until_end_of_month(self):
        """Test the valid_until_end_of_month function."""
        # Create a test file
        test_file = os.path.join(self.test_dir, "test_file.txt")
        with open(test_file, "w") as f:
            f.write("test")
        
        # Call the function
        cache.valid_until_end_of_month(test_file)
        
        # Verify the file's modification time was set to the end of the month
        now = datetime.now()
        if now.month == 12:
            next_month = datetime(now.year + 1, 1, 1)
        else:
            next_month = datetime(now.year, now.month + 1, 1)
        
        file_mod_time = os.path.getmtime(test_file)
        self.assertAlmostEqual(file_mod_time, next_month.timestamp(), delta=1)


if __name__ == "__main__":
    unittest.main() 