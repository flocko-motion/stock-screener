"""
Jupyter Server Module

This module provides Jupyter server functionality for FINS.
"""

import threading
import time
import os
import logging
import sys

# Import centralized shutdown mechanism
from fins.shutdown import set_shutdown_event, is_shutdown_requested


def start_jupyter_server():
    """Start Jupyter server in background thread within same process."""
    print("Starting Jupyter server in background...")
    
    try:
        import jupyter_server
        from jupyter_server.serverapp import ServerApp
        from jupyter_server.auth import passwd
        import tornado.ioloop
        
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
                
                # Check for shutdown while running
                while not is_shutdown_requested():
                    tornado.ioloop.IOLoop.current().start()
                    break  # Exit loop if IOLoop stops
                    
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