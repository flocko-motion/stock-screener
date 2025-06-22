"""
codegen.py generates python files based on data fetched from the fmp API
"""
from fins.data_sources.fmp import all_stocks, all_etfs

symbols_py_export =  ""
symbols_py_body = ""

def add_ticker(ticker: str):
	global symbols_py_export, symbols_py_body
	alias = (ticker if ticker[0].isalpha() else "_" + ticker).replace("-", "_")
	symbols_py_export += "    \"" + alias + "\",\n"
	symbols_py_body += f"{alias} = BasketItem('{ticker}')\n"

for ticker in all_stocks():
	add_ticker(ticker)

for ticker in all_etfs():
	add_ticker(ticker)


with open('fins/terminal/symbols/__init__.py', 'w') as file:
	file.write(f""" 
from fins.entities import BasketItem

{symbols_py_body}

__all__ = [
{symbols_py_export}
]
""")


