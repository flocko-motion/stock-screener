"""
Unit tests for AI assistant functionality.
"""

import unittest
import yaml
import json
from pathlib import Path
from datetime import datetime
import time

from fins.notebook.assistant import NotebookAssistant, get_assistant
from fins.entities.note import Fact, Observation
from fins.config import PATH_ASSISTANT_CONFIG, get_openai_api_key


class TestNotebookAssistant(unittest.TestCase):
    """Test cases for NotebookAssistant class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Load API key from config
        self.api_key = get_openai_api_key()
        if not self.api_key:
            self.skipTest("No API key found. Add your OpenAI API key to ~/.fins/config/assistant.yaml")
    
    def tearDown(self):
        """Clean up after tests."""
        pass  # No cleanup needed in testing mode
    
    def test_assistant_initialization(self):
        """Test assistant initialization."""
        assistant = NotebookAssistant(api_key=self.api_key, testing_mode=True)
        
        self.assertEqual(assistant.api_key, self.api_key)
        self.assertIsNotNone(assistant.assistant_id)
        self.assertIsNotNone(assistant.assistant)
        self.assertTrue(assistant.assistant_id.startswith('asst_'))
    
    def test_load_existing_assistant(self):
        """Test loading an existing assistant from config."""
        # Create an assistant first
        assistant1 = NotebookAssistant(api_key=self.api_key, testing_mode=True)
        assistant_id = assistant1.assistant_id
        
        # Now load it normally (not in testing mode)
        assistant2 = NotebookAssistant(api_key=self.api_key)
        
        # Should be the same assistant
        self.assertEqual(assistant2.assistant_id, assistant_id)
    
    def test_upload_note_file(self):
        """Test uploading a note as a file to the assistant."""
        assistant = NotebookAssistant(api_key=self.api_key, testing_mode=True)
        
        # Create a test note
        note = Fact("Test fact", "This is a test fact", source="Test source")
        
        file_id = assistant._upload_note_file(note)
        
        self.assertIsNotNone(file_id)
        self.assertTrue(file_id.startswith('file_'))
    
    def test_sync_notes(self):
        """Test syncing notes to the assistant."""
        assistant = NotebookAssistant(api_key=self.api_key, testing_mode=True)
        
        # Create test notes and save them to the notebook
        from fins.notebook import get_notebook
        notebook = get_notebook()
        
        note1 = Fact("Test fact 1", "First test fact")
        note2 = Observation("Test observation", "Test observation content")
        
        # Save notes to notebook
        notebook.save(note1)
        notebook.save(note2)
        
        # Sync notes to assistant
        assistant.sync_notes()
        
        # Verify assistant has files
        status = assistant.get_status()
        self.assertGreaterEqual(status['file_count'], 2)
    
    def test_send_message(self):
        """Test sending a message to the assistant."""
        assistant = NotebookAssistant(api_key=self.api_key, testing_mode=True)
        
        response = assistant.send_message("Hello")
        
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
    
    def test_get_status(self):
        """Test getting assistant status."""
        assistant = NotebookAssistant(api_key=self.api_key, testing_mode=True)
        status = assistant.get_status()
        
        self.assertIn('assistant_id', status)
        self.assertIn('name', status)
        self.assertIn('model', status)
        self.assertIn('file_count', status)
        self.assertEqual(status['assistant_id'], assistant.assistant_id)


class TestGetAssistant(unittest.TestCase):
    """Test cases for get_assistant function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.api_key = get_openai_api_key()
        if not self.api_key:
            self.skipTest("No API key found. Add your OpenAI API key to ~/.fins/config/assistant.yaml")
    
    def test_get_assistant_singleton(self):
        """Test that get_assistant returns the same instance."""
        # Import and reset the global instance
        import fins.notebook.assistant
        fins.notebook.assistant._assistant_instance = None
        
        assistant1 = get_assistant()
        assistant2 = get_assistant()
        
        self.assertIs(assistant1, assistant2)
        self.assertIsNotNone(assistant1.assistant_id)


if __name__ == '__main__':
    unittest.main() 