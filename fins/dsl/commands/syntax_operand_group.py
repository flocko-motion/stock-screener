from ..output import Output
from .command import Command, CommandArgs
from ...entities import Basket, BasketItem

class OperandGroupCommand(Command):
    """Handles groups of operands (symbols and variables with optional weights)."""
    
    @property
    def description(self) -> str:
        return "Processes a group of operands (symbols and variables) with optional weights"
        
    @property
    def input_type(self) -> str:
        return "none"
        
    @property
    def output_type(self) -> str:
        return "basket"
    
    def execute(self, args: CommandArgs) -> Basket:
        """Execute the operand group command."""
        group_node = args.command_tree
        items = []
        
        for operand in group_node.children:
            if not isinstance(operand, Tree):
                continue
                
            if operand.data == "operand":
                weight = 1.0
                for child in operand.children:
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