import unittest

from fins.entities import columns
from fins.entities.basket import Basket
from fins.entities.basket_item import BasketItem
from .tools import time_it, no_cache


class BasketTests(unittest.TestCase):

    def test_simple_basket(self):
        basket = Basket(name="foo", items=[
            BasketItem("AAPL"),
        ])

        cols = [
            columns.McapColumn(),
            columns.NpmColumn(),
            columns.PeColumn(),
            columns.PegColumn(),
            columns.RoeColumn(),
            columns.VolColumn(),
            columns.YieldColumn(),
        ]
        for col in cols:
            basket.add_column(col)

        desc = basket.to_dict()

        assert not (desc is None)
        assert desc["name"] == "foo"
        assert len(desc["items"]) == 1
        assert desc["items"][0]["ticker"] == "AAPL"
        assert desc["items"][0]["amount"] == 1
        assert desc["items"][0]["class"] == "BasketItem"

        assert len(desc["columns"]) == len(cols)
        assert desc["columns"][0]["class"] == "McapColumn"
        assert desc["columns"][1]["class"] == "NpmColumn"
        assert desc["columns"][2]["class"] == "PeColumn"
        assert desc["columns"][3]["class"] == "PegColumn"
        assert desc["columns"][4]["class"] == "RoeColumn"
        assert desc["columns"][5]["class"] == "VolColumn"
        assert desc["columns"][6]["class"] == "YieldColumn"

        data = basket.data()
        assert not (data is None)
        print(f"\n{data}\n")

    @time_it
    @no_cache
    def test_multithreaded_basket_creation_one(self):
        symbols = ["AAPL"]
        basket = Basket.from_symbols(symbols)
        assert len(basket.items) == len(symbols)

    @time_it
    @no_cache
    def test_multithreaded_basket_creation(self):
        symbols = ["ATLFF","ALFNF","ACMDY","ASBPW","CWBR","ATIW","FBTC","FXED","PFS","DGRS","BUFIX","GPFT","FFTI","ASXSF","BKAYY","AMH-PE","RGNX","WSCC","RXST","ACU","TIBGX","ZSPY","AHG","GOP","FTA","HROWM","FORD","RSYEX","NNAVW","HNGZY","TNGRF","MARUY","HIZOF","ALRY","RUSHA","ORMP","WLGS","SRTS","DISSX","ULNV","SOGFF","DFLIW","TCEFF","APPZ","CGO","YAMCF","NIKLF",]
        #symbols = ["AAPL", "GOOG", "MSFT"]
        basket = Basket.from_symbols(symbols)
        assert len(basket.items) == len(symbols)


if __name__ == "__main__":
    unittest.main() 