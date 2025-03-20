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
                raise RuntimeError("Invalid operand group structure")
            
            items.extend(self._process_node(node))
        
        return Output(Basket(items), previous=args.previous_output)

    def _process_node(self, node: Tree) -> list[BasketItem]:
        """Process a single node and return resulting basket items."""
        if node.data == "operand":
            return self._process_operand_node(node)
        elif node.data in ("symbol", "variable"):
            return self._process_direct_node(node)
        return []

    def _process_operand_node(self, node: Tree) -> list[BasketItem]:
        """Process an operand node with potential weights."""
        weight = 1.0
        symbol = None
        var_name = None
        
        for child in node.children:
            if not isinstance(child, Tree):
                continue
                
            if child.data == "weight":
                weight = self._parse_weight(child.children[0].value)
            elif child.data == "symbol":
                symbol = child.children[0].value
            elif child.data == "variable":
                var_name = child.children[0].value
        
        if symbol:
            return [BasketItem(symbol, weight)]
        elif var_name:
            return self._get_weighted_var_items(var_name, weight)
        return []

    def _process_direct_node(self, node: Tree) -> list[BasketItem]:
        """Process a direct symbol or variable node."""
        if len(node.children) != 1:
            raise RuntimeError("Invalid node structure")
            
        value = node.children[0].value
        if node.data == "symbol":
            return [BasketItem(value, 1.0)]
        return self._get_weighted_var_items(value, 1.0)

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
            
        return [BasketItem(item.symbol, item.weight * weight) for item in var_basket.items] 