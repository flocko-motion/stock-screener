from dsl.command import CommandArg
from fins.entities import Basket, BasketItem
from fins.dsl import *
from data_sources.fmp import all_etfs

@Command.register("ls")
class FunctionFilesList(Command):
    @classmethod
    def category(cls) -> str | None:
        return "files"

    @classmethod
    def description(cls) -> str:
        return "List files, optionally with search filters"

    @classmethod
    def examples(cls) -> str:
        return f"""{cls.name()}(path="/foo/bar")"""

    @classmethod
    def named_args(cls) -> list[CommandArg] | None:
        return [
            CommandArg(name="path", description="Path prefix filter", optional=True),
            CommandArg(name="type", description="Entity type to filter for, e.g. 'basket'", optional=True),
        ]

    @classmethod
    def input_type(cls) -> type:
        return object

    @classmethod
    def output_type(cls) -> type:
        return object

    def execute(self, args: CommandArgs) -> Output:
        p = args.get_named_arg("path")
        if p is None:
            p = "/"
        elif not p.startswith("/"):
            p = "/" + p
        files = args.storage.list(prefix=p)
        files.sort()
        captions = ["path", "type", "size"]
        print(f"{captions[0]:<20}\t{captions[1]}\t{captions[2]}")
        for file in files:
            info = args.storage.info(file)
            print(f"{file:<20}\t{info[0]}\t{info[1]}")

        return Output(None)