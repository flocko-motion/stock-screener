"""
IPython Session Manager

This module provides multiple IPython sessions managed by session IDs
to allow multiple users to have isolated sessions.
"""

import sys
import io
import traceback
from contextlib import redirect_stdout, redirect_stderr
from typing import Dict, Any, Tuple, List
import threading
from fins.shutdown import register_cleanup_handler, is_shutdown_requested
import uuid
import base64
import types

from matplotlib.figure import Figure

class IPythonSession:
    """Manages an IPython session in the same process."""
    
    def __init__(self, session_id: int):
        """Initialize the IPython session."""
        self.session_id = session_id
        self.rich_element_cache: Dict[str, dict] = {}  # uuid -> {type, data}
        try:
            from IPython import get_ipython
            from IPython.terminal.prompts import Prompts, Token
            
            # Create a new IPython instance for this session
            self.ipython = self._create_ipython()
            
            # Set up FINS prompts
            class FinsPrompts(Prompts):
                def in_prompt_tokens(self, cli=None):
                    return [(Token.Prompt, f'FINS[{session_id}]> ')]
                
                def continuation_prompt_tokens(self, cli=None, width=None):
                    return [(Token.Prompt, '...   ')]
                
                def out_prompt_tokens(self):
                    return []
            
            if hasattr(self.ipython, 'prompts'):
                self.ipython.prompts = FinsPrompts(self.ipython)
            
            # Import FINS modules into the session
            self._setup_fins_environment()
            
            # Register display hook for rich elements
            self._register_display_hook()
            
        except ImportError:
            print("⚠️  IPython not available")
            self.ipython = None
    
    def _create_ipython(self):
        """Create an IPython instance programmatically."""
        try:
            from IPython.core.interactiveshell import InteractiveShell
            
            # Create a shell instance
            shell = InteractiveShell()
            return shell
            
        except Exception as e:
            print(f"⚠️  Error creating IPython shell: {e}")
            return None
    
    def _setup_fins_environment(self):
        """Set up the FINS environment in the IPython session."""
        if not self.ipython:
            return
        
        try:
            # Import the terminal module - it should provide everything
            import fins.terminal
            
            # Copy all terminal symbols to the IPython namespace
            for name in dir(fins.terminal):
                if not name.startswith('_'):
                    self.ipython.user_ns[name] = getattr(fins.terminal, name)
            
            # Set up the prompt
            sys.ps1 = f"FINS[{self.session_id}]> "
            sys.ps2 = "...   "
            
            print(f"FINS environment loaded in IPython session {self.session_id}")
            
        except Exception as e:
            print(f"⚠️  Error setting up FINS environment: {e}")
    
    def execute(self, code: str) -> Tuple[str, str, bool, object]:
        """
        Execute code in the IPython session.
        
        Args:
            code: The code to execute
            
        Returns:
            Tuple of (output, error, success, result)
        """
        if not self.ipython:
            return "", "IPython not available", False, None
        
        # Capture stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        result_obj = None
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Execute the code
                result = self.ipython.run_cell(code)
                
                # Get the output
                output = stdout_capture.getvalue()
                error = stderr_capture.getvalue()
                
                # Check if execution was successful
                success = not result.error_in_exec
                
                # If there was an error, get the traceback
                if not success and result.error_in_exec:
                    error = ''.join(traceback.format_exception(
                        result.error_in_exec.__class__,
                        result.error_in_exec,
                        result.error_in_exec.__traceback__
                    ))
                
                # Get the result value if there is one
                if hasattr(result, 'result'):
                    result_obj = result.result
                    if result_obj is not None:
                        result_str = str(result_obj)
                        if result_str and result_str != 'None':
                            output += result_str + '\n'
                
                # Also check for the last result in IPython's result history
                if hasattr(self.ipython, 'last_result') and self.ipython.last_result is not None:
                    last_result = str(self.ipython.last_result)
                    if last_result and last_result != 'None' and last_result not in output:
                        output += last_result + '\n'
                
                # Debug: Check if any rich elements were captured
                print(f"[DEBUG] Rich element cache size: {len(self.rich_element_cache)}")
                if self.rich_element_cache:
                    print(f"[DEBUG] Rich elements captured: {list(self.rich_element_cache.keys())}")
                
                return output, error, success, result_obj
                
        except Exception as e:
            error = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            return "", error, False, None
    
    def get_completions(self, text: str) -> List[str]:
        """Get completions for the given text."""
        # Auto-completion disabled for now
        return []

    def _register_display_hook(self):
        """Register a display hook to capture rich elements like matplotlib figures."""
        shell = self.ipython
        if not shell:
            return
        old_publish = shell.display_pub.publish
        session = self

        def custom_publish(data, metadata=None, source=None, **kwargs):
            print(f"[DEBUG] Display hook called with data type: {type(data)}")
            # Matplotlib Figure
            if isinstance(data, Figure):
                print(f"[DEBUG] Matplotlib figure detected: {data}")
                buf = io.BytesIO()
                data.savefig(buf, format='png')
                buf.seek(0)
                img_bytes = buf.read()
                element_id = str(uuid.uuid4())
                session.rich_element_cache[element_id] = {
                    'type': 'image/png',
                    'data': img_bytes,
                }
                print(f"[DEBUG] Captured matplotlib figure as rich element: {element_id}")
                print(f"RICH_ELEMENT:{element_id}:image/png")
                return
            # Add more types as needed (e.g., DataFrame, HTML, etc.)
            print(f"[DEBUG] Using default display for: {type(data)}")
            old_publish(data, metadata, source, **kwargs)
        shell.display_pub.publish = custom_publish

    def get_rich_element(self, element_id: str):
        return self.rich_element_cache.get(element_id)


