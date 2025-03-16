"""
Unit tests for the FINS parser
"""

import unittest
# Import from the dsl package instead of directly
from fins.dsl import parser as fins_parser
from fins.dsl.parser import AstTransformer

class TestFinsParser(unittest.TestCase):
    
    def setUp(self):
        """Set up the transformer for tests"""
        self.transformer = AstTransformer()
    
    def test_symbol_parsing(self):
        """Test parsing of individual symbols"""
        # Test stock symbol
        parse_tree = fins_parser.parser.parse("AAPL")
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["type"], "command_chain")
        self.assertEqual(len(result["commands"]), 1)
        self.assertEqual(result["commands"][0]["type"], "basket")
        self.assertEqual(len(result["commands"][0]["symbols"]), 1)
        self.assertEqual(result["commands"][0]["symbols"][0]["ticker"], "AAPL")
        
        # Test index symbol
        parse_tree = fins_parser.parser.parse("^SPX")
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["commands"][0]["symbols"][0]["ticker"], "^SPX")
    
    def test_basket_creation(self):
        """Test creating a basket from multiple symbols"""
        parse_tree = fins_parser.parser.parse("AAPL MSFT GOOGL")
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["type"], "command_chain")
        self.assertEqual(len(result["commands"]), 1)
        self.assertEqual(result["commands"][0]["type"], "basket")
        
        symbols = result["commands"][0]["symbols"]
        self.assertEqual(len(symbols), 3)
        self.assertEqual(symbols[0]["ticker"], "AAPL")
        self.assertEqual(symbols[1]["ticker"], "MSFT")
        self.assertEqual(symbols[2]["ticker"], "GOOGL")
    
    def test_variable_parsing(self):
        """Test parsing of variables"""
        # Test non-persistent variable
        parse_tree = fins_parser.parser.parse("$A")
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["commands"][0]["type"], "variable")
        self.assertEqual(result["commands"][0]["name"], "$A")
        
        # Test persistent variable
        parse_tree = fins_parser.parser.parse("/MyBasket")
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["commands"][0]["name"], "/MyBasket")
        
        # Test nested persistent variable
        parse_tree = fins_parser.parser.parse("/tech/FAANG")
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["commands"][0]["name"], "/tech/FAANG")
    
    def test_set_operations(self):
        """Test set operations"""
        # Test union
        parse_tree = fins_parser.parser.parse("+ AAPL")
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["commands"][0]["type"], "command")
        self.assertEqual(result["commands"][0]["action"], "union")
        
        # Test difference
        parse_tree = fins_parser.parser.parse("- MSFT")
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["commands"][0]["action"], "difference")
        
        # Test intersection
        parse_tree = fins_parser.parser.parse("& GOOGL")
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["commands"][0]["action"], "intersection")
        
        # Test spread
        parse_tree = fins_parser.parser.parse("..VTI")
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["commands"][0]["action"], "spread")
    
    def test_sort_command(self):
        """Test sort command"""
        parse_tree = fins_parser.parser.parse("sort mcap desc")
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["commands"][0]["type"], "command")
        self.assertEqual(result["commands"][0]["action"], "sort")
        self.assertEqual(result["commands"][0]["attribute"], "mcap")
        self.assertEqual(result["commands"][0]["order"], "desc")
    
    def test_filter_command(self):
        """Test filter command"""
        parse_tree = fins_parser.parser.parse("mcap > 10000")
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["commands"][0]["type"], "command")
        self.assertEqual(result["commands"][0]["action"], "filter")
        self.assertEqual(result["commands"][0]["attribute"], "mcap")
        self.assertEqual(result["commands"][0]["operator"], ">")
        self.assertEqual(result["commands"][0]["value"], 10000.0)
        
        # Test with number shortcuts
        parse_tree = fins_parser.parser.parse("mcap > 10B")
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["commands"][0]["value"], 10000000000.0)
    
    def test_command_chain(self):
        """Test command chain with multiple commands"""
        parse_tree = fins_parser.parser.parse("AAPL MSFT -> + GOOGL -> sort mcap desc")
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["type"], "command_chain")
        self.assertEqual(len(result["commands"]), 3)
        
        # First command: basket creation
        self.assertEqual(result["commands"][0]["type"], "basket")
        self.assertEqual(len(result["commands"][0]["symbols"]), 2)
        
        # Second command: union operation
        self.assertEqual(result["commands"][1]["type"], "command")
        self.assertEqual(result["commands"][1]["action"], "union")
        
        # Third command: sort
        self.assertEqual(result["commands"][2]["type"], "command")
        self.assertEqual(result["commands"][2]["action"], "sort")
    
    def test_column_addition(self):
        """Test column addition commands"""
        # Test basic column addition
        parse_tree = fins_parser.parser.parse("cagr 10y")
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["commands"][0]["type"], "command")
        self.assertEqual(result["commands"][0]["action"], "add_column")
        self.assertEqual(result["commands"][0]["column_type"], "cagr")
        self.assertEqual(result["commands"][0]["period"], "10y")
        
        # Test with column naming
        parse_tree = fins_parser.parser.parse("|cagr10 cagr 10y")
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["commands"][0]["column_name"], "cagr10")
        self.assertEqual(result["commands"][0]["column_type"], "cagr")
        
        # Test with time range
        parse_tree = fins_parser.parser.parse("cagr [2010:2020] 5y")
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["commands"][0]["start_year"], 2010)
        self.assertEqual(result["commands"][0]["end_year"], 2020)
        self.assertEqual(result["commands"][0]["period"], "5y")
        
        # Test with column naming and time range
        parse_tree = fins_parser.parser.parse("|cagr_decade cagr [2010:2020]")
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["commands"][0]["column_name"], "cagr_decade")
        self.assertEqual(result["commands"][0]["start_year"], 2010)
        self.assertEqual(result["commands"][0]["end_year"], 2020)
    
    def test_info_command(self):
        """Test info command"""
        # Test info on symbol
        parse_tree = fins_parser.parser.parse(": AAPL")
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["commands"][0]["type"], "command")
        self.assertEqual(result["commands"][0]["action"], "info")
        self.assertEqual(result["commands"][0]["target"]["type"], "symbol")
        self.assertEqual(result["commands"][0]["target"]["ticker"], "AAPL")
        
        # Test info on variable
        parse_tree = fins_parser.parser.parse(": $A")
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["commands"][0]["action"], "info")
        self.assertEqual(result["commands"][0]["target"]["type"], "variable")
        self.assertEqual(result["commands"][0]["target"]["name"], "$A")
    
    def test_function_definition(self):
        """Test function definition"""
        parse_tree = fins_parser.parser.parse('DEFINE !HighCapCAGR = "mcap > 10000 -> cagr [2010:2020] 10y"')
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["type"], "function_definition")
        self.assertEqual(result["name"], "!HighCapCAGR")
        self.assertEqual(result["command"], "mcap > 10000 -> cagr [2010:2020] 10y")
    
    def test_variable_management(self):
        """Test variable locking and unlocking"""
        # Test lock command
        parse_tree = fins_parser.parser.parse("lock $A")
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["commands"][0]["type"], "command")
        self.assertEqual(result["commands"][0]["action"], "lock")
        self.assertEqual(result["commands"][0]["variable"], "$A")
        
        # Test unlock command
        parse_tree = fins_parser.parser.parse("unlock $A")
        result = self.transformer.transform(parse_tree)
        self.assertEqual(result["commands"][0]["action"], "unlock")
        self.assertEqual(result["commands"][0]["variable"], "$A")

if __name__ == "__main__":
    unittest.main() 