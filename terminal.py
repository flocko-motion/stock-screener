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


def start_jupyter_server():
	print("Starting Jupyter server in background...")
	"""Start Jupyter server in background thread within same process."""
	try:
		import jupyter_server
		from jupyter_server.serverapp import ServerApp
		from jupyter_server.auth import passwd
		import tornado.ioloop
		import signal
		import logging
		import os
		import sys
		
		# Configure Jupyter server
		app = ServerApp()
		app.port = 8888
		app.ip = '127.0.0.1'
		app.open_browser = False
		app.allow_root = True
		app.allow_origin = '*'
		app.init_signal = lambda: None  # Disable signal handling in background thread
		app.default_url = '/lab'  # Open JupyterLab by default
		app.root_dir = './notebooks'  # Set default working directory
		app.notebook_dir = './notebooks'  # Set notebook directory
		
		# Ensure notebooks directory exists
		os.makedirs('./notebooks', exist_ok=True)
		
		# Start server in background thread
		def run_server():
			try:
				# Set logging level to ERROR to suppress INFO messages
				logging.getLogger('jupyter_server').setLevel(logging.ERROR)
				logging.getLogger('jupyterlab').setLevel(logging.ERROR)
				logging.getLogger('notebook').setLevel(logging.ERROR)
				logging.getLogger('tornado.access').setLevel(logging.ERROR)
				logging.getLogger('tornado.application').setLevel(logging.ERROR)
				logging.getLogger('tornado.general').setLevel(logging.ERROR)
				
				app.initialize()
				app.start()
				tornado.ioloop.IOLoop.current().start()
			except Exception as e:
				print(f"⚠️  Jupyter server error: {e}")
		
		server_thread = threading.Thread(target=run_server, daemon=True)
		server_thread.start()
		
		# Wait a moment for server to start
		time.sleep(2)
		
		print("🌐 Jupyter Lab started at http://localhost:8888")
		print("   (Server running in same process)")
		
		return server_thread
		
	except ImportError:
		print("⚠️  Jupyter Server not found. Install with: poetry add jupyter-server")
		return None
	except Exception as e:
		print(f"⚠️  Error starting Jupyter: {e}")
		return None


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

# Start Jupyter server in background thread
jupyter_thread = start_jupyter_server()

print("Welcome to FINS terminal")
