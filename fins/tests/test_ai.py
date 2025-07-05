"""
Unit tests for AI assistant functionality.
"""
import time
import unittest

from fins.notebook import *
from fins.entities.note import Fact, Observation, NoteSymbol


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
    
    def test_assistant(self):
        a = NotebookAi()
        a.ask("what's in the news about markets?")
        a.ask("say that again in 4 words")

    def test_sync_notes(self):
        """Test syncing notes to the assistant."""

        # to have a clean start for our tests, delete all notes
        notebook().clear_all()

        a = NotebookAi()
        a.sync_notes()

        notes = [
            Fact("Test", "First test fact"),
            Observation("Test", "Test observation content"),
            NoteSymbol("ADP", "ADP is a pretty hot one - good for a winter portfolio")
        ]

        for note in notes:
            note.save(ai=a)

        # give some time for processing
        time.sleep(3)

        a.ask("What did I note about ADP?")

    def test_search(self):
        a = NotebookAi()
        res = a.search("ADP")




if __name__ == '__main__':
    unittest.main() 