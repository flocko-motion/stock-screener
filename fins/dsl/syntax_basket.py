from output import Output
from command import Command, CommandArgs
from fins.entities import Basket, BasketItem

class BasketCommand(Command):
    """Handles basket creation commands."""
    
    @property
    def description(self) -> str:
        return "Creates a basket from a list of symbols"
        
    @property
    def input_type(self) -> str:
        return "none"
        
    @property
    def output_type(self) -> str:
        return "basket"
    
    def execute(self, args: CommandArgs) -> Basket:
        """Execute the basket command."""
        command = args.command_tree
        
        # Process each child node to build the basket
        items = []
        for child in command.children:
            if child.data == "symbol":
                items.append(BasketItem(child.children[0].value))
        
        return Basket(items) 