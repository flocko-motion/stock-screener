"""
OpenAI Assistant Integration for Notebook

This module provides integration with OpenAI's Assistant API to create an AI assistant
that can access and analyze all notes in the notebook system.
"""

import yaml
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

import openai
from openai import OpenAI

from fins.config import PATH_ASSISTANT_CONFIG, DIR_PERSISTENCE, get_openai_api_key, get_assistant_id, save_assistant_id
from fins.notebook import get_notebook


class NotebookAssistant:
    """
    OpenAI Assistant integration for the FINS notebook system.
    
    Manages assistant creation, file uploads, and state persistence.
    """
    
    def __init__(self, api_key: Optional[str] = None, testing_mode: bool = False):
        """
        Initialize the notebook assistant.
        
        Args:
            api_key: OpenAI API key (will be loaded from config if not provided)
            testing_mode: If True, create new assistant and don't persist ID
        """
        self.api_key = api_key or self._load_api_key()
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set it in assistant.yaml config file.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.assistant_id = None
        self.assistant = None
        self.thread_id = None
        self.testing_mode = testing_mode
        
        # Load or create assistant
        self._load_or_create_assistant()
    
    def _load_api_key(self) -> Optional[str]:
        """Load API key from assistant config file."""
        return get_openai_api_key()
    
    def _save_config(self):
        """Save assistant configuration to file."""
        if not self.testing_mode:
            save_assistant_id(self.assistant_id)
    
    def _load_or_create_assistant(self):
        """Load existing assistant or create a new one."""
        # Skip config loading in testing mode
        if self.testing_mode:
            self._create_assistant()
            return
        
        # Try to load existing assistant ID
        assistant_id = get_assistant_id()
        
        if assistant_id:
            try:
                self.assistant = self.client.assistants.retrieve(assistant_id)
                self.assistant_id = assistant_id
                print(f"✓ Loaded existing assistant: {assistant_id}")
                return
            except Exception as e:
                print(f"⚠ Failed to load assistant {assistant_id}: {e}")
        
        # Create new assistant
        self._create_assistant()
    
    def _create_assistant(self):
        """Create a new OpenAI assistant."""
        base_instructions = """You are a financial analysis assistant with access to a comprehensive notebook of market observations, trades, facts, and strategies.

Your knowledge base includes:
- Market observations and insights
- Trading records and analysis
- Factual information about companies and markets
- Investment strategies and principles
- Symbol-specific notes and analysis

When analyzing or responding:
1. Reference specific notes when relevant
2. Provide context from the notebook data
3. Be precise about dates, symbols, and financial data
4. Suggest connections between different notes
5. Help identify patterns or insights across the data

Always cite your sources from the notebook when making claims or providing analysis."""

        self.assistant = self.client.assistants.create(
            name="FINS Financial Assistant",
            instructions=base_instructions,
            model="gpt-4o",
            tools=[{"type": "file_search"}]
        )
        
        self.assistant_id = self.assistant.id
        self._save_config()
        print(f"✓ Created new assistant: {self.assistant_id}")
    
    def _upload_note_file(self, note) -> Optional[str]:
        """
        Upload a note as a file to the assistant.
        
        Args:
            note: Note entity to upload
            
        Returns:
            File ID if successful, None otherwise
        """
        try:
            # Create verbose JSON representation
            note_data = note.to_dict()
            
            # Add metadata for better context
            note_data['_metadata'] = {
                'entity_type': note.entity_type,
                'note_id': note.id,
                'created_at': note.created_at.isoformat() if note.created_at else None,
                'updated_at': note.updated_at.isoformat() if note.updated_at else None,
                'related_symbols': note.related_symbols
            }
            
            # Create filename
            timestamp = note.created_at.strftime('%Y%m%d_%H%M%S') if note.created_at else 'unknown'
            filename = f"{note.entity_type}_{timestamp}_{note.id[:8]}.json"
            
            # Upload file
            file = self.client.files.create(
                file=json.dumps(note_data, indent=2).encode('utf-8'),
                purpose='assistants'
            )
            
            return file.id
            
        except Exception as e:
            print(f"⚠ Failed to upload note {note.id}: {e}")
            return None
    
    def sync_notes(self, force: bool = False):
        """
        Sync all notes to the assistant.
        
        Args:
            force: If True, re-upload all notes even if already uploaded
        """
        notebook = get_notebook()
        notes = notebook.list_notes(limit=10000)  # Get all notes
        
        print(f"Syncing {len(notes)} notes to assistant...")
        
        # Get existing file IDs
        existing_files = set()
        if not force and self.assistant:
            existing_files = set(self.assistant.file_ids)
        
        uploaded_count = 0
        for note in notes:
            # Skip if already uploaded (unless force)
            if not force and any(note.id[:8] in file_id for file_id in existing_files):
                continue
            
            file_id = self._upload_note_file(note)
            if file_id:
                uploaded_count += 1
                print(f"  ✓ Uploaded: {note.entity_type} - {note.title}")
        
        if uploaded_count > 0:
            # Update assistant with new files
            self._update_assistant_files()
            print(f"✓ Synced {uploaded_count} new notes to assistant")
        else:
            print("✓ All notes already synced")
    
    def _update_assistant_files(self):
        """Update assistant with current file list."""
        # Get all file IDs from the assistant
        assistant = self.client.assistants.retrieve(self.assistant_id)
        file_ids = assistant.file_ids
        
        # Update assistant with current files
        self.assistant = self.client.assistants.update(
            self.assistant_id,
            file_ids=file_ids
        )
    
    def create_thread(self) -> str:
        """
        Create a new conversation thread.
        
        Returns:
            Thread ID
        """
        thread = self.client.threads.create()
        self.thread_id = thread.id
        return self.thread_id
    
    def send_message(self, message: str, thread_id: Optional[str] = None) -> str:
        """
        Send a message to the assistant and get response.
        
        Args:
            message: The message to send
            thread_id: Thread ID (creates new if not provided)
            
        Returns:
            Assistant's response
        """
        if not thread_id:
            thread_id = self.create_thread()
        else:
            self.thread_id = thread_id
        
        # Add message to thread
        self.client.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        
        # Run assistant
        run = self.client.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant_id
        )
        
        # Wait for completion
        while run.status in ['queued', 'in_progress']:
            run = self.client.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
        
        if run.status == 'completed':
            # Get response
            messages = self.client.threads.messages.list(thread_id=thread_id)
            for msg in messages.data:
                if msg.role == 'assistant':
                    return msg.content[0].text.value
        else:
            raise Exception(f"Assistant run failed with status: {run.status}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get assistant status information.
        
        Returns:
            Dictionary with assistant status
        """
        if not self.assistant:
            return {'status': 'not_initialized'}
        
        try:
            assistant = self.client.assistants.retrieve(self.assistant_id)
            return {
                'assistant_id': self.assistant_id,
                'name': assistant.name,
                'model': assistant.model,
                'file_count': len(assistant.file_ids),
                'created_at': assistant.created_at,
                'last_updated': assistant.updated_at
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}


# Global assistant instance
_assistant_instance = None

def get_assistant(api_key: Optional[str] = None) -> NotebookAssistant:
    """
    Get or create the global assistant instance.
    
    Args:
        api_key: OpenAI API key (only used for first creation)
        
    Returns:
        NotebookAssistant instance
    """
    global _assistant_instance
    if _assistant_instance is None:
        _assistant_instance = NotebookAssistant(api_key)
    return _assistant_instance
