"""
Test utilities and decorators for the FINS test suite.
"""

import time
import functools
import os
import sys

import fins.data_sources.fmp


def time_it(func):
    """Decorator to time function execution and print the result."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"{func.__name__} took {elapsed_time:.2f} seconds")
        return result
    return wrapper


def time_it_detailed(func):
    """Decorator to time function execution with more detailed output."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        print(f"{func.__name__} took {elapsed_time:.4f} seconds (high precision)")
        return result
    return wrapper

def no_cache(func):
    """Decorator to disable cache."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from fins.financial import Symbol

        Symbol.set_caching("none")
        fmp_cache_original = fins.data_sources.fmp.use_cache
        fins.data_sources.fmp.use_cache = False

        result = func(*args, **kwargs)

        Symbol.set_caching("default")
        fins.data_sources.fmp.use_cache = fmp_cache_original
        return result
    return wrapper

def unbuffered_output(func):
    """Decorator to force immediate output by setting environment variable and using explicit flushing."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Set environment variable for unbuffered output
        old_pythonunbuffered = os.environ.get('PYTHONUNBUFFERED', '')
        os.environ['PYTHONUNBUFFERED'] = '1'
        
        # Force flush on all print statements by monkey-patching print temporarily
        import builtins
        original_print = builtins.print
        
        def flushing_print(*args, **kwargs):
            kwargs.setdefault('flush', True)
            return original_print(*args, **kwargs)
        
        builtins.print = flushing_print
        
        try:
            result = func(*args, **kwargs)
        finally:
            # Restore original state
            builtins.print = original_print
            if old_pythonunbuffered:
                os.environ['PYTHONUNBUFFERED'] = old_pythonunbuffered
            else:
                os.environ.pop('PYTHONUNBUFFERED', None)
        
        return result
    return wrapper
