from fins.terminal import *
# from fins.terminal.symbols import *
# use this file in interactive mode

import sys

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


print("Welcome to FINS terminal")
