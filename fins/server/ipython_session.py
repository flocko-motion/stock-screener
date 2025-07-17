"""
IPython Session Manager

This module provides an IPython session that runs in the same process
to maintain in-memory caching and state.
"""

import sys
import io
import traceback
from contextlib import redirect_stdout, redirect_stderr
from typing import Dict, Any, Tuple


class IPythonSession:
    """Manages an IPython session in the same process."""
    
    def __init__(self):
        """Initialize the IPython session."""
        try:
            from IPython import get_ipython
            from IPython.terminal.prompts import Prompts, Token
            
            # Get or create IPython instance
            self.ipython = get_ipython()
            if self.ipython is None:
                # Create a new IPython instance
                from IPython import start_ipython
                # We'll use a different approach - create the namespace directly
                self.ipython = self._create_ipython()
            
            # Set up FINS prompts
            class FinsPrompts(Prompts):
                def in_prompt_tokens(self, cli=None):
                    return [(Token.Prompt, 'FINS> ')]
                
                def continuation_prompt_tokens(self, cli=None, width=None):
                    return [(Token.Prompt, '...   ')]
                
                def out_prompt_tokens(self):
                    return []
            
            if hasattr(self.ipython, 'prompts'):
                self.ipython.prompts = FinsPrompts(self.ipython)
            
            # Import FINS modules into the session
            self._setup_fins_environment()
            
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
            sys.ps1 = "FINS> "
            sys.ps2 = "...   "
            
            print("FINS environment loaded in IPython session")
            
        except Exception as e:
            print(f"⚠️  Error setting up FINS environment: {e}")
    
    def execute(self, code: str) -> Tuple[str, str, bool]:
        """
        Execute code in the IPython session.
        
        Args:
            code: The code to execute
            
        Returns:
            Tuple of (output, error, success)
        """
        if not self.ipython:
            return "", "IPython not available", False
        
        # Capture stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
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
                if hasattr(result, 'result') and result.result is not None:
                    result_str = str(result.result)
                    if result_str and result_str != 'None':
                        output += result_str + '\n'
                
                # Also check for the last result in IPython's result history
                if hasattr(self.ipython, 'last_result') and self.ipython.last_result is not None:
                    last_result = str(self.ipython.last_result)
                    if last_result and last_result != 'None' and last_result not in output:
                        output += last_result + '\n'
                
                return output, error, success
                
        except Exception as e:
            error = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            return "", error, False
    
    def get_completions(self, text: str) -> List[str]:
        """Get completions for the given text."""
        if not self.ipython:
            return []
        
        try:
            # Use IPython's completion system
            completions = self.ipython.complete(text)
            return list(completions)
        except Exception as e:
            print(f"⚠️  Error getting completions: {e}")
            return []


# Global session instance
_session = None

def get_session() -> IPythonSession:
    """Get the global IPython session instance."""
    global _session
    if _session is None:
        _session = IPythonSession()
    return _session

def execute_code(code: str) -> Tuple[str, str, bool]:
    """Execute code in the IPython session."""
    session = get_session()
    return session.execute(code)

def get_completions(text: str) -> List[str]:
    """Get completions for the given text."""
    session = get_session()
    return session.get_completions(text) 