"""
Unit tests for AI assistant functionality.
"""

import unittest

from fins.notebook import *
from fins.entities.note import Fact, Observation


class TestNotebookAssistant(unittest.TestCase):
    """Test cases for NotebookAssistant class."""
    
    def setUp(self):
        """Set up test fixtures."""
        Notebook.test_mode = True
        pass

    def tearDown(self):
        """Clean up after tests."""
        Notebook.test_mode = False
        pass  # No cleanup needed in testing mode
    
    def test_assistant_initialization(self):
        self.assertIsNotNone(assistant().assistant_id)
        self.assertIsNotNone(assistant().assistant)
        self.assertTrue(assistant().assistant_id.startswith('asst_'))

    
    def test_sync_notes(self):
        """Test syncing notes to the assistant."""

        # Create test notes and save them to the notebook
        notebook().clear_all()
        assistant().sync_notes()

        note1 = Fact("Test", "First test fact")
        note2 = Observation("Test", "Test observation content")

        note1.save()
        note2.save()


        # Verify assistant has files
        status = assistant().get_status()
        print(status)

        notebook().delete(note1.id)
        notebook().delete(note2.id)
    
    def test_send_message(self):
        response = assistant().send_message("Hello")
        
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
    
    def test_get_status(self):
        status = assistant().get_status()
        
        self.assertIn('assistant_id', status)
        self.assertIn('name', status)
        self.assertIn('model', status)
        self.assertIn('file_count', status)
        self.assertEqual(status['assistant_id'], assistant().assistant_id)



if __name__ == '__main__':
    unittest.main() 