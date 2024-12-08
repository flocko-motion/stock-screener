import os
from datetime import datetime

rootpath = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def get_cache_time():
	return datetime.now().strftime("%Y-%m")


def get_cache_path(ticker: str, identifier: str, extension: str) -> str:
	cache_path = os.path.join(rootpath, "cache", get_cache_time(), f"{ticker}_{identifier}.{extension}")
	os.makedirs(os.path.dirname(cache_path), exist_ok=True)
	return cache_path