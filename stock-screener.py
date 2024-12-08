import os
import shutil
import traceback

from lib import Ticker
import lib

# fetch and process data
tickers = lib.stockanalysis_get_constituents()
for ticker in tickers.keys():
    try:
        print(f"\n-----[{ticker}]----------------\n")
        Ticker.get(ticker).analyze()
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        traceback.print_exc()

# build html page
html_dir = os.path.join(os.path.dirname(__file__), "html")
if os.path.exists(html_dir):
    shutil.rmtree(html_dir)

for ticker in tickers:
    Ticker.get(ticker).add_to_html()

