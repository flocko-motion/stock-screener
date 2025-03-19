from lark import Tree, Token
from ..output import Output
from .command import Command, CommandArgs
from ...entities import Basket, BasketItem

@Command.register("operation_command")
class OperationCommand(Command):
    """Handles operation commands like + MSFT, - AAPL, etc."""
    
    @property
    def description(self) -> str:
        return "Performs set operations (+, -, &) on baskets in a pipeline"
        
    @property
    def input_type(self) -> str:
        return "basket"  # Requires a basket from the pipeline
        
    @property
    def output_type(self) -> str:
        return "basket"
    
    def execute(self, args: CommandArgs) -> Output:
        """Execute the operation command."""
        command = args.tree
        
        # Find the operator and operand group
        operator = None
        operand_group = None
        left_basket = None
        
        for child in command.children:
            if isinstance(child, Token) and child.type == 'OPERATOR':
                operator = child.value
            elif isinstance(child, Tree):
                if child.data == "operand_group":
                    operand_group = child
                elif child.data == "basket":
                    left_basket = self._process_basket_node(child)
        
        if operator is None or operand_group is None:
            return Output("Invalid operation command structure", output_type="error")
            
        operand_output = self._execute_subcommand("operand_group", operand_group)
        result = self._apply_operation(left_basket, operand_output.data, operator)
        return Output(result, output_type="basket")

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
                    elif isinstance(symbol_token, str):
                        items.append(BasketItem(symbol_token, 1.0))
                    elif isinstance(symbol_token, Tree):
                        symbol_value = symbol_token.children[0]
                        if isinstance(symbol_value, Token):
                            items.append(BasketItem(symbol_value.value, 1.0))
                        else:
                            items.append(BasketItem(str(symbol_value), 1.0))
                elif child.data == "operand":
                    weight = 1.0
                    symbol = None
                    
                    for operand_child in child.children:
                        if isinstance(operand_child, Tree):
                            if operand_child.data == "weight":
                                weight = float(operand_child.children[0].value.rstrip('x'))
                            elif operand_child.data == "symbol":
                                symbol_token = operand_child.children[0]
                                if isinstance(symbol_token, Token):
                                    symbol = symbol_token.value
                                elif isinstance(symbol_token, str):
                                    symbol = symbol_token
                                elif isinstance(symbol_token, Tree):
                                    symbol_value = symbol_token.children[0]
                                    if isinstance(symbol_value, Token):
                                        symbol = symbol_value.value
                                    else:
                                        symbol = str(symbol_value)
                    
                    if symbol:
                        items.append(BasketItem(symbol, weight))
        return Basket(items)

    def _apply_operation(self, left_basket, right_basket, operator) -> Basket:
        """Apply the specified operation between two baskets."""
        if left_basket is None:
            return right_basket
            
        if operator == "+":
            return left_basket.union(right_basket)
        elif operator == "-":
            return left_basket.subtract(right_basket)
        elif operator == "&":
            return left_basket.intersection(right_basket)
        else:
            raise ValueError(f"Unknown operator: {operator}") 