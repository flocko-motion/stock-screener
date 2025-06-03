"""
Print help
"""

from typing import Type, List

from fins.entities.entity import Entity
from fins.entities.column import Column

from fins.dsl import *

@Command.register("function_help")
class HelpCommand(Command):

    @classmethod

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

    @classmethod
    def examples(cls) -> str:
        return ""

    @classmethod
    def named_args(cls) -> dict[str,str] | None:
        return None

    def __init__(self):
        self.content = None
        super().__init__()

    def function_core_name(self, name: str) -> str:
        if name[-2] == "()":
            name = name[:-2]
        if name[0] == ".":
            name = name[1:]
        return name

    def execute(self, args: CommandArgs) -> Output:
        if len(args.tree.children) == 1:
            topic = args.tree.children[0]
            topic_type = "" if topic is None else str(topic.data)
            topic_value = "" if topic is None else str(topic.children[0])
            if topic_type == "help_topic_function":
                cmd = Command.get_command(self.function_core_name(topic_value))
                out = f"{topic_value}()"
                if cmd.named_args():
                    for arg in cmd.named_args():
                        out += ("\n(optional)" if arg.optional else "(required)") + f" {arg.name}='{arg.default}'\t{arg.description}"
                out += f"\n{cmd.description()}"
                examples = cmd.examples()
                if not (examples is None):
                    out += f"\nExamples:\n{examples}"
                return Output(out)


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