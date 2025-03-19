from ..output import Output
from .command import Command, CommandArgs
from ...entities import Basket, BasketItem

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
    
    def execute(self, args: CommandArgs) -> Basket:
        """Execute the sequence command."""
        sequence_tree = args.command_tree
        result_basket = None
        current_operator = "+"  # Default to union for implicit operations
        
        for node in sequence_tree.children:
            if not isinstance(node, Tree):
                continue
                
            if node.data == "operand_group":
                operand_basket = self.commands["operand_group"].execute(CommandArgs(command_tree=node))
                result_basket = self._apply_operation(result_basket, operand_basket, current_operator)
            elif node.data == "OPERATOR":
                current_operator = node.value
        
        return result_basket

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