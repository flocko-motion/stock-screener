import unittest

# from fins.entities import columns
from fins.entities.basket import Basket
from fins.entities.basket_item import BasketItem
from .tools import time_it, no_cache, unbuffered_output


class BasketItemTests(unittest.TestCase):

    def test_basket_item_multiplication(self):
        print("hello")
        item = BasketItem("AAPL")
        multiplied_item = item * 3
        self.assertEqual(multiplied_item.ticker, "AAPL")
        self.assertEqual(multiplied_item.amount, 3)


if __name__ == "__main__":
    unittest.main() 