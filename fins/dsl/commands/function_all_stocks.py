from fins.entities import Basket, BasketItem
from fins.dsl import *
from data_sources.fmp import all_stocks

@Command.register("function_stocks")
class FunctionAllStocks(Command):
    @classmethod
    def category(cls) -> str | None:
        return "search"

    @classmethod
    def description(cls) -> str:
        return "Get all available stocks"

    @property
    def input_type(self) -> str:
        return "none"

    @property
    def output_type(self) -> str:
        return "basket"

    def execute(self, args: CommandArgs) -> Output:
        symbols = all_stocks()
        basket = Basket()
        for symbol in symbols:
            try:
                item = BasketItem(symbol)
                basket.add_item(item)
            except Exception as e:
                print(f"invalid symbol in fetched list: {e}")
        return Output(basket)