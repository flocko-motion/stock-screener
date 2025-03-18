"""
AST Transformer for FINS (Financial Insights Script)

This module contains the transformer that converts the parse tree to an abstract syntax tree (AST).
"""

from lark import Transformer

class AstTransformer(Transformer):
    def start(self, items):
        return items[0]

    def command_chain(self, items):
        return {"type": "command_chain", "commands": items}

    def sort_command(self, items):
        attribute, order = items
        return {"type": "command", "action": "sort", "attribute": str(attribute), "order": str(order)}

    def filter_command(self, items):
        attribute, operator, number = items
        return {"type": "command", "action": "filter", "attribute": str(attribute), "operator": str(operator), "value": self._parse_number(number)}

    def basket(self, items):
        return {"type": "basket", "symbols": items}

    def variable(self, items):
        return {"type": "variable", "name": str(items[0])}

    def symbol(self, items):
        return {"type": "symbol", "ticker": str(items[0])}

    def union_op(self, items):
        return {"type": "command", "action": "union", "operand": items[0]}

    def difference_op(self, items):
        return {"type": "command", "action": "difference", "operand": items[0]}

    def intersection_op(self, items):
        return {"type": "command", "action": "intersection", "operand": items[0]}

    def spread_op(self, items):
        return {"type": "command", "action": "spread", "symbol": items[0]}

    def set_operation(self, items):
        return items[0]

    def direct_operation(self, items):
        var, operation = items
        operation["basket"] = var
        return operation

    def direct_union(self, items):
        if isinstance(items[0], list):  # Multiple symbols
            return {"type": "command", "action": "union", "operand": {"type": "basket", "symbols": items[0]}}
        return {"type": "command", "action": "union", "operand": items[0]}

    def direct_difference(self, items):
        if isinstance(items[0], list):  # Multiple symbols
            return {"type": "command", "action": "difference", "operand": {"type": "basket", "symbols": items[0]}}
        return {"type": "command", "action": "difference", "operand": items[0]}

    def direct_intersection(self, items):
        if isinstance(items[0], list):  # Multiple symbols
            return {"type": "command", "action": "intersection", "operand": {"type": "basket", "symbols": items[0]}}
        return {"type": "command", "action": "intersection", "operand": items[0]}
    
    def column_command(self, items):
        result = {"type": "command", "action": "add_column"}
        
        # Process each item based on its type
        for item in items:
            if isinstance(item, dict):
                if item.get("type") == "column_name":
                    result["column_name"] = item.get("name")
                elif item.get("type") == "column_type":
                    result["column_type"] = item.get("name")
                elif item.get("type") == "time_range":
                    result["start_year"] = item.get("start_year")
                    result["end_year"] = item.get("end_year")
                elif item.get("type") == "period":
                    result["period"] = item.get("value")
        
        return result
    
    def column_name(self, items):
        return {"type": "column_name", "name": str(items[0])}
    
    def column_type(self, items):
        if not items:
            return {"type": "column_type", "name": ""}
        return {"type": "column_type", "name": str(items[0])}
    
    def time_range(self, items):
        start_year, end_year = items
        return {"type": "time_range", "start_year": int(start_year), "end_year": int(end_year)}
    
    def period(self, items):
        period_str = str(items[0])
        return {"type": "period", "value": period_str}
    
    def info_command(self, items):
        return {"type": "command", "action": "info", "target": items[0]}
    
    def function_definition(self, items):
        function_name, command_string = items
        # Remove quotes from the command string
        command_string = str(command_string).strip('"')
        return {"type": "function_definition", "name": str(function_name), "command": command_string}
    
    def lock_command(self, items):
        return {"type": "command", "action": "lock", "variable": str(items[0])}
    
    def unlock_command(self, items):
        return {"type": "command", "action": "unlock", "variable": str(items[0])}

    def _parse_number(self, number_str: str) -> float:
        """Parse a number with optional K, M, B, T suffixes"""
        number_str = str(number_str).upper()
        multipliers = {'K': 1e3, 'M': 1e6, 'B': 1e9, 'T': 1e12}
        
        if number_str[-1] in multipliers:
            return float(number_str[:-1]) * multipliers[number_str[-1]]
        return float(number_str)

    # Terminal conversions
    STOCK_SYMBOL = str
    ETF_SYMBOL = str
    INDEX_SYMBOL = str
    VARIABLE = str
    FUNCTION_VARIABLE = str
    NAME = str
    ATTRIBUTE = str
    ORDER = str
    COMPARISON_OPERATOR = str
    NUMBER = str
    YEAR = str
    STRING = str 