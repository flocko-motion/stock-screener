"""
Union operator command for combining baskets.
"""

from typing import Type

from fins.entities import Basket, Entity
from fins.dsl import *

@Command.register("+")
class UnionCommand(Command):
    """Command for combining baskets (union operation)."""
    
    @property
    def input_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def output_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def description(self) -> str:
        """Get the operator's description."""
        return "Basket union operator"
        
    def execute(self, args: CommandArgs) -> Output:
        """Execute the union operation on the baskets."""
        self.validate_input(args)
        basket = args.effective_input
        
        # Get the right-hand operand from the tree
        right_operand = args.tree.children[0]
        
        # Apply the union
        basket.union(right_operand)
            
        return Output(basket) 