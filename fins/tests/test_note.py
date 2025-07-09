"""
Unit tests for AI assistant functionality.
"""

import unittest
import re
from fins.entities.note import NoteSymbol
from fins.terminal import Notes
from fins.notebook import notebook


class TestNotebook(unittest.TestCase):

	def setUp(self):
		"""Set up test fixtures."""
		pass

	def tearDown(self):
		"""Clean up after tests."""
		pass  # No cleanup needed in testing mode

	def test_note_symbol(self):
		note = NoteSymbol("TEST", "not a bad choice")
		note.save()
		print(note.to_ai_note())
		res = Notes(symbol="TEST")
		print(res)

	def test_notes_search(self):
		res = Notes(symbol="V")
		print(res)

	def test_fix_missing_symbols(self):
		"""Find and fix NoteSymbol notes with missing symbol fields."""
		# Get all notes
		all_notes = notebook().list_notes(limit=1000)
		
		# Filter for NoteSymbol notes
		symbol_notes = [note for note in all_notes if note.entity_type == "symbol_note"]
		
		print(f"Found {len(symbol_notes)} NoteSymbol notes")
		
		fixed_count = 0
		for note in symbol_notes:
			# Check if symbol is missing
			if not note.symbol:
				# Extract ticker from title using regex
				# Look for patterns like "Note on AAPL", "AAPL analysis", etc.
				title = note.title
				
				# Try different patterns to extract ticker
				ticker = None
				
				# Pattern 1: "Note on TICKER"
				match = re.search(r'Note on ([A-Z]+)', title)
				if match:
					ticker = match.group(1)
				
				# Pattern 2: "TICKER - description" or "TICKER: description"
				if not ticker:
					match = re.search(r'^([A-Z]+)[\s\-:]', title)
					if match:
						ticker = match.group(1)
				
				# Pattern 3: "description for TICKER"
				if not ticker:
					match = re.search(r'for ([A-Z]+)', title)
					if match:
						ticker = match.group(1)
				
				# Pattern 4: Just look for any 2-5 letter uppercase sequence
				if not ticker:
					match = re.search(r'\b([A-Z]{2,5})\b', title)
					if match:
						ticker = match.group(1)
				
				if ticker:
					print(f"Fixing note '{note.title}' - extracted ticker: {ticker}")
					note.symbol = ticker
					note.save()
					fixed_count += 1
				else:
					print(f"Could not extract ticker from title: '{note.title}'")
		
		print(f"Fixed {fixed_count} notes with missing symbols")
		return fixed_count

if __name__ == '__main__':
	unittest.main()