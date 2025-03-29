from lark import Tree, Token

from fins.entities import Basket, BasketItem

from . import Output
from . import Command, CommandArgs

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
        operator = None
        operand = None

        for tree in args.tree.children:
            if isinstance(tree, Token) and tree.type == 'OPERATOR':
                operator = tree.value
            elif isinstance(tree, Tree):
                if tree.data == "operand_group":
                    operand = tree
        
        if operator is None or operand is None:
            return Output("Invalid operation command structure", output_type="error")

        executor = Command.get_command(operand.data)
        operand_result = executor.execute(CommandArgs(tree=operand, previous_output=args.previous_output))

        if not isinstance(args.previous_output, Output) or not isinstance(args.previous_output.data, Basket):
            return Output(RuntimeError(f"expected 'Basket' as left input, got '{args.previous_output}"), previous=args.previous_output)
        left_basket: Basket = args.previous_output.data

        if not isinstance(operand_result.data, Basket):
            return Output(RuntimeError(f"expected 'Basket' as right input, got '{operand_result.data}"), previous=args.previous_output)
        right_basket: Basket = operand_result.data

        result = Output(left_basket.operation(right_basket, operator), previous=args.previous_output)
        return result


    #
    # def _process_basket_node(self, basket_node) -> Basket:
    #     """Process a basket node into a Basket object."""
    #     items = []
    #     for child in basket_node.children:
    #         if isinstance(child, Tree):
    #             if child.data == "symbol":
    #                 # Get the STOCK_SYMBOL token value
    #                 symbol_token = child.children[0]
    #                 if isinstance(symbol_token, Token):
    #                     items.append(BasketItem(symbol_token.value, 1.0))
    #                 elif isinstance(symbol_token, str):
    #                     items.append(BasketItem(symbol_token, 1.0))
    #                 elif isinstance(symbol_token, Tree):
    #                     symbol_value = symbol_token.children[0]
    #                     if isinstance(symbol_value, Token):
    #                         items.append(BasketItem(symbol_value.value, 1.0))
    #                     else:
    #                         items.append(BasketItem(str(symbol_value), 1.0))
    #             elif child.data == "operand":
    #                 weight = 1.0
    #                 symbol = None
    #
    #                 for operand_child in child.children:
    #                     if isinstance(operand_child, Tree):
    #                         if operand_child.data == "weight":
    #                             weight = float(operand_child.children[0].value.rstrip('x'))
    #                         elif operand_child.data == "symbol":
    #                             symbol_token = operand_child.children[0]
    #                             if isinstance(symbol_token, Token):
    #                                 symbol = symbol_token.value
    #                             elif isinstance(symbol_token, str):
    #                                 symbol = symbol_token
    #                             elif isinstance(symbol_token, Tree):
    #                                 symbol_value = symbol_token.children[0]
    #                                 if isinstance(symbol_value, Token):
    #                                     symbol = symbol_value.value
    #                                 else:
    #                                     symbol = str(symbol_value)
    #
    #                 if symbol:
    #                     items.append(BasketItem(symbol, weight))
    #     return Basket(items)
