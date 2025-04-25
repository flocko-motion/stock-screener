from lark import Tree, Token
from typing import Type

from fins.entities import Basket, BasketItem, Column
from fins.dsl import *

@Command.register("column_function")
class ColumnFunctionCommand(Command):

    @property
    def description(self) -> str:
        return "Execute a column function"
        
    @property
    def input_type(self) -> str:
        return "none"  # Can start fresh or use injected basket
        
    @property
    def output_type(self) -> str:
        return "basket"
    
    def execute(self, args: CommandArgs) -> Output:
        col_func_args = args.tree.children
        if len(col_func_args) != 3:
            raise SyntaxError(f"wrong number of args")
        column_class_name = col_func_args[1].value
        column_class:Type[Column] = Column.get(column_class_name)
        # TODO: parse col_func_args[2].value into args dict
        column_name = str(col_func_args[0].value) if col_func_args[0] is not None else column_class_name
        column:Column = column_class(column_name, args={})
        basket = args.get_previous_basket().copy_of()
        basket.add_column(column)
        return Output(basket, previous=args.previous_output)

    @staticmethod
    def _parse_weight(value):
        if value.endswith("x"):
            return float(value.rstrip("x"))
        return float(value)
