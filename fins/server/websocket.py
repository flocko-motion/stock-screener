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

# Import centralized shutdown mechanism
from fins.shutdown import set_shutdown_event, is_shutdown_requested
from .ipython_session import execute_code


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        self.connections: Set[object] = set()
        self.lock = threading.Lock()
    
    def add_connection(self, websocket):
        """Add a new WebSocket connection."""
        with self.lock:
            self.connections.add(websocket)
    
    def remove_connection(self, websocket):
        """Remove a WebSocket connection."""
        with self.lock:
            self.connections.discard(websocket)
    
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
            ws_manager.add_connection(websocket)
            print(f"WebSocket client connected: {websocket.remote_address}")
            
            try:
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        if data.get('type') == 'command':
                            command = data.get('command', '')
                            print(f"Received command: {command}")
                            
                            # Execute command in IPython session
                            output, error, success = execute_code(command)
                            
                            if success:
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
                        elif data.get('type') == 'completion':
                            text = data.get('text', '')
                            print(f"Received completion request for: {text}")
                            
                            # Get completions from IPython session
                            completions = get_completions(text)
                            
                            response = {
                                'type': 'completion',
                                'completions': completions
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
        
        async def run_server():
            """Run the WebSocket server."""
            server = await websockets.serve(
                websocket_handler,
                "127.0.0.1",
                8001
            )
            
            print("🌐 WebSocket server started at ws://localhost:8001")
            print("   (Server running in same process)")
            
            # Keep server running until shutdown
            while not is_shutdown_requested():
                await asyncio.sleep(1)
            
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