class SessionManager:
    """Manages multiple IPython sessions by session ID."""
    
    def __init__(self):
        self.sessions: Dict[int, IPythonSession] = {}
        self.lock = threading.Lock()
        # Register cleanup handler for graceful shutdown
        register_cleanup_handler(self.cleanup_all_sessions)
    
    def get_session(self, session_id: int) -> IPythonSession:
        """Get or create a session for the given session ID."""
        with self.lock:
            if session_id not in self.sessions:
                print(f"Creating new IPython session for ID: {session_id}")
                self.sessions[session_id] = IPythonSession(session_id)
            return self.sessions[session_id]
    
    def remove_session(self, session_id: int):
        """Remove a session (cleanup)."""
        with self.lock:
            if session_id in self.sessions:
                print(f"Removing IPython session for ID: {session_id}")
                del self.sessions[session_id]
    
    def get_session_count(self) -> int:
        """Get the number of active sessions."""
        with self.lock:
            return len(self.sessions)
    
    def cleanup_all_sessions(self):
        """Clean up all sessions during shutdown."""
        with self.lock:
            session_count = len(self.sessions)
            if session_count > 0:
                print(f"🧹 Cleaning up {session_count} IPython sessions...")
                self.sessions.clear()
                print(f"✅ Cleaned up {session_count} IPython sessions")


# Global session manager
_session_manager = SessionManager()

def get_session(session_id: int) -> IPythonSession:
    """Get or create a session for the given session ID."""
    return _session_manager.get_session(session_id)

def remove_session(session_id: int):
    """Remove a session."""
    _session_manager.remove_session(session_id)

def get_session_count() -> int:
    """Get the number of active sessions."""
    return _session_manager.get_session_count()

def execute_code(code: str, session_id: int) -> Tuple[str, str, bool, object]:
    """Execute code in the specified IPython session."""
    session = get_session(session_id)
    return session.execute(code)

def get_completions(text: str, session_id: int) -> List[str]:
    """Get completions for the given text in the specified session."""
    session = get_session(session_id)
    return session.get_completions(text) 