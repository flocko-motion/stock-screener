from lark import Tree, Token
from typing import Type

from fins.entities import Basket, BasketItem, Column
from fins.dsl import *

@Command.register("column_function")
class ColumnFunctionCommand(Command):

    @classmethod
    def category(cls) -> str | None:
        return "syntax"
        
    @classmethod
    def description(cls) -> str:
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
        if isinstance(col_func_args[0], Tree):
            column_name = str(col_func_args[0].children[0])
        else:
            column_name = str(col_func_args[0].value) if col_func_args[0] is not None else column_class_name

        # fetch named args for column function
        col_func_args_dict = {
            "alias": column_name
        }
        if len(col_func_args) == 3 and isinstance(col_func_args[2], Tree):
            for arg in col_func_args[2].children:
                col_func_args_dict[str(arg.children[0])] = str(arg.children[1].children[0])

        column:Column = column_class(**col_func_args_dict)
        basket = args.get_previous_basket().copy_of()
        basket.add_column(column)
        return Output(basket, previous=args.previous_output)

    @staticmethod
    def _parse_weight(value):
        if value.endswith("x"):
            return float(value.rstrip("x"))
        return float(value)
