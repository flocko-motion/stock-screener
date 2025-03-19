from ..output import Output
from .command import Command, CommandArgs
from ...entities import Basket, BasketItem

class BasketCommand(Command):
    """Handles basket creation commands."""
    
    def execute(self, args: CommandArgs) -> Basket:
        """Execute the basket command."""
        command = args.command_tree
        
        # Process each child node to build the basket
        items = []
        for child in command.children:
            if child.data == "symbol":
                items.append(BasketItem(child.children[0].value))
        
        return Basket(items) 