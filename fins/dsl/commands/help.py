"""
Print help
"""

from typing import Type, List

from fins.entities.entity import Entity
from fins.entities.column import Column

from fins.dsl import *

@Command.register("function_help")
class HelpCommand(Command):

    @property
    def input_type(self) -> Type[Entity]:
        return None
        
    @property
    def output_type(self) -> Type[Entity]:
        return None

    @classmethod
    def category(cls) -> str | None:
        return "help"
        
    @classmethod
    def description(cls) -> str:
        return "Print help"

    def __init__(self):
        self.content = None
        super().__init__()

    def execute(self, args: CommandArgs) -> Output:
        if self.content is not None:
            return Output(self.content)

        result = []
        commands = Command.get_commands()

        cats = {"help":[]}

        for name, command in commands.items():
            cat = command.category()
            if not cat:
                continue
            if not (cat in cats):
                cats[cat] = []
            cats[cat].append(command)


        for cat_name, cat_commands in cats.items():
            if cat_name == "syntax":
                continue
            result.extend(self.title(cat_name))
            for command in cat_commands:
                name = Command.get_name_of_command(command).removeprefix("function_")
                if name == "help":
                    name = "?"
                elif cat_name != "basket.operator":
                    name = f"{name}()"
                result.extend(self.format_command(name, command.description()))

        result.extend(self.title("columns"))
        column_classes = sorted(Column.list(), key=lambda col: col.name())
        for col_class in column_classes:
            result.extend(self.format_command(f".{col_class.name()}()", col_class.description()))

        self.content = "\n".join(result)
        return Output(self.content)

    @staticmethod
    def title(caption: str) -> List[str]:
        return [f"---[{caption}]---------------------------",  ]

    @staticmethod
    def format_command(name: str, description: str) -> List[str]:
        return [f"{name:<20} {description}", ]