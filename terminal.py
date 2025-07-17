from fins.terminal import *
# from fins.terminal.symbols import *
# use this file in interactive mode

import sys
import threading
import time
import os

# Regular Python prompt
sys.ps1 = "FINS> "
sys.ps2 = "...   "

# IPython prompt configuration
try:
	from IPython import get_ipython
	from IPython.terminal.prompts import Prompts, Token


	class FinsPrompts(Prompts):
		def in_prompt_tokens(self, cli=None):
			return [(Token.Prompt, 'FINS> ')]

		def continuation_prompt_tokens(self, cli=None, width=None):
			return [(Token.Prompt, '...   ')]

		def out_prompt_tokens(self):
			return []


	ipython = get_ipython()
	if ipython is not None:
		ipython.prompts = FinsPrompts(ipython)

except (ImportError, AttributeError):
	# IPython not available or different version
	pass


# Import centralized shutdown mechanism
from fins.shutdown import setup_shutdown_handlers, register_cleanup_handler

# Setup shutdown handlers
setup_shutdown_handlers()

# Register database cleanup
try:
    from fins.database import shutdown_db
    register_cleanup_handler(shutdown_db)
except ImportError:
    pass

print("Welcome to FINS terminal")
