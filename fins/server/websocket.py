"""
WebSocket Server Module

This module provides WebSocket server for streaming IPython session to browser.
"""

import threading
import time
import os
import logging
import json
import asyncio
from typing import Dict, Set
from datetime import datetime, timedelta

# Import centralized shutdown mechanism
from fins.shutdown import set_shutdown_event, is_shutdown_requested
from .ipython_session import execute_code, get_session_count, remove_session, get_session
from fins.entities import BasketRuntime
from fins.entities.media import media_cache


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        self.connections: Set[object] = set()
        self.session_map: Dict[object, int] = {}  # Map websocket to session_id
        self.session_last_seen: Dict[int, datetime] = {}  # Track when sessions were last active
        self.lock = threading.Lock()
        self.session_timeout = timedelta(minutes=30)  # Sessions expire after 30 minutes of inactivity
    
    def add_connection(self, websocket, session_id: int = None):
        """Add a new WebSocket connection."""
        with self.lock:
            self.connections.add(websocket)
            if session_id:
                self.session_map[websocket] = session_id
                self.session_last_seen[session_id] = datetime.now()
    
    def remove_connection(self, websocket):
        """Remove a WebSocket connection but keep the session alive."""
        with self.lock:
            self.connections.discard(websocket)
            if websocket in self.session_map:
                session_id = self.session_map[websocket]
                del self.session_map[websocket]
                # Don't cleanup the session immediately - it might reconnect
                print(f"Client disconnected, keeping session {session_id} alive for potential reconnection")
    
    def update_session_activity(self, session_id: int):
        """Update the last activity time for a session."""
        with self.lock:
            self.session_last_seen[session_id] = datetime.now()
    
    def cleanup_expired_sessions(self):
        """Clean up sessions that have been inactive for too long."""
        with self.lock:
            now = datetime.now()
            expired_sessions = []
            
            for session_id, last_seen in self.session_last_seen.items():
                if now - last_seen > self.session_timeout:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                print(f"Cleaning up expired session {session_id} (inactive for {self.session_timeout})")
                remove_session(session_id)
                del self.session_last_seen[session_id]
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients."""
        with self.lock:
            connections = list(self.connections)
        
        for websocket in connections:
            try:
                await websocket.send(message)
            except Exception as e:
                logging.error(f"Error sending to websocket: {e}")
                self.remove_connection(websocket)


# Global WebSocket manager
ws_manager = WebSocketManager()


def start_websocket_server():
    """Start WebSocket server in background thread."""
    print("Starting WebSocket server in background...")
    
    try:
        import websockets
        import asyncio
        
        async def websocket_handler(websocket, path):
            """Handle WebSocket connections."""
            client_session_id = None
            ws_manager.add_connection(websocket)
            print(f"WebSocket client connected: {websocket.remote_address}")
            
            try:
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        if data.get('type') == 'command':
                            command = data.get('command', '')
                            session_id = data.get('session_id', 1)  # Default to session 1
                            
                            # Track session ID for this connection
                            if client_session_id is None:
                                client_session_id = session_id
                                ws_manager.add_connection(websocket, session_id)
                            
                            # Update session activity
                            ws_manager.update_session_activity(session_id)
                            
                            print(f"Received command for session {session_id}: {command}")
                            
                            # Execute command in IPython session
                            output, error, success = execute_code(command, session_id)
                            
                            if success:
                                # Check if the result is a BasketRuntime (which contains media)
                                
                                # Get the last result from the IPython session
                                session = get_session(session_id)
                                if session and hasattr(session.ipython, 'last_result'):
                                    last_result = session.ipython.last_result
                                    
                                    if isinstance(last_result, BasketRuntime):
                                        print(f"[DEBUG] BasketRuntime detected in session {session_id}")
                                        
                                        # Get the output data from the BasketRuntime
                                        output_data = last_result.output_data()
                                        
                                        # Process any media in the output data
                                        media_handles = []
                                        for series_name, series_data in output_data._items.items():
                                            for item_idx, item_data in series_data.items():
                                                if hasattr(item_data, 'handle') and callable(item_data.handle):
                                                    # This is a Media object
                                                    media_cache.register(item_data)
                                                    handle = item_data.handle()
                                                    media_handles.append(handle)
                                                    print(f"[DEBUG] Found media handle: {handle}")
                                        
                                        # Send the regular output first
                                        if output.strip():
                                            response = {
                                                'type': 'output',
                                                'content': output.strip()
                                            }
                                            await websocket.send(json.dumps(response))
                                        
                                        # Send media handles as a special message
                                        if media_handles:
                                            media_response = {
                                                'type': 'media',
                                                'handles': media_handles
                                            }
                                            await websocket.send(json.dumps(media_response))
                                            print(f"[DEBUG] Sent {len(media_handles)} media handles to client")
                                        
                                        # If no regular output, send success message
                                        if not output.strip() and not media_handles:
                                            response = {
                                                'type': 'output',
                                                'content': 'Command executed successfully'
                                            }
                                            await websocket.send(json.dumps(response))
                                    else:
                                        # Regular output (not BasketRuntime)
                                        if output.strip():
                                            response = {
                                                'type': 'output',
                                                'content': output.strip()
                                            }
                                            await websocket.send(json.dumps(response))
                                        else:
                                            # Command executed successfully but no output
                                            response = {
                                                'type': 'output',
                                                'content': 'Command executed successfully'
                                            }
                                            await websocket.send(json.dumps(response))
                                else:
                                    # Fallback for regular output
                                    if output.strip():
                                        response = {
                                            'type': 'output',
                                            'content': output.strip()
                                        }
                                        await websocket.send(json.dumps(response))
                                    else:
                                        # Command executed successfully but no output
                                        response = {
                                            'type': 'output',
                                            'content': 'Command executed successfully'
                                        }
                                        await websocket.send(json.dumps(response))
                            else:
                                # Send error
                                response = {
                                    'type': 'error',
                                    'content': error.strip() if error.strip() else 'Unknown error'
                                }
                                await websocket.send(json.dumps(response))

                    except json.JSONDecodeError:
                        await websocket.send(json.dumps({
                            'type': 'error',
                            'content': 'Invalid JSON'
                        }))
                    except Exception as e:
                        logging.error(f"Error handling message: {e}")
                        await websocket.send(json.dumps({
                            'type': 'error',
                            'content': f'Internal server error: {e}'
                        }))
            except Exception as e:
                logging.error(f"WebSocket connection error: {e}")
            finally:
                ws_manager.remove_connection(websocket)
                print(f"WebSocket client disconnected: {websocket.remote_address}")
        
        async def cleanup_task():
            """Background task to clean up expired sessions."""
            while not is_shutdown_requested():
                try:
                    ws_manager.cleanup_expired_sessions()
                    await asyncio.sleep(60)  # Check every minute
                except Exception as e:
                    logging.error(f"Error in cleanup task: {e}")
                    await asyncio.sleep(60)
        
        async def run_server():
            """Run the WebSocket server."""
            server = await websockets.serve(
                websocket_handler,
                "127.0.0.1",
                8001
            )
            
            print("🌐 WebSocket server started at ws://localhost:8001")
            print("   (Server running in same process)")
            print(f"   (Sessions timeout after {ws_manager.session_timeout})")
            
            # Start cleanup task
            cleanup_task_handle = asyncio.create_task(cleanup_task())
            
            # Keep server running until shutdown
            while not is_shutdown_requested():
                await asyncio.sleep(1)
            
            # Cancel cleanup task
            cleanup_task_handle.cancel()
            try:
                await cleanup_task_handle
            except asyncio.CancelledError:
                pass
            
            server.close()
            await server.wait_closed()
        
        # Start server in background thread
        def run_in_thread():
            try:
                asyncio.run(run_server())
            except Exception as e:
                print(f"⚠️  WebSocket server error: {e}")
        
        server_thread = threading.Thread(target=run_in_thread, daemon=True)
        server_thread.start()
        
        # Wait a moment for server to start
        time.sleep(2)
        
        return server_thread
        
    except ImportError:
        print("⚠️  websockets not found. Install with: poetry add websockets")
        return None
    except Exception as e:
        print(f"⚠️  Error starting WebSocket server: {e}")
        return None


async def broadcast_to_clients(message: str):
    """Broadcast message to all connected WebSocket clients."""
    await ws_manager.broadcast(message) 