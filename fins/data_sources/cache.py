import os
import json
import time
import hashlib
from datetime import datetime
from typing import Any, Dict, Optional, Union, Callable


_original_rootpath = rootpath = os.path.expanduser("~/.fins/cache")
os.makedirs(rootpath, exist_ok=True)

def set_test_cache_dir(test_dir: str):
	"""
	Set a test cache directory for testing purposes.
	
	Args:
		test_dir: The test directory to use
		
	Returns:
		The original cache directory
	"""
	global rootpath
	
	# Set the new rootpath
	rootpath = test_dir
	os.makedirs(rootpath, exist_ok=True)
	


def restore_cache_dir() -> None:
	"""
	Restore the original cache directory after testing.
	"""
	global rootpath, _original_rootpath
	
	# Restore the original rootpath
	rootpath = _original_rootpath



def get_cache_path(ticker: str, identifier: str, extension: str) -> str:
	"""
	Get the path for a ticker-specific cache file.
	
	Args:
		ticker: The ticker symbol
		identifier: The cache identifier (e.g., 'fmp_history')
		extension: The file extension (e.g., 'pkl', 'json')
		
	Returns:
		The full path to the cache file
	"""
	cache_path = os.path.join(rootpath, "cache", identifier, f"{ticker}.{extension}")
	os.makedirs(os.path.dirname(cache_path), exist_ok=True)
	return cache_path


def get_cache_path_api(filename: str) -> str:
	"""
	Get the path for an API cache file.
	
	Args:
		filename: The filename for the cache file
		
	Returns:
		The full path to the API cache file
	"""
	path_cache_api = os.path.join(rootpath, "api")
	os.makedirs(path_cache_api, exist_ok=True)
	cache_path = os.path.join(path_cache_api, filename)
	return cache_path


def delete_if_not_from_this_month(file_path: str):
	"""
	Delete a cache file if it's not from the current month.
	
	Args:
		file_path: The path to the cache file
	"""
	if not os.path.exists(file_path):
		return
	file_timestamp = os.path.getmtime(file_path)
	file_date = datetime.fromtimestamp(file_timestamp)
	now = datetime.now()
	if file_date.year != now.year or file_date.month != now.month:
		print(f"Deleting outdated cache file: {file_path}")
		os.remove(file_path)


def valid_until_end_of_month(output_file):
	"""
	Set a cache file to be valid until the end of the current month.
	
	Args:
		output_file: The path to the cache file
	"""
	if not os.path.exists(output_file):
		return
	now = datetime.now()
	if now.month == 12:  # If December, move to January of the next year
		next_month = datetime(year=now.year + 1, month=1, day=1)
	else:
		next_month = datetime(year=now.year, month=now.month + 1, day=1)
	next_month_timestamp = next_month.timestamp()
	os.utime(output_file, (next_month_timestamp, next_month_timestamp))


def set_cache_expiry(file_path: str, validity_seconds: int):
	"""
	Set a cache file to expire after a specified number of seconds.
	
	Args:
		file_path: The path to the cache file
		validity_seconds: The number of seconds the cache should be valid for
	"""
	if not os.path.exists(file_path):
		return
	expiry_time = time.time() + validity_seconds
	os.utime(file_path, (expiry_time, expiry_time))


def is_cache_valid(file_path: str) -> bool:
	"""
	Check if a cache file is still valid based on its modification time.
	
	Args:
		file_path: The path to the cache file
		
	Returns:
		True if the cache is valid, False otherwise
	"""
	if not os.path.exists(file_path):
		return False
	
	current_time = time.time()
	file_mod_time = os.path.getmtime(file_path)
	
	# If the modification time is in the future, the cache is still valid
	return current_time <= file_mod_time


def cache_api_request(resource: str, fetch_func: Callable, validity_seconds: int = 3600) -> Any:
	"""
	Cache the result of an API request.
	
	Args:
		resource: A string identifying the resource being requested
		fetch_func: A function that fetches the data if not in cache
		validity_seconds: How long the cache should be valid for (in seconds)
		
	Returns:
		The cached or freshly fetched data
	"""
	# Hash the resource string to create a unique filename
	resource_hash = hashlib.md5(resource.encode()).hexdigest()
	cache_file = get_cache_path_api(f"{resource_hash}.json")
	
	# Check if we have a valid cache file
	if is_cache_valid(cache_file):
		with open(cache_file, "r") as f:
			return json.load(f)
	
	# If not in cache or cache is invalid, fetch the data
	data = fetch_func()
	
	# Save to cache
	with open(cache_file, "w") as f:
		json.dump(data, f)
	
	# Set expiry time
	set_cache_expiry(cache_file, validity_seconds)
	
	return data


def cache_api_response(endpoint: str, params: Dict = None, 
					  fetch_func: Callable = None, 
					  validity_seconds: Optional[int] = None) -> Any:
	"""
	Cache an API response with endpoint and parameters.
	
	Args:
		endpoint: The API endpoint
		params: The parameters for the API request
		fetch_func: A function that fetches the data if not in cache
		validity_seconds: How long the cache should be valid for (in seconds)
		
	Returns:
		The cached or freshly fetched data
	"""
	if params is None:
		params = {}
	
	# Create a unique resource identifier from the endpoint and params
	resource = f"{endpoint}_{json.dumps(params)}"
	
	# Use the first part of the endpoint to determine cache validity if not specified
	if validity_seconds is None:
		eom = expiry_end_of_month()
		endpoint_cache_validity = {
			"profile": eom,
			"historical-price-full": eom,
			"quote": 24 * 3600,  # 1 day
			"search": 3600,
		}
		validity_seconds = endpoint_cache_validity.get(endpoint.split("/")[-1], 3600)
	
	return cache_api_request(resource, fetch_func, validity_seconds)


def clear_cache(identifier: Optional[str] = None):
	"""
	Clear all cache files or only those matching a specific identifier.
	
	Args:
		identifier: Optional identifier to limit which cache files are cleared
	"""
	if identifier:
		cache_dir = os.path.join(rootpath, "cache", identifier)
		if os.path.exists(cache_dir):
			for filename in os.listdir(cache_dir):
				file_path = os.path.join(cache_dir, filename)
				if os.path.isfile(file_path):
					os.remove(file_path)
			print(f"Cleared cache for {identifier}")
	else:
		# Clear all cache files
		for root, dirs, files in os.walk(rootpath):
			for file in files:
				file_path = os.path.join(root, file)
				os.remove(file_path)
		print("Cleared all cache files")


def expiry_end_of_month():
    """ number of seconds until noon on the first day of next month"""
    now = datetime.now()
    # Get the first day of next month
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1, 12, 0)  # Noon on Jan 1st of next year
    else:
        next_month = datetime(now.year, now.month + 1, 1, 12, 0)  # Noon on 1st of next month

    # Calculate seconds until that timestamp
    seconds_until_expiry = (next_month - now).total_seconds()
    return int(seconds_until_expiry)
