from fins.entities import Basket, BasketItem
from fins.dsl import *
from data_sources.fmp import all_etfs

@Command.register("function_ls")
class FunctionFilesList(Command):
    @classmethod
    def category(cls) -> str | None:
        return "files"

    @classmethod
    def description(cls) -> str:
        return "List files, optionally with search filters"

    @property
    def input_type(self) -> str:
        return "none"

    @property
    def output_type(self) -> str:
        return "none"

    def execute(self, args: CommandArgs) -> Output:
        p = args.get_named("path", default="", required=False)
        if p is None:
            p = "/"
        elif not p.startswith("/"):
            p = "/" + p
        files = args.storage.list(prefix=p)
        files.sort()
        for file in files:
            print(f"{file} \t{args.storage.get_type(file)}")

        return Output(None)