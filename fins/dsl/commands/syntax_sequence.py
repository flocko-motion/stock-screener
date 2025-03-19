from lark import Tree, Token
from ..output import Output
from .command import Command, CommandArgs
from ...entities import Basket, BasketItem

@Command.register("sequence")
class SequenceCommand(Command):
    """Handles sequences of operands and operators."""
    
    @property
    def description(self) -> str:
        return "Processes a sequence of operands and operators to create or modify baskets"
        
    @property
    def input_type(self) -> str:
        return "none"  # Can start fresh or use injected basket
        
    @property
    def output_type(self) -> str:
        return "basket"
    
    def execute(self, args: CommandArgs) -> Output:
        """Execute the sequence command."""
        sequence_tree = args.tree
        result_basket = self._find_existing_basket(sequence_tree)
        
        # Process operand groups and operators
        i = 0
        while i < len(sequence_tree.children):
            node = sequence_tree.children[i]
            if not isinstance(node, Tree):
                i += 1
                continue
                
            if node.data == "operand_group":
                result_basket = self._process_operand_group(node, result_basket)
                i += 1
            elif node.data == "OPERATOR":
                # Get the next operand group and skip it in the next iteration
                next_node = sequence_tree.children[i + 1] if i + 1 < len(sequence_tree.children) else None
                result_basket = self._process_operator(node, next_node, result_basket)
                i += 2  # Skip the next node since we processed it
            else:
                i += 1
        
        if result_basket is None:
            result_basket = Basket([])
            
        return Output(result_basket, output_type="basket")

    def _find_existing_basket(self, sequence_tree: Tree) -> Basket:
        """Find any existing basket from the pipeline."""
        for node in sequence_tree.children:
            if isinstance(node, Tree) and node.data == "basket":
                return self._process_basket_node(node)
        return None

    def _process_operand_group(self, node: Tree, result_basket: Basket) -> Basket:
        """Process an operand group node."""
        operand_output = self._execute_subcommand("operand_group", node)
        if result_basket is None:
            return operand_output.data
        return result_basket.union(operand_output.data)

    def _process_operator(self, operator_node: Tree, next_node: Tree, result_basket: Basket) -> Basket:
        """Process an operator and its following operand group."""
        if not next_node or next_node.data != "operand_group" or result_basket is None:
            return result_basket

        operator = operator_node.value
        operand_output = self._execute_subcommand("operand_group", next_node)
        
        operations = {
            "-": lambda x, y: x.subtract(y),
            "&": lambda x, y: x.intersection(y),
            "+": lambda x, y: x.union(y)
        }
        
        operation = operations.get(operator)
        if operation:
            return operation(result_basket, operand_output.data)
        return result_basket

    def _process_basket_node(self, basket_node) -> Basket:
        """Process a basket node into a Basket object."""
        items = []
        for child in basket_node.children:
            if isinstance(child, Tree):
                if child.data == "symbol":
                    # Get the STOCK_SYMBOL token value
                    symbol_token = child.children[0]
                    if isinstance(symbol_token, Token):
                        items.append(BasketItem(symbol_token.value, 1.0))
                    else:
                        items.append(BasketItem(symbol_token.children[0].value, 1.0))
                elif child.data == "operand":
                    weight = 1.0
                    symbol = None
                    
                    for operand_child in child.children:
                        if isinstance(operand_child, Tree):
                            if operand_child.data == "weight":
                                weight = float(operand_child.children[0].value.rstrip('x'))
                            elif operand_child.data == "symbol":
                                symbol = operand_child.children[0].value
                    
                    if symbol:
                        items.append(BasketItem(symbol, weight))
        return Basket(items)