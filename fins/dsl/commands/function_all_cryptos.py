from types import NoneType

from fins.entities import Basket, BasketItem
from fins.dsl import *
from fins.data_sources.fmp import all_cryptos

@Command.register("cryptos")
class FunctionAllCryptos(Command):
    @classmethod
    def category(cls) -> str | None:
        return "search"

    @classmethod
    def description(cls) -> str:
        return "Get all available cryptocurrencies"


    @classmethod
    def named_args(cls) -> list[CommandArg]:
        return []

    @classmethod
    def input_type(cls) -> type:
        return NoneType

    @classmethod
    def output_type(cls) -> type:
        return Basket

    def execute(self, args: CommandArgs) -> Output:
        symbols = all_cryptos()
        basket = Basket()
        for symbol in symbols:
            try:
                item = BasketItem(symbol)
                basket.add_item(item)
            except Exception as e:
                print(f"invalid symbol in fetched list: {e}")
        return Output(basket)