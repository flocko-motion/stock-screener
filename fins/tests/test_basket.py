import unittest
from fins.entities.basket import Basket
from fins.entities.basket_item import BasketItem


class BasketTests(unittest.TestCase):

    def test_simple_basket(self):
        basket = Basket(items=[
            BasketItem("AAPL"),
        ])
        assert not (basket is None)


if __name__ == "__main__":
    unittest.main() 