from lark import Tree, Token

from fins.entities import Basket, BasketItem
from fins.dsl import *

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