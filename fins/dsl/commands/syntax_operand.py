from lark import Tree, Token

from fins.entities import Basket, BasketItem
from fins.dsl import *

@Command.register("operand")
class OperandCommand(Command):
    """ Handles operation commands like: 3x $foo
    There's no left input. The operand acts as a function on the next argument and returns a basket.
    """
    
    @property
    def description(self) -> str:
        return "Performs set operations (+, -, &) on next argument. Takes no left input."
        
    @property
    def input_type(self) -> str:
        return "none"  # Requires a basket from the pipeline
        
    @property
    def output_type(self) -> str:
        return "basket"
    
    def execute(self, args: CommandArgs) -> Output:
        arg = None
        if args.has_previous_output():
            if len(args.tree.children) > 1:
                raise SyntaxError("Operand accepts left input OR right input, not both")
            arg = args.previous_output
        elif len(args.tree.children) < 2:
            raise SyntaxError("Operand requires at least one right argument")
        else:
            node = args.tree.children[1]
            if isinstance(node, Tree):
                arg = self.execute_tree(CommandArgs(tree=node, previous_output=None, storage=args.storage))

        if not arg.assert_type(Basket):
            raise SyntaxError("Operand requires a basket as an argument")
        operand: Basket = arg.data

        operator = args.tree.children[0]
        if operator.type == "WEIGHT":
            weight = self._parse_weight(operator.value)
            return Output(operand.multiply(weight), previous=args.previous_output)

        raise SyntaxError(f"Unexpected operator {operator}")
