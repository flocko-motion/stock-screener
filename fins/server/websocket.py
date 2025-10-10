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

import pandas as pd

# Import centralized shutdown mechanism
from fins.shutdown import set_shutdown_event, is_shutdown_requested
from .ipython_session import execute_code, get_session_count, remove_session, get_session
from fins.entities import BasketRuntime
from fins.entities.media import media_cache, DataFrameMedia


async def send_response(websocket, response_type, content):
    """Send a response to the client."""
    response = {'type': response_type, 'content': content}
    await websocket.send(json.dumps(response))


async def handle_command_output(websocket, output, session_id, command_res=None):
    """Handle command output and extract media if BasketRuntime is present."""
    media_handles = []

    # If BasketRuntime, register its DataFrame as media
    if isinstance(command_res, BasketRuntime):
        print(f"[DEBUG] BasketRuntime detected in session {session_id}")
        handle = DataFrameMedia(command_res.df()).handle()
        media_handles.append(handle)
        print(f"[DEBUG] Registered DataFrameMedia handle: {handle}")
    elif isinstance(command_res, pd.DataFrame):
        print(f"[DEBUG] DataFrame detected in session {session_id}")
        handle = DataFrameMedia(command_res).handle()
        media_handles.append(handle)
        print(f"[DEBUG] Registered DataFrameMedia handle: {handle}")

    # Send the regular output first
    if output.strip():
        await send_response(websocket, 'output', output.strip())

    # Send media handles as a special message
    if media_handles:
        media_response = {'type': 'media', 'handles': media_handles}
        await websocket.send(json.dumps(media_response))
        print(f"[DEBUG] Sent {len(media_handles)} media handles to client")

    # If no regular output and no media, send success message
    if not output.strip() and not media_handles:
        await send_response(websocket, 'output', 'Command executed successfully')


async def process_command(websocket, command, session_id):
    """Process a single command and send response."""
    print(f"Received command for session {session_id}: {command}")

    # Strip and check command
    cmd_stripped = command.strip()

    # Redirect help commands to Help()
    if cmd_stripped in ('help()', '?', 'help'):
        # Execute Help() command instead
        output, error, success, result = execute_code('Help()', session_id)
        if success:
            await handle_command_output(websocket, output, session_id, result)
        else:
            await send_response(websocket, 'error', error.strip() if error.strip() else 'Unknown error')
        return

    # Convert object-specific help (e.g., "object?") to print docstring
    if cmd_stripped.endswith('?') and len(cmd_stripped) > 1:
        obj_name = cmd_stripped[:-1].strip()
        # Execute print(obj.__doc__) instead of interactive help
        docstring_cmd = f"print({obj_name}.__doc__ if hasattr({obj_name}, '__doc__') and {obj_name}.__doc__ else 'No documentation available')"
        output, error, success, result = execute_code(
            docstring_cmd, session_id)
        if success:
            await handle_command_output(websocket, output, session_id, result)
        else:
            await send_response(websocket, 'error', error.strip() if error.strip() else 'Unknown error')
        return

    # Execute command in IPython session
    output, error, success, result = execute_code(command, session_id)

    if success:
        await handle_command_output(websocket, output, session_id, result)
    else:
        # Send error
        await send_response(websocket, 'error', error.strip() if error.strip() else 'Unknown error')


async def handle_websocket_messages(websocket, client_session_id):
    """Handle all WebSocket messages for a connection."""
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get('type') == 'command':
                    command = data.get('command', '')
                    # Default to session 1
                    session_id = data.get('session_id', 1)

                    # Track session ID for this connection
                    if client_session_id is None:
                        client_session_id = session_id
                        ws_manager.add_connection(websocket, session_id)

                    # Update session activity
                    ws_manager.update_session_activity(session_id)

                    await process_command(websocket, command, session_id)

            except json.JSONDecodeError:
                await send_response(websocket, 'error', 'Invalid JSON')
            except Exception as e:
                logging.error(f"Error handling message: {e}")
                await send_response(websocket, 'error', f'Internal server error: {e}')
    except Exception as e:
        logging.error(f"WebSocket connection error: {e}")


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self):
        self.connections: Set[object] = set()
        self.session_map: Dict[object, int] = {}  # Map websocket to session_id
        # Track when sessions were last active
        self.session_last_seen: Dict[int, datetime] = {}
        self.lock = threading.Lock()
        # Sessions expire after 30 minutes of inactivity
        self.session_timeout = timedelta(minutes=30)

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
                print(
                    f"Client disconnected, keeping session {session_id} alive for potential reconnection")

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
                print(
                    f"Cleaning up expired session {session_id} (inactive for {self.session_timeout})")
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
                await handle_websocket_messages(websocket, client_session_id)
            except Exception as e:
                logging.error(f"WebSocket connection error: {e}")
            finally:
                ws_manager.remove_connection(websocket)
                print(
                    f"WebSocket client disconnected: {websocket.remote_address}")

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
