"""
Pipe Entity

A pipeline of several chained plugins
"""

from typing import List
from .plugin import Plugin


class Pipe:
    """A pipeline of several chained plugins"""

    def __init__(self, *plugins: Plugin):
        self._plugins: List[Plugin] = list(plugins)

    def run(self, basket):
        for plugin in self._plugins:
            basket = plugin.run(basket)
        return basket

