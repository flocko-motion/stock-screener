from lark import Tree, Token

from ..output import Output
from .command import Command, CommandArgs
from ...entities import Basket, BasketItem

@Command.register("operand_group")
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
    
    def execute(self, args: CommandArgs) -> Output:
        items = []
        for node in args.tree.children:
            if not isinstance(node, Tree):
                raise RuntimeError("Why? What is this? Invalid operand group structure")
                # continue
                
            if node.data == "operand":
                weight = 1.0
                symbol = None
                var_name = None
                
                for child in node.children:
                    if isinstance(child, Tree):
                        if child.data == "weight":
                            weight = self._parse_weight(child.children[0].value)
                        elif child.data == "symbol":
                            symbol = child.children[0].value
                        elif child.data == "variable":
                            var_name = child.children[0].value
                
                if symbol:
                    items.append(BasketItem(symbol, weight))
                elif var_name:
                    items.extend(self._get_weighted_var_items(var_name, weight))
            elif node.data == "symbol":
                # Handle direct symbols (without weight)
                items.append(BasketItem(node.children[0].value, 1.0))
            elif node.data == "variable":
                # Handle direct variables (without weight)
                items.extend(self._get_weighted_var_items(node.children[0].value, 1.0))
        
        return Output(Basket(items), output_type="basket")

    def _parse_weight(self, weight_str: str) -> float:
        """Parse weight string into float value."""
        if isinstance(weight_str, (int, float)):
            return float(weight_str)
        return float(weight_str[:-1]) if weight_str.endswith('x') else float(weight_str)

    def _get_weighted_var_items(self, var_name: str, weight: float) -> list[BasketItem]:
        """Get weighted items from a variable basket."""
        var_basket = self.storage.get(var_name)
        if var_basket is None:
            return []
            
        # Apply weight to all items in the variable basket
        return [BasketItem(item.symbol, item.weight * weight) for item in var_basket.items] 