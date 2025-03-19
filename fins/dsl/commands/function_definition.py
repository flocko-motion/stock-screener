from ..output import Output
from .command import Command, CommandArgs
from ...entities import Token

class FunctionDefinitionCommand(Command):
    """Handles function definition commands."""
    
    def execute(self, args: CommandArgs) -> None:
        """Execute the function definition command."""
        command = args.command_tree
        
        # Extract name and function command from the tree
        name = None
        function_command = None
        
        for child in command.children:
            if child.data == "FUNCTION_VARIABLE":
                name = child.value
            elif child.data == "STRING":
                # Remove the quotes from the string
                function_command = child.value[1:-1]
        
        if name is None or function_command is None:
            raise ValueError("Function definition must have a name and command")
            
        # Store the function in the storage
        self.storage.set_function(name, function_command)
        
        return None  # Function definitions don't return a basket 