"""
Tests for the SortCommand class.
"""

import pytest
from ..entities.basket import Basket
from ..entities.symbol import Symbol
from ..dsl.commands.sort import SortCommand

def create_test_basket():
    """Create a test basket with market cap and PE data."""
    symbols = [
        Symbol("AAPL", {"mcap": 2000, "pe": 15}),
        Symbol("MSFT", {"mcap": 3000, "pe": 10}),
        Symbol("GOOGL", {"mcap": 1500, "pe": 20})
    ]
    return Basket(symbols)

def test_sort_by_mcap_ascending():
    """Test sorting by market cap in ascending order."""
    basket = create_test_basket()
    cmd = SortCommand(column="mcap", order="asc")
    result = cmd.execute(basket)
    
    assert isinstance(result, Basket)
    assert [s.symbol for s in result.symbols] == ["GOOGL", "AAPL", "MSFT"]

def test_sort_by_mcap_descending():
    """Test sorting by market cap in descending order."""
    basket = create_test_basket()
    cmd = SortCommand(column="mcap", order="desc")
    result = cmd.execute(basket)
    
    assert isinstance(result, Basket)
    assert [s.symbol for s in result.symbols] == ["MSFT", "AAPL", "GOOGL"]

def test_sort_by_pe_ascending():
    """Test sorting by PE ratio in ascending order."""
    basket = create_test_basket()
    cmd = SortCommand(column="pe")  # Default order is asc
    result = cmd.execute(basket)
    
    assert isinstance(result, Basket)
    assert [s.symbol for s in result.symbols] == ["MSFT", "AAPL", "GOOGL"]

def test_sort_missing_column():
    """Test sorting with missing column parameter."""
    basket = create_test_basket()
    cmd = SortCommand()  # No column specified
    
    with pytest.raises(ValueError, match="Column must be specified"):
        cmd.execute(basket)

def test_sort_invalid_order():
    """Test sorting with invalid order parameter."""
    basket = create_test_basket()
    cmd = SortCommand(column="mcap", order="invalid")
    
    with pytest.raises(ValueError, match="Order must be 'asc' or 'desc'"):
        cmd.execute(basket)

def test_sort_invalid_input_type():
    """Test sorting with invalid input type."""
    cmd = SortCommand(column="mcap")
    
    with pytest.raises(TypeError):
        cmd.execute("not a basket")

def test_sort_nonexistent_column():
    """Test sorting by a column that doesn't exist."""
    basket = create_test_basket()
    cmd = SortCommand(column="nonexistent")
    result = cmd.execute(basket)
    
    # Should not raise, but sort by 0 (default) for missing values
    assert isinstance(result, Basket)
    assert len(result.symbols) == len(basket.symbols)

def test_help_text():
    """Test help text generation."""
    cmd = SortCommand()
    help_text = cmd.help()
    
    assert "Command: SortCommand" in help_text
    assert "Sort a basket by a specified column" in help_text
    assert "Input: Basket" in help_text
    assert "Output: Basket" in help_text
    assert "Parameters:" in help_text
    assert "column:" in help_text
    assert "order:" in help_text
    assert "Examples:" in help_text
    assert "sort mcap desc" in help_text 