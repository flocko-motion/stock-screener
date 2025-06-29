#!/usr/bin/env python
"""
Tests for terminal persistence functions.

This module contains unit tests for the terminal persistence system,
testing Get, Put, Dir, and Delete functions for entity management.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys

# Add the parent directory to the path to allow imports from the fins package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fins.terminal.persistence import Get, Put, Dir, Delete, _storage
from fins.entities.basket import Basket
from fins.entities.basket_item import BasketItem
from fins.entities.note import Note, Observation, Fact
from fins.storage import Storage
from fins.terminal.symbols import AAPL, MSFT, GOOGL, NFLX


class TerminalPersistenceTests(unittest.TestCase):
    """Test cases for terminal persistence functions."""

    def setUp(self):
        """Set up test fixtures with temporary storage."""
        # Create temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        
        # Replace the global storage with test storage
        import fins.terminal.persistence as persistence_module
        self.original_storage = persistence_module._storage
        persistence_module._storage = Storage(self.test_dir)
        
        # Update the module-level _storage reference
        global _storage
        _storage = persistence_module._storage

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original storage
        import fins.terminal.persistence as persistence_module
        persistence_module._storage = self.original_storage
        
        # Clean up temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_put_and_get_basket(self):
        """Test saving and loading a basket."""
        # Create test basket
        basket = Basket(AAPL * 1.0, MSFT * 0.5, GOOGL * 2.0, name='test_basket')
        
        # Test Put
        success = Put(basket, 'portfolios/tech_stocks', silent=True)
        self.assertTrue(success)
        
        # Test Get
        loaded_basket = Get('portfolios/tech_stocks.Basket', silent=True)
        self.assertIsNotNone(loaded_basket)
        self.assertEqual(loaded_basket._name, 'test_basket')
        self.assertEqual(len(loaded_basket._items), 3)
        
        # Check individual items
        tickers = [item.ticker for item in loaded_basket._items]
        weights = [item.amount for item in loaded_basket._items]
        self.assertIn('AAPL', tickers)
        self.assertIn('MSFT', tickers)
        self.assertIn('GOOGL', tickers)
        self.assertIn(1.0, weights)
        self.assertIn(0.5, weights)
        self.assertIn(2.0, weights)

    def test_put_and_get_note(self):
        """Test saving and loading a note."""
        # Create test note
        note = Note(
            title="Apple Analysis",
            content="Apple is showing strong fundamentals with growing services revenue.",
            tags=["analysis", "tech"]
        )
        
        # Test Put
        success = Put(note, 'research/apple_analysis', silent=True)
        self.assertTrue(success)
        
        # Test Get
        loaded_note = Get('research/apple_analysis.Note', silent=True)
        self.assertIsNotNone(loaded_note)
        self.assertEqual(loaded_note.title, "Apple Analysis")
        self.assertIn("Apple is showing strong fundamentals", loaded_note.content)
        self.assertIn("analysis", loaded_note.tags)
        self.assertIn("tech", loaded_note.tags)

    def test_put_and_get_observation(self):
        """Test saving and loading an observation."""
        # Create test observation
        obs = Observation(
            title="Market Volatility",
            content="High volatility observed in tech sector today.",
            tags=["market", "volatility"]
        )
        
        # Test Put
        success = Put(obs, 'observations/market_vol_20241201', silent=True)
        self.assertTrue(success)
        
        # Test Get
        loaded_obs = Get('observations/market_vol_20241201.Observation', silent=True)
        self.assertIsNotNone(loaded_obs)
        self.assertEqual(loaded_obs.title, "Market Volatility")
        self.assertIn("High volatility", loaded_obs.content)

    def test_put_and_get_fact(self):
        """Test saving and loading a fact."""
        # Create test fact
        fact = Fact(
            title="Tesla Founding",
            content="Elon Musk did not found Tesla, he joined as an investor.",
            source="Wikipedia",
            confidence=0.95
        )
        
        # Test Put
        success = Put(fact, 'facts/tesla_founding', silent=True)
        self.assertTrue(success)
        
        # Test Get
        loaded_fact = Get('facts/tesla_founding.Fact', silent=True)
        self.assertIsNotNone(loaded_fact)
        self.assertEqual(loaded_fact.title, "Tesla Founding")
        self.assertEqual(loaded_fact.source, "Wikipedia")
        self.assertEqual(loaded_fact.confidence, 0.95)

    def test_automatic_extension_addition(self):
        """Test that entity class names are automatically added as extensions."""
        basket = Basket(AAPL * 1.0, name='test')
        
        # Put without extension
        Put(basket, 'test/basket_no_ext', silent=True)
        
        # Should be able to get with extension
        loaded = Get('test/basket_no_ext.Basket', silent=True)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded._name, 'test')

    def test_dir_listing(self):
        """Test directory listing functionality."""
        # Create test entities
        basket1 = Basket(AAPL * 1.0, name='basket1')
        basket2 = Basket(MSFT * 1.0, name='basket2')
        
        note = Note("Test Note", "Content")
        
        # Put entities in different directories
        Put(basket1, 'portfolios/growth/basket1', silent=True)
        Put(basket2, 'portfolios/value/basket2', silent=True)
        Put(note, 'research/notes/test_note', silent=True)
        
        # Test root directory listing
        root_items = Dir(silent=True)
        self.assertIn('portfolios/', root_items)
        self.assertIn('research/', root_items)
        
        # Test portfolios directory
        portfolio_items = Dir('portfolios', silent=True)
        self.assertIn('growth/', portfolio_items)
        self.assertIn('value/', portfolio_items)
        
        # Test specific subdirectory
        growth_items = Dir('portfolios/growth', silent=True)
        self.assertIn('basket1.Basket', growth_items)
        
        # Test research directory
        research_items = Dir('research', silent=True)
        self.assertIn('notes/', research_items)
        
        notes_items = Dir('research/notes', silent=True)
        self.assertIn('test_note.Note', notes_items)

    def test_dir_recursive_listing(self):
        """Test recursive directory listing functionality."""
        # Create test entities in nested structure
        basket1 = Basket(AAPL * 1.0, name='growth_basket')
        basket2 = Basket(MSFT * 1.0, name='value_basket')
        note1 = Note("Tech Analysis", "Content about tech")
        note2 = Note("Market Overview", "General market content")
        fact = Fact("Important Fact", "Some factual content")
        
        # Put entities in nested directories
        Put(basket1, 'strategies/equity/growth/momentum_strategy', silent=True)
        Put(basket2, 'strategies/equity/value/deep_value_strategy', silent=True)
        Put(note1, 'research/sectors/technology/analysis', silent=True)
        Put(note2, 'research/market/overview', silent=True)
        Put(fact, 'facts/market/structure', silent=True)
        
        # Test recursive listing from root
        all_items = Dir(recursive=True, silent=True)
        expected_items = [
            'strategies/equity/growth/momentum_strategy.Basket',
            'strategies/equity/value/deep_value_strategy.Basket',
            'research/sectors/technology/analysis.Note',
            'research/market/overview.Note',
            'facts/market/structure.Fact'
        ]
        for item in expected_items:
            self.assertIn(item, all_items)
        
        # Test recursive listing from specific directory
        research_items = Dir('research', recursive=True, silent=True)
        self.assertIn('sectors/technology/analysis.Note', research_items)
        self.assertIn('market/overview.Note', research_items)
        
        # Test recursive listing from deeper directory
        strategies_items = Dir('strategies', recursive=True, silent=True)
        self.assertIn('equity/growth/momentum_strategy.Basket', strategies_items)
        self.assertIn('equity/value/deep_value_strategy.Basket', strategies_items)

    def test_delete_single_entity(self):
        """Test deleting a single entity."""
        # Create and save entity
        basket = Basket(AAPL * 1.0, name='to_delete')
        Put(basket, 'temp/delete_me', silent=True)
        
        # Verify it exists
        loaded = Get('temp/delete_me.Basket', silent=True)
        self.assertIsNotNone(loaded)
        
        # Delete it
        success = Delete('temp/delete_me.Basket', silent=True)
        self.assertTrue(success)
        
        # Verify it's gone
        loaded_after = Get('temp/delete_me.Basket', silent=True)
        self.assertIsNone(loaded_after)

    def test_delete_directory_requires_force(self):
        """Test that deleting directories with contents requires force=True."""
        # Create entities in a directory
        basket = Basket(AAPL * 1.0, name='test')
        note = Note("Test", "Content")
        
        Put(basket, 'temp_dir/basket', silent=True)
        Put(note, 'temp_dir/note', silent=True)
        
        # Try to delete directory without force - should fail
        with self.assertRaises(ValueError) as context:
            Delete('temp_dir', silent=True)
        self.assertIn("Use force=True", str(context.exception))
        
        # Delete with force should work
        success = Delete('temp_dir', force=True, silent=True)
        self.assertTrue(success)
        
        # Verify directory is empty
        items = Dir('temp_dir', silent=True)
        self.assertEqual(len(items), 0)

    def test_get_nonexistent_entity(self):
        """Test getting a non-existent entity returns None."""
        result = Get('nonexistent/entity', silent=True)
        self.assertIsNone(result)

    def test_put_invalid_entity_type(self):
        """Test putting a non-entity object raises TypeError."""
        with self.assertRaises(TypeError):
            Put("not an entity", 'invalid/path', silent=True)
        
        with self.assertRaises(TypeError):
            Put(123, 'invalid/path', silent=True)
        
        with self.assertRaises(TypeError):
            Put({'key': 'value'}, 'invalid/path', silent=True)

    def test_path_normalization(self):
        """Test that paths are properly normalized."""
        basket = Basket(AAPL * 1.0, name='test')
        
        # Put with various path formats
        Put(basket, 'test_path', silent=True)  # No leading slash
        Put(basket, '/absolute_path', silent=True)  # With leading slash
        
        # Should be able to get with either format
        loaded1 = Get('test_path.Basket', silent=True)
        loaded2 = Get('/absolute_path.Basket', silent=True)
        
        self.assertIsNotNone(loaded1)
        self.assertIsNotNone(loaded2)

    def test_complex_directory_structure(self):
        """Test creating and navigating complex directory structures."""
        # Create entities in nested directories
        entities = [
            (Basket(NFLX * 1.0, name='growth'), 'strategies/equity/growth/momentum'),
            (Basket(NFLX * 1.0, name='value'), 'strategies/equity/value/deep_value'),
            (Note("Bond Analysis", "Content"), 'strategies/fixed_income/analysis'),
            (Fact("Market Fact", "Content"), 'research/facts/market_structure'),
        ]
        
        for entity, path in entities:
            success = Put(entity, path, silent=True)
            self.assertTrue(success)
        
        # Test navigation
        strategies = Dir('strategies', silent=True)
        self.assertIn('equity/', strategies)
        self.assertIn('fixed_income/', strategies)
        
        equity = Dir('strategies/equity', silent=True)
        self.assertIn('growth/', equity)
        self.assertIn('value/', equity)
        
        growth = Dir('strategies/equity/growth', silent=True)
        self.assertIn('momentum.Basket', growth)
        
        # Test retrieval
        loaded_momentum = Get('strategies/equity/growth/momentum.Basket', silent=True)
        self.assertIsNotNone(loaded_momentum)
        self.assertEqual(loaded_momentum._name, 'growth')

    def test_basket_with_description(self):
        """Test saving and loading baskets with descriptions."""
        basket = Basket(AAPL * 1.0, name='described_basket')
        basket.description('This is a test basket with a description')
        
        Put(basket, 'described/basket', silent=True)
        
        loaded = Get('described/basket.Basket', silent=True)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.description(), 'This is a test basket with a description')


if __name__ == '__main__':
    unittest.main() 