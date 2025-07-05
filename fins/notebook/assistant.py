"""
OpenAI Assistant Integration for Notebook

This module provides integration with OpenAI's Assistant API to create an AI assistant
that can access and analyze all notes in the notebook system.
"""

from io import BytesIO
from typing import Optional, Dict, Any, List
from datetime import datetime
from openai import OpenAI
from openai.types.beta import FileSearchToolParam
from openai.types.beta.assistant import ToolResources, ToolResourcesFileSearch

from fins.config import get_openai_api_key, get_assistant_config, set_assistant_config
from fins.entities import Note
from fins.notebook import notebook, Notebook

base_instructions = """You are a financial analysis assistant of FINS (Financial Intelligence and Notebook System), 
a unique analysis and financial strategy tool to analyze markets. Part of the system is a comprehensive notebook of market observations, trades, facts, and strategies of the user.

Your knowledge base includes:
- Market observations and insights
- Trading records and analysis
- Factual information about companies and markets
- Investment strategies and principles
- Symbol-specific notes and analysis

When analyzing or responding:
1. Always reference specific notes when relevant and explicity state the note id, type and date
2. Provide context from the notebook data
3. Be precise about dates, symbols, and financial data
4. Suggest connections between different notes
5. Help identify patterns or insights across the data

Always cite your sources from the notebook when making claims or providing analysis."""

class NotebookAssistant:
    """
    OpenAI Assistant integration for the FINS notebook system.
    
    Manages assistant creation, file uploads, and state persistence.
    Uses file search approach with comprehensive file uploads.
    """

    def __init__(self):
        """
        Initialize the notebook assistant.
        
        Args:
            api_key: OpenAI API key (will be loaded from config if not provided)
        """
        self.api_key = get_openai_api_key()
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set it in assistant.yaml config file.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.assistant_id = None
        self.assistant = None
        self.thread_id = None

        self._vector_store = None

        # Load or create assistant
        self._load_or_create_assistant()



    def _load_or_create_assistant(self):
        """Load existing assistant or create a new one."""

        # Try to load existing assistant ID
        assistant_id = get_assistant_config('assistant_id')
        
        if assistant_id:
            try:
                self.assistant = self.client.beta.assistants.retrieve(assistant_id)
                self.assistant_id = assistant_id
                self.assistant = self.client.beta.assistants.update(
                    assistant_id=self.assistant_id,
                    instructions=base_instructions,
                )
                print(f"✓ Loaded existing assistant: {assistant_id}")
                return
            except Exception as e:
                print(f"⚠ Failed to load assistant {assistant_id}: {e}")
        
        self._create_assistant()


    
    def _create_assistant(self):
        """Create a new OpenAI assistant."""
        self.assistant = self.client.beta.assistants.create(
            name="FINS Financial Assistant",
            instructions=base_instructions,
            model="gpt-4o",
            tools=[FileSearchToolParam(type="file_search"),],
        )

        self.assistant_id = self.assistant.id
        if not Notebook.is_test_mode():
            set_assistant_config("assistant_id", self.assistant_id)
        print(f"✓ Created new assistant: {self.assistant_id}")


    def vector_store(self):
        if self._vector_store is not None:
            return self._vector_store
        if Notebook.is_test_mode():
            self._vector_store = self.client.vector_stores.create(name="FINS Notes Test")
        else:
            vector_store_id = get_assistant_config("vector_store")
            if vector_store_id:
                self._vector_store = self.client.vector_stores.retrieve(vector_store_id)
            else:
                self._vector_store = self.client.vector_stores.create(name="FINS Notes")
                set_assistant_config("vector_store", self._vector_store.id)

        # Update assistant to use the vector store
        self.assistant = self.client.beta.assistants.update(
            assistant_id=self.assistant_id,
            tool_resources=ToolResources(file_search=ToolResourcesFileSearch(vector_store_ids=[self._vector_store.id]))
        )

        return self._vector_store

    def sync_notes(self, force: bool = False):
        """
        Sync all notes to the assistant using file search approach.
        This should be done at startup.
        
        Args:
            force: If True, re-upload all notes even if already uploaded
        """
        vector_store = self.vector_store()

        notes = notebook().list_notes(limit=10000)
        vs_file_ids_local = set()
        for note in notes:
            if note.vector_store_file_id is None:
                res = self.client.vector_stores.files.upload(vector_store_id=vector_store.id, file=(note.id + ".json", BytesIO(note.to_ai_note())))
                note.vector_store_file_id = res.id
                vs_file_ids_local.add(res.id)

        vs_files = self.client.vector_stores.files.list(vector_store_id=vector_store.id)
        vs_file_ids_online = set([d.id for d in vs_files.data])

        vs_file_ids_delete = vs_file_ids_online - vs_file_ids_local
        vs_file_ids_attach = vs_file_ids_local - vs_file_ids_local

        for vs_file_id in vs_file_ids_delete:
            res = self.client.vector_stores.files.delete(vector_store_id=vector_store.id, file_id=vs_file_id)
            if res.deleted:
                print(f"Sync: deleted note {vs_file_id}")
        for vs_file_id in vs_file_ids_attach:
            res = self.client.vector_stores.files.create(vector_store_id=vector_store.id, file_id=vs_file_id)

        print("✓ Notes are now available for file search")

    def sync_note(self, note: Note):
        """ sync a single to vector storage - this will modify the vector store file id! save not to db after this action"""
        vector_store = self.vector_store()

        if note.vector_store_file_id is not None:
            res = self.client.vector_stores.files.delete(vector_store_id=vector_store.id, file_id=note.vector_store_file_id)
            if res.deleted:
                print(f"✓ Deleted old version of Note from vector store")

        res = self.client.vector_stores.files.upload(vector_store_id=vector_store.id, file=(note.id + ".json", BytesIO(note.to_ai_note())))
        note.vector_store_file_id = res.id
        print("✓ Note uploaded to vector store")

    def create_thread(self) -> str:
        """
        Create a new conversation thread.
        
        Returns:
            Thread ID
        """
        thread = self.client.beta.threads.create()
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
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        
        # Run assistant
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant_id
        )
        
        # Wait for completion
        while run.status in ['queued', 'in_progress']:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
        
        if run.status == 'completed':
            # Get response
            messages = self.client.beta.threads.messages.list(thread_id=thread_id)
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
            assistant = self.client.beta.assistants.retrieve(self.assistant_id)
            return {
                'assistant_id': self.assistant_id,
                'name': assistant.name,
                'model': assistant.model,
                'created_at': datetime.fromtimestamp(assistant.created_at).isoformat(),
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}


# Global assistant instance
_assistant_instance = None

def assistant() -> NotebookAssistant:
    """
    Get or create the global assistant instance.
    
    Args:
        api_key: OpenAI API key (only used for first creation)
        
    Returns:
        NotebookAssistant instance
    """
    global _assistant_instance
    if _assistant_instance is None:
        _assistant_instance = NotebookAssistant()
    return _assistant_instance
