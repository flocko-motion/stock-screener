"""
codegen.py generates python files based on data fetched from the fmp API
"""
from fins.data_sources.fmp import all_stocks, all_etfs

symbols_py_export =  ""
symbols_py_body = ""

def add_ticker(ticker: str):
	global symbols_py_export, symbols_py_body
	if not ticker[0].isalpha() or "-" in ticker:
		return
	symbols_py_export += "    \"" + ticker + "\",\n"
	symbols_py_body += f"{ticker} = BasketItem('{ticker}')\n"

for ticker in all_stocks():
	add_ticker(ticker)

for ticker in all_etfs():
	add_ticker(ticker)

symbols_py = f""" 
from fins.entities import BasketItem

{symbols_py_body}

__all__ = [
{symbols_py_export}
]
"""

# write to file
with open('fins/terminal/symbols/__init__.py', 'w') as file:
	file.write(symbols_py)


