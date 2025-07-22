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
from fins.server.ipython_session import get_session
from fins.entities.media import Chart


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
        
        # Basic health check endpoint
        @app.get("/api/health")
        async def health_check():
            return {"status": "healthy", "service": "fins-api"}
        
        # Serve rich elements by UUID
        @app.get("/api/rich/{session_id}/{element_id}")
        async def get_rich_element(session_id: int, element_id: str):
            print(f"[DEBUG] API request for rich element: session={session_id}, id={element_id}")
            session = get_session(session_id)
            element = session.get_rich_element(element_id)
            if not element:
                raise HTTPException(status_code=404, detail="Rich element not found")
            if element['type'] == 'image/png':
                from fastapi.responses import Response
                return Response(content=element['data'], media_type='image/png')
            # Add more types as needed
            raise HTTPException(status_code=415, detail="Unsupported rich element type")
        
        # Serve media from MediaCache
        @app.get("/api/media/{uuid}")
        async def get_media(uuid: str):
            print(f"[DEBUG] API request for media: {uuid}")
            from fins.entities.media import media_cache
            
            try:
                media = media_cache.get(uuid)
                if not media:
                    raise HTTPException(status_code=404, detail="Media not found")
                
                if isinstance(media, Chart):
                    from fastapi.responses import Response
                    return Response(content=media.image_bytes, media_type='image/png')
                else:
                    raise HTTPException(status_code=415, detail="Unsupported media type")
                    
            except Exception as e:
                print(f"[ERROR] Failed to serve media {uuid}: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        
        # Get media metadata
        @app.get("/api/media/{uuid}/metadata")
        async def get_media_metadata(uuid: str):
            print(f"[DEBUG] API request for media metadata: {uuid}")
            from fins.entities.media import media_cache
            
            try:
                media = media_cache.get(uuid)
                if not media:
                    raise HTTPException(status_code=404, detail="Media not found")
                
                return {
                    "uuid": uuid,
                    "type": media.__class__.__name__,
                    "handle": media.handle()
                }
                    
            except Exception as e:
                print(f"[ERROR] Failed to get media metadata {uuid}: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        
        # Mount static files at root (this will serve index.html at / and style.css at /style.css)
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
        
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