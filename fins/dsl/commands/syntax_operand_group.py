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
        if len(args.tree.children) == 1 and args.tree.children[0].data == "variable":
            # the whole tree is a single variable name => store the previous output in the variable (if it exists) and return var value
            return Output(self._process_single_variable(args.tree.children[0], args.previous_output), previous=args.previous_output)

        # process all nodes in the tree to compute the operation
        items = []
        for node in args.tree.children:
            if not isinstance(node, Tree):
                raise RuntimeError("Invalid operand group structure")
            
            items.extend(self._process_node(node, previous_output=args.previous_output))
        
        return Output(Basket(items), previous=args.previous_output)

    def _process_node(self, node: Tree, previous_output: Output) -> list[BasketItem]:
        """Process a single node and return resulting basket items."""
        if node.data == "operand":
            return self._process_operand_node(node)
        elif node.data == "symbol":
            return self._process_direct_node(node)
        elif node.data == "variable":
            return self._process_variable_node(node, previous_output)
        return []

    def _process_operand_node(self, node: Tree) -> list[BasketItem]:
        """Process an operand node with potential weights."""
        weight = 1.0
        symbol = None
        var_name = None
        
        for child in node.children:
            if isinstance(child, Token):
                token: Token = child
                if token.type == "WEIGHT":
                    weight = self._parse_weight(token.value)
                else:
                    raise RuntimeError(f"Unexpected token {token}")
            elif isinstance(child, Tree):
                tree: Tree = child
                if tree.data == "weight":
                    weight = self._parse_weight(tree.children[0].value)
                elif tree.data == "symbol":
                    symbol = tree.children[0].value
                elif tree.data == "variable":
                    var_name = tree.children[0].value
                else:
                    raise RuntimeError(f"Unexpected tree {tree}")
        
        if symbol:
            return [BasketItem(symbol, weight)]
        elif var_name:
            return self._get_weighted_var_items(var_name, weight)
        return []

    def _process_direct_node(self, node: Tree) -> list[BasketItem]:
        """Process a direct symbol or variable node."""
        if len(node.children) != 1:
            raise RuntimeError("Invalid node structure")

        ticker = node.children[0].value
        return [BasketItem(ticker, 1.0)]

    def _process_variable_node(self, node: Tree, previous_output: Output | None) -> list[BasketItem]:
        """Process a direct symbol or variable node."""
        if len(node.children) != 1:
            raise RuntimeError("Invalid node structure")

        variable_name = node.children[0].value

        if previous_output is not None:
            if not isinstance(previous_output, Output):
                raise RuntimeError("Expected Output as previous output")
            self.storage.set(variable_name, previous_output)

        return self.storage.get(variable_name)

    def _process_single_variable(self, node: Tree, previous_output: Output | None) -> Basket:
        """Process a direct symbol or variable node."""
        if len(node.children) != 1:
            raise RuntimeError("Invalid node structure")

        variable_name = node.children[0].value

        if (previous_output is not None) and (not previous_output.is_void()) and previous_output.assert_type(Basket):
            self.storage.set(variable_name, previous_output.data)

        val = self.storage.get(variable_name)
        if val is None:
            return Basket()
        elif isinstance(val, Basket):
            return val
        else:
            raise RuntimeError("Expected Basket as variable value")


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