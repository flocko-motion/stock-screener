"""
Unit tests for AI assistant functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import yaml
import json
from pathlib import Path
from datetime import datetime

from fins.notebook.assistant import NotebookAssistant, get_assistant
from fins.entities.note import Fact, Observation
from fins.config import PATH_ASSISTANT_CONFIG


class TestNotebookAssistant(unittest.TestCase):
    """Test cases for NotebookAssistant class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Try to load API key from config, fallback to test key
        self.test_api_key = "sk-test-key-12345"
        if PATH_ASSISTANT_CONFIG.exists():
            try:
                with open(PATH_ASSISTANT_CONFIG, 'r') as f:
                    config = yaml.safe_load(f) or {}
                    if config.get('api_key'):
                        self.test_api_key = config['api_key']
            except Exception:
                pass  # Use test key if config loading fails
        
        self.test_assistant_id = "asst_test123"
        
        # Mock config file
        self.config_data = {
            'api_key': self.test_api_key,
            'assistant_id': self.test_assistant_id,
            'last_updated': datetime.now().isoformat()
        }
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove test config file if it exists
        if PATH_ASSISTANT_CONFIG.exists():
            PATH_ASSISTANT_CONFIG.unlink()
    
    @patch('fins.notebook.assistant.OpenAI')
    def test_assistant_initialization_with_api_key(self, mock_openai):
        """Test assistant initialization with provided API key."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        assistant = NotebookAssistant(api_key=self.test_api_key)
        
        self.assertEqual(assistant.api_key, self.test_api_key)
        mock_openai.assert_called_once_with(api_key=self.test_api_key)
    
    @patch('fins.notebook.assistant.OpenAI')
    @patch('builtins.open')
    def test_assistant_initialization_from_config(self, mock_open, mock_openai):
        """Test assistant initialization loading API key from config file."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock config file
        mock_file = Mock()
        mock_file.read.return_value = yaml.dump(self.config_data)
        mock_open.return_value.__enter__.return_value = mock_file
        
        assistant = NotebookAssistant()
        
        self.assertEqual(assistant.api_key, self.test_api_key)
    
    @patch('fins.notebook.assistant.OpenAI')
    def test_assistant_initialization_no_api_key(self, mock_openai):
        """Test assistant initialization fails without API key."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Ensure no config file exists for this test
        if PATH_ASSISTANT_CONFIG.exists():
            PATH_ASSISTANT_CONFIG.unlink()
        
        with self.assertRaises(ValueError, msg="OpenAI API key is required"):
            NotebookAssistant()
    
    @patch('fins.notebook.assistant.OpenAI')
    def test_assistant_initialization_with_real_config(self, mock_openai):
        """Test assistant initialization with real config file."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Create a real config file for this test
        PATH_ASSISTANT_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        with open(PATH_ASSISTANT_CONFIG, 'w') as f:
            yaml.dump(self.config_data, f)
        
        assistant = NotebookAssistant()
        
        self.assertEqual(assistant.api_key, self.test_api_key)
        mock_openai.assert_called_once_with(api_key=self.test_api_key)
    
    @patch('fins.notebook.assistant.OpenAI')
    def test_create_new_assistant(self, mock_openai):
        """Test creating a new assistant when none exists."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock assistant creation
        mock_assistant = Mock()
        mock_assistant.id = self.test_assistant_id
        mock_client.beta.assistants.create.return_value = mock_assistant
        
        assistant = NotebookAssistant(api_key=self.test_api_key)
        
        # Verify assistant was created
        mock_client.beta.assistants.create.assert_called_once()
        call_args = mock_client.beta.assistants.create.call_args
        self.assertEqual(call_args[1]['name'], "FINS Financial Assistant")
        self.assertEqual(call_args[1]['model'], "gpt-4-turbo-preview")
        self.assertEqual(call_args[1]['tools'], [{"type": "file_search"}])
        
        self.assertEqual(assistant.assistant_id, self.test_assistant_id)
    
    @patch('fins.notebook.assistant.OpenAI')
    def test_load_existing_assistant(self, mock_openai):
        """Test loading an existing assistant from config."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock existing assistant
        mock_assistant = Mock()
        mock_assistant.id = self.test_assistant_id
        mock_client.beta.assistants.retrieve.return_value = mock_assistant
        
        # Create config file
        PATH_ASSISTANT_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        with open(PATH_ASSISTANT_CONFIG, 'w') as f:
            yaml.dump(self.config_data, f)
        
        assistant = NotebookAssistant(api_key=self.test_api_key)
        
        # Verify existing assistant was loaded
        mock_client.beta.assistants.retrieve.assert_called_once_with(self.test_assistant_id)
        self.assertEqual(assistant.assistant_id, self.test_assistant_id)
    
    @patch('fins.notebook.assistant.OpenAI')
    def test_upload_note_file(self, mock_openai):
        """Test uploading a note as a file to the assistant."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock file upload
        mock_file = Mock()
        mock_file.id = "file_test123"
        mock_client.files.create.return_value = mock_file
        
        assistant = NotebookAssistant(api_key=self.test_api_key)
        
        # Create a test note
        note = Fact("Test fact", "This is a test fact", source="Test source")
        
        file_id = assistant._upload_note_file(note)
        
        self.assertEqual(file_id, "file_test123")
        mock_client.files.create.assert_called_once()
    
    @patch('fins.notebook.assistant.OpenAI')
    @patch('fins.notebook.assistant.get_notebook')
    def test_sync_notes(self, mock_get_notebook, mock_openai):
        """Test syncing notes to the assistant."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock assistant with existing files
        mock_assistant = Mock()
        mock_assistant.file_ids = ["file_existing"]
        mock_client.beta.assistants.retrieve.return_value = mock_assistant
        mock_client.beta.assistants.update.return_value = mock_assistant
        
        # Mock file upload
        mock_file = Mock()
        mock_file.id = "file_new"
        mock_client.files.create.return_value = mock_file
        
        # Mock notebook
        mock_notebook = Mock()
        mock_get_notebook.return_value = mock_notebook
        
        # Create test notes
        note1 = Fact("Test fact 1", "First test fact")
        note2 = Observation("Test observation", "Test observation content")
        mock_notebook.list_notes.return_value = [note1, note2]
        
        assistant = NotebookAssistant(api_key=self.test_api_key)
        assistant.sync_notes()
        
        # Verify notes were processed
        self.assertEqual(mock_client.files.create.call_count, 2)
        mock_client.beta.assistants.update.assert_called_once()
    
    @patch('fins.notebook.assistant.OpenAI')
    def test_send_message(self, mock_openai):
        """Test sending a message to the assistant."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock thread creation
        mock_thread = Mock()
        mock_thread.id = "thread_test123"
        mock_client.beta.threads.create.return_value = mock_thread
        
        # Mock run
        mock_run = Mock()
        mock_run.status = "completed"
        mock_client.beta.threads.runs.create.return_value = mock_run
        mock_client.beta.threads.runs.retrieve.return_value = mock_run
        
        # Mock message response
        mock_message = Mock()
        mock_message.role = "assistant"
        mock_message.content = [Mock()]
        mock_message.content[0].text.value = "Hello! How can I help you?"
        mock_client.beta.threads.messages.list.return_value = Mock(data=[mock_message])
        
        assistant = NotebookAssistant(api_key=self.test_api_key)
        response = assistant.send_message("Hello")
        
        self.assertEqual(response, "Hello! How can I help you?")
        mock_client.beta.threads.messages.create.assert_called_once()
        mock_client.beta.threads.runs.create.assert_called_once()
    
    @patch('fins.notebook.assistant.OpenAI')
    def test_get_status(self, mock_openai):
        """Test getting assistant status."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock assistant
        mock_assistant = Mock()
        mock_assistant.id = self.test_assistant_id
        mock_assistant.name = "Test Assistant"
        mock_assistant.model = "gpt-4-turbo-preview"
        mock_assistant.file_ids = ["file1", "file2"]
        mock_assistant.created_at = "2024-01-01T00:00:00Z"
        mock_assistant.updated_at = "2024-01-02T00:00:00Z"
        mock_client.beta.assistants.retrieve.return_value = mock_assistant
        
        assistant = NotebookAssistant(api_key=self.test_api_key)
        status = assistant.get_status()
        
        expected_status = {
            'assistant_id': self.test_assistant_id,
            'name': "Test Assistant",
            'model': "gpt-4-turbo-preview",
            'file_count': 2,
            'created_at': "2024-01-01T00:00:00Z",
            'last_updated': "2024-01-02T00:00:00Z"
        }
        
        self.assertEqual(status, expected_status)


class TestGetAssistant(unittest.TestCase):
    """Test cases for get_assistant function."""
    
    @patch('fins.notebook.assistant.NotebookAssistant')
    def test_get_assistant_singleton(self, mock_assistant_class):
        """Test that get_assistant returns the same instance."""
        mock_assistant = Mock()
        mock_assistant_class.return_value = mock_assistant
        
        # Import and reset the global instance
        import fins.notebook.assistant
        fins.notebook.assistant._assistant_instance = None
        
        assistant1 = get_assistant()
        assistant2 = get_assistant()
        
        self.assertIs(assistant1, assistant2)
        mock_assistant_class.assert_called_once()


if __name__ == '__main__':
    unittest.main() 