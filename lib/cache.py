import os
from datetime import datetime


rootpath = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def get_cache_path(ticker: str, identifier: str, extension: str) -> str:
	cache_path = os.path.join(rootpath, "cache", identifier, f"{ticker}.{extension}")
	os.makedirs(os.path.dirname(cache_path), exist_ok=True)
	return cache_path


def delete_if_not_from_this_month(file_path: str):
	if not os.path.exists(file_path):
		return
	file_timestamp = os.path.getmtime(file_path)
	file_date = datetime.fromtimestamp(file_timestamp)
	now = datetime.now()
	if file_date.year != now.year or file_date.month != now.month:
		print(f"Deleting outdated cache file: {file_path}")
		os.remove(file_path)


def valid_until_end_of_month(output_file):
	if not os.path.exists(output_file):
		return
	now = datetime.now()
	if now.month == 12:  # If December, move to January of the next year
		next_month = datetime(year=now.year + 1, month=1, day=1)
	else:
		next_month = datetime(year=now.year, month=now.month + 1, day=1)
	next_month_timestamp = next_month.timestamp()
	os.utime(output_file, (next_month_timestamp, next_month_timestamp))
