"""
API Server Module

This module provides HTTP REST API server for FINS using FastAPI.
"""

import threading
import time
import os
import logging
from pathlib import Path

# Import centralized shutdown mechanism
from fins.shutdown import set_shutdown_event, is_shutdown_requested


def start_api_server():
    """Start FastAPI server in background thread."""
    print("Starting API server in background...")
    
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import HTMLResponse
        import uvicorn
        
        # Create FastAPI app
        app = FastAPI(title="FINS API", version="1.0.0")
        
        # Create static files directory for client
        static_dir = Path("./fins/server/html")
        static_dir.mkdir(parents=True, exist_ok=True)
        
        # Mount static files
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        
        # Basic health check endpoint
        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "service": "fins-api"}
        
        # Serve the client HTML
        @app.get("/", response_class=HTMLResponse)
        async def serve_client():
            html_file = static_dir / "index.html"
            if html_file.exists():
                with open(html_file, 'r') as f:
                    return f.read()
            else:
                return HTMLResponse(content="<h1>FINS Console</h1><p>HTML file not found</p>", status_code=404)
        
        # Start server in background thread
        def run_server():
            try:
                config = uvicorn.Config(
                    app=app,
                    host="127.0.0.1",
                    port=8000,
                    log_level="error"
                )
                server = uvicorn.Server(config)
                
                # Check for shutdown while running
                while not is_shutdown_requested():
                    server.run()
                    break  # Exit loop if server stops
                    
            except Exception as e:
                print(f"⚠️  API server error: {e}")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait a moment for server to start
        time.sleep(2)
        
        print("🌐 API server started at http://localhost:8000")
        print("   (Server running in same process)")
        
        return server_thread
        
    except ImportError:
        print("⚠️  FastAPI not found. Install with: poetry add fastapi uvicorn")
        return None
    except Exception as e:
        print(f"⚠️  Error starting API server: {e}")
        return None 