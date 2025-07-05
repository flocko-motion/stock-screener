"""
Unit tests for AI assistant functionality.
"""

import unittest

from fins.entities.note import NoteSymbol


class TestNotebook(unittest.TestCase):

	def setUp(self):
		"""Set up test fixtures."""
		pass

	def tearDown(self):
		"""Clean up after tests."""
		pass  # No cleanup needed in testing mode

	def test_note_symbol(self):
		note = NoteSymbol("AAPL", "not a bad choice")
		ai_note = note.to_ai_note()
		print(ai_note)


if __name__ == '__main__':
	unittest.main()