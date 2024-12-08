import os
import pickle
import time
import yfinance as yf

from lib.cache import get_cache_path
from typing import BinaryIO

yahoo_tickers = {
	"BRK.A": "BRK-A",
	"BRK.B": "BRK-B",
}

def yahoo_ticker(ticker: str) -> str:
	if ticker in yahoo_tickers:
		return yahoo_tickers[ticker]
	return ticker


def info_extract(ticker, ticker_info):
	info = {}
	try:
		if "longName" in ticker_info:
			info["name"] = ticker_info["longName"]
		elif "shortName" in ticker_info:
			info["name"] = ticker_info["shortName"]
		else:
			info["name"] = ticker

		if "marketCap" in ticker_info:
			info["market_cap"] = ticker_info["marketCap"]
		else:
			info["market_cap"] = None

		if "trailingPE" in ticker_info:
			info["trailing_pe"] = ticker_info["trailingPE"]
		else:
			info["trailing_pe"] = None

		if "forwardPE" in ticker_info:
			info["forward_pe"] = ticker_info["forwardPE"]
		else:
			info["forward_pe"] = None
		return info
	except Exception as e:
		print(f"Error extracting info for {ticker}: {e}")
		raise e


def api_delay(seconds):
	print("API delay 10 seconds: ", end="")
	for i in range(seconds):
		print(".", end="")
		time.sleep(1)
	print()


def load_ticker(ticker: str):
	info_path = get_cache_path(ticker, "yahoo_info", "pkl")
	history_path = get_cache_path(ticker, "yahoo_history", "pkl")

	# check cache
	try:
		if os.path.exists(history_path) and os.path.exists(info_path):
			print(f"Loading {ticker} from cache..")
			with open(info_path, "rb") as f_info:
				with open(history_path, "rb") as f_history:
					ticker_history = pickle.load(f_history)
					ticker_info = pickle.load(f_info)
					return info_extract(ticker, ticker_info), ticker_history
	except Exception as e:
		print(f"Error loading {ticker} from cache: {e}")
		os.remove(history_path)
		os.remove(info_path)

	# fetch data
	print(f"Loading {ticker} from yahoo finance API..")
	api_delay(10)
	ticker_info = yf.Ticker(yahoo_ticker(ticker))
	ticker_history = ticker_info.history(period="max", auto_adjust=True)  # , currency="EUR")

	try:
		with open(history_path, "wb") as f:
			pickle.dump(ticker_history, f)
		with open(info_path, "wb") as f:
			pickle.dump(ticker_info.info, f)
	except Exception as e:
		os.remove(history_path)
		os.remove(info_path)

	return info_extract(ticker, ticker_info.info), ticker_history