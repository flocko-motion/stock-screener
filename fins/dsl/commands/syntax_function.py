from lark import Tree, Token

from fins.dsl import *

@Command.register("function_call")
class FunctionCallCommand(Command):
    """ Executes a function call.
    """
    
    @classmethod
    def category(cls) -> str | None:
        return "syntax"
        
    @classmethod
    def description(cls) -> str:
        return "Call a function with arguments"
        
    @property
    def input_type(self) -> str:
        return "none"  # Requires a basket from the pipeline
        
    @property
    def output_type(self) -> str:
        return "basket"
    
    def execute(self, args: CommandArgs) -> Output:
        f_name = f"function_{args.tree.children[0]}"
        f_args: Tree | None = args.tree.children[1] if len(args.tree.children) > 1 else None
        if not f_args is None and not isinstance(f_args, Tree):
            raise TypeError("failed to parse arguments of function call")

        handler = Command.get_command(f_name)
        return handler.execute(CommandArgs(tree=f_args, previous_output=args.previous_output, storage=args.storage))

