#!/usr/bin/env python3
"""
Script to run FINS tests directly
"""

import unittest
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the test module
from test_parser import TestFinsParser

if __name__ == "__main__":
    unittest.main() 