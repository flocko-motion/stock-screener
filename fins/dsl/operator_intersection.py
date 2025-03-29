"""
Intersection operator command for finding common elements in baskets.
"""

from typing import Type
from fins.entities import Basket, Entity
from command import Command, CommandArgs
from output import Output


class IntersectionCommand(Command):
    """Command for finding common elements in baskets (intersection operation)."""
    
    @property
    def input_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def output_type(self) -> Type[Entity]:
        return Basket
        
    @property
    def description(self) -> str:
        """Get the operator's description."""
        return "Basket intersection operator"
        
    def execute(self, args: CommandArgs) -> Output:
        """Execute the intersection operation on the baskets."""
        self.validate_input(args)
        basket = args.effective_input
        
        # Get the right-hand operand from the tree
        right_operand = args.tree.children[0]
        
        # Apply the intersection
        basket.intersection(right_operand)
            
        return Output(basket) 