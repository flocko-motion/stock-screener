from ..output import Output
from .command import Command, CommandArgs
from ...entities import Basket, BasketItem

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
    
    def execute(self, args: CommandArgs) -> Basket:
        """Execute the operation command."""
        command = args.command_tree
        operator = command.children[0].value
        operand_group = command.children[1]
        operand_basket = self.commands["operand_group"].execute(CommandArgs(command_tree=operand_group))
        
        # The left basket will be injected by _execute_command_chain
        left_basket = None
        for child in command.children:
            if child.data == "basket":
                left_basket = self._process_basket_node(child)
                break
        
        return self._apply_operation(left_basket, operand_basket, operator)

    def _process_basket_node(self, basket_node):
        """Process a basket node into a Basket object."""
        items = []
        for child in basket_node.children:
            if child.data == "symbol":
                items.append(BasketItem(child.children[0].value))
        return Basket(items)

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