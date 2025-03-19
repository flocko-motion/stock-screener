from ..output import Output
from .command import Command, CommandArgs
from ...entities import Basket, BasketItem

class OperationCommand(Command):
    """Handles operation commands like + MSFT, - AAPL, etc."""
    
    def execute(self, args: CommandArgs) -> Basket:
        """Execute the operation command."""
        command = args.command_tree
        operator = command.children[0].value
        operand_group = command.children[1]
        operand_basket = self._process_operand_group(operand_group)
        
        # The left basket will be injected by _execute_command_chain
        left_basket = None
        for child in command.children:
            if child.data == "basket":
                left_basket = self._process_basket_node(child)
                break
        
        return self._apply_operation(left_basket, operand_basket, operator)

    def _process_operand_group(self, group_node):
        """Process a group of operands into a single basket."""
        items = []
        for operand in group_node.children:
            if not isinstance(operand, Tree):
                continue
                
            if operand.data == "operand":
                weight = 1.0
                for child in operand.children:
                    if child.data == "weight":
                        weight = self._parse_weight(child.children[0].value)
                    elif child.data == "symbol":
                        symbol = child.children[0].value
                        items.append(BasketItem(symbol, weight))
                    elif child.data == "variable":
                        items.extend(self._get_weighted_var_items(child.children[0].value, weight))
        
        return Basket(items)

    def _process_basket_node(self, basket_node):
        """Process a basket node into a Basket object."""
        items = []
        for child in basket_node.children:
            if child.data == "symbol":
                items.append(BasketItem(child.children[0].value))
        return Basket(items)

    def _parse_weight(self, weight_str):
        """Parse weight string into float value."""
        return float(weight_str[:-1]) if weight_str.endswith('x') else float(weight_str)

    def _get_weighted_var_items(self, var_name, weight):
        """Get weighted items from a variable basket."""
        var_basket = self.storage.get(var_name)
        if var_basket is None:
            raise ValueError(f"Variable not found: {var_name}")
        
        return [BasketItem(item.symbol, item.weight * weight) 
                for item in var_basket.items]

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