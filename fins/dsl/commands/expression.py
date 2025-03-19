from ..output import Output
from .command import Command, CommandArgs
from ...entities import Basket, BasketItem

class ExpressionCommand(Command):
    """Handles expression commands that combine operands with operators."""
    
    @property
    def description(self) -> str:
        return "Combines operands (symbols and variables) with operators (+, -, &) to create or modify baskets"
        
    @property
    def input_type(self) -> str:
        return "none"  # Can start fresh or use injected basket
        
    @property
    def output_type(self) -> str:
        return "basket"
    
    def execute(self, args: CommandArgs) -> Basket:
        """Execute the expression command."""
        expr_tree = args.command_tree
        result_basket = None
        current_operator = "+"  # Default to union for implicit operations
        
        for node in expr_tree.children:
            if not isinstance(node, Tree):
                continue
            
            if node.data == "operator":
                current_operator = node.value
            elif node.data == "operand":
                operand_basket = self._process_operand(node)
                result_basket = self._apply_operation(result_basket, operand_basket, current_operator)
        
        return result_basket

    def _process_operand(self, operand_node):
        """Convert an operand node into a Basket."""
        weight = 1.0
        items = []
        
        for child in operand_node.children:
            if not isinstance(child, Tree):
                continue
            
            if child.data == "weight":
                weight = self._parse_weight(child.children[0].value)
            elif child.data == "symbol":
                symbol = child.children[0].value
                items.append(BasketItem(symbol, weight))
            elif child.data == "variable":
                items.extend(self._get_weighted_var_items(child.children[0].value, weight))
        
        return Basket(items)

    def _parse_weight(self, weight_str):
        """Parse weight string into float value."""
        return float(weight_str[:-1]) if weight_str.endswith('x') else float(weight_str)

    def _get_weighted_var_items(self, var_name, weight):
        """Get weighted items from a variable basket."""
        var_basket = self.storage.get(var_name)
        if var_basket is None:
            raise ValueError(f"Variable not found: {var_name}")
        
        return [BasketItem(item.symbol, item.weight * weight) 
                for item in var_basket.items]

    def _apply_operation(self, left_basket, right_basket, operator):
        """Apply the specified operation between two baskets."""
        if left_basket is None:
            return right_basket
        
        operations = {
            "+": "union",
            "-": "difference",
            "&": "intersection"
        }
        
        command = self.commands[operations[operator]]
        return command.execute(CommandArgs([left_basket], [right_basket])) 