"""
Utility functions and classes for the FINS application.
"""

import time


def format_value(value) -> str:
    """
    Format a value for inclusion in Python code.
    
    Args:
        value: Any value to format
        
    Returns:
        String representation suitable for Python code
    """
    if value is None:
        return "None"
    elif isinstance(value, str):
        return f"'{value}'"
    elif isinstance(value, bool):
        return str(value)
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, (list, tuple)):
        formatted_items = [format_value(item) for item in value]
        if isinstance(value, list):
            return f"[{', '.join(formatted_items)}]"
        else:
            return f"({', '.join(formatted_items)})"
    elif isinstance(value, dict):
        formatted_items = [f"{format_value(k)}: {format_value(v)}" for k, v in value.items()]
        return f"{{{', '.join(formatted_items)}}}"
    elif isinstance(value, set):
        formatted_items = [format_value(item) for item in value]
        return f"[{', '.join(formatted_items)}]"  # Represent as list for readability
    elif hasattr(value, 'isoformat') and hasattr(value, 'date'):  # datetime.date objects
        if hasattr(value, 'time'):  # datetime.datetime
            return f"datetime.datetime.fromisoformat('{value.isoformat()}')"
        else:  # datetime.date
            return f"datetime.date.fromisoformat('{value.isoformat()}')"
    elif hasattr(value, '__class__'):
        # For other objects, try to represent them reasonably
        return f"{value.__class__.__name__}(...)"
    else:
        return repr(value)


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to a human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string like "1h 23m 45s", "5m 30s", or "42s"
    """
    if seconds <= 0:
        return "0s"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:  # Always show seconds if nothing else
        parts.append(f"{secs}s")
    
    return " ".join(parts)


class ProgressTracker:
    """
    A reusable progress tracker that displays real-time statistics.
    
    Usage:
        tracker = ProgressTracker(1000, "Fetching symbols")
        for item in items:
            # Do work
            tracker.next()
        tracker.done()
    """
    
    def __init__(self, total: int, description: str = "Processing"):
        """
        Initialize the progress tracker.
        
        Args:
            total: Total number of items to process
            description: Description of what's being processed
        """
        self.total = total
        self.description = description
        self.completed = 0
        self.start_time = time.time()
        self.last_print_time = 0
        
        print(f"{self.description} {self.total} items...")
    
    def next(self) -> None:
        """Mark one item as completed and update the display."""
        self.completed += 1
        
        # Rate limit output - only print if 0.5 seconds have passed since last print
        current_time = time.time()
        if current_time - self.last_print_time < 0.5:
            return
        
        self.last_print_time = current_time
        
        # Calculate stats
        elapsed_time = current_time - self.start_time
        items_per_sec = self.completed / elapsed_time if elapsed_time > 0 else 0
        remaining = self.total - self.completed
        eta_seconds = remaining / items_per_sec if items_per_sec > 0 else 0
        
        # Format time
        elapsed_str = format_duration(elapsed_time)
        eta_str = format_duration(eta_seconds)
        
        print(f"\r{self.completed}/{self.total} ({items_per_sec:.1f}/s) - {elapsed_str} elapsed, {eta_str} left", end='', flush=True)
    
    def done(self) -> None:
        """Mark processing as complete and print final stats."""
        elapsed_time = time.time() - self.start_time
        items_per_sec = self.completed / elapsed_time if elapsed_time > 0 else 0
        
        print(f"\rCompleted {self.completed}/{self.total} in {format_duration(elapsed_time)} ({items_per_sec:.1f}/s)") 