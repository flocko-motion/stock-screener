import unittest

from fins.entities import columns
from fins.entities.basket import Basket
from fins.entities.basket_item import BasketItem


class BasketTests(unittest.TestCase):

    def test_simple_basket(self):
        basket = Basket(name="foo", items=[
            BasketItem("AAPL"),
        ])
        basket.add_column(columns.PeColumn())
        desc = basket.to_dict()

        assert not (desc is None)
        assert desc["name"] == "foo"
        assert len(desc["items"]) == 1
        assert desc["items"][0]["ticker"] == "AAPL"
        assert desc["items"][0]["amount"] == 1
        assert desc["items"][0]["class"] == "BasketItem"
        assert len(desc["columns"]) == 1
        assert desc["columns"][0]["class"] == "PeColumn"

        data = basket.data()
        assert not (data is None)


if __name__ == "__main__":
    unittest.main() 