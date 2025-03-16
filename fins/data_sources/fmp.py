import hashlib
import os
import sys

import pandas as pd
import requests
import json
import threading
import time
from .cache import (
    get_cache_path, 
    cache_api_response, 
    is_cache_valid, 
    set_cache_expiry
)
from lib.ticker_info import TickerInfo
from .watchdog import watchdog


# Read the API key from the file
key_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'api-keys', 'financialmodelingprep.key')
try:
    with open(key_file_path, 'r') as file:
        API_KEY = file.read().strip()
    
    # Print the first few characters of the API key for debugging
    print(f"FMP API key loaded successfully. Length: {len(API_KEY)}, First chars: {API_KEY[:3]}...")
    
    # Crash immediately if API key is empty or too short
    if not API_KEY or len(API_KEY) < 10:
        print(f"ERROR: Invalid FMP API key found in {key_file_path}. Key is empty or too short.")
        sys.exit(1)
except Exception as e:
    print(f"ERROR loading FMP API key from {key_file_path}: {str(e)}")
    sys.exit(1)

def load_ticker(ticker: str):
    # ticker = ticker.replace(".", "-")
    fundamentals_raw = load_ticker_fundamentals(ticker)
    if fundamentals_raw is None:
        raise ValueError(f"No fundamentals data found for ticker '{ticker}'.")
    fundamentals = to_ticker_info(fundamentals_raw)
    history = load_ticker_history(ticker)
    return fundamentals, history

def to_ticker_info(fundamentals):
    if len(fundamentals) == 0:
        raise ValueError("No fundamentals data found.")
    fundamentals = fundamentals.iloc[0]
    info = TickerInfo(
        ticker=fundamentals["symbol"],
        name=str(fundamentals["companyName"]),
        exchange=str(fundamentals["exchange"]),
        currency=str(fundamentals["currency"]),
        industry=str(fundamentals["industry"]),
        sector=str(fundamentals["sector"]),
        country=str(fundamentals["country"]),
        market_cap=float(fundamentals["mktCap"]),
        beta=fundamentals["beta"],
        # trailing_pe=fundamentals["trailing_pe"],
        # forward_pe=fundamentals["forward_pe"]
    )
    return info

# Initialize a lock and a variable to store the last request time
rate_limit_lock = threading.Lock()
last_request_time = 0
RATE_LIMIT_INTERVAL = 0.25

# Print rate limit settings
print(f"FMP rate limit interval set to {RATE_LIMIT_INTERVAL} seconds")

def api_get(endpoint, params=None):
    """
    Make an API request to the FMP API with rate limiting and caching.
    
    Args:
        endpoint: The API endpoint to request
        params: Optional parameters for the request
        
    Returns:
        The JSON response from the API
    """
    global last_request_time
    
    if params is None:
        params = {}
    
    url = f"https://financialmodelingprep.com/api/v3/{endpoint}"
    
    # Define a function to fetch the data if not in cache
    def fetch_data():
        global last_request_time
        with rate_limit_lock:
            current_time = time.time()
            elapsed_time = current_time - last_request_time
            if elapsed_time < RATE_LIMIT_INTERVAL:
                time.sleep(RATE_LIMIT_INTERVAL - elapsed_time)
            
            # Update the last request time
            last_request_time = time.time()
            
            # Print the URL being fetched
            params_url_string = "&".join([f"{k}={v}" for k, v in params.items()])
            print(f"Fetching {url}?{params_url_string}")
        
        # Add API key to params dictionary
        request_params = params.copy()
        request_params["apikey"] = API_KEY
        
        # Make the request
        response = requests.get(url, params=request_params)
        if response.status_code != 200:
            raise Exception(f"Error fetching data from {url}: {response.json()}")
        
        return response.json()
    
    # Use the cache_api_response function to handle caching
    return cache_api_response(endpoint, params, fetch_data)

def search(query: str):
    return api_get(f"search", {"query":query})

def profile(ticker: str):
    return api_get(f"profile/{ticker}")

def quote(ticker):
    return api_get(f"quote/{ticker}")

def search_name(query: str):
    return api_get(f"search-name", {"query":query})

def tradeable_symbols():
    return api_get(f"available-traded/list")

def etf_holder(ticker: str):
    return api_get(f"etf-holder/{ticker}")

def load_ticker_fundamentals(ticker: str):
    fundamentals_data = api_get(f"profile/{ticker}")
    try:
        return pd.DataFrame(fundamentals_data)
    except Exception as e:
        print(f"Error converting fundamentals data to DataFrame: {e}")
        print(fundamentals_data)
        raise e


@watchdog(timeout=10, retries=3)
def load_ticker_history(ticker: str):
    history_path = get_cache_path(ticker, "fmp_history", "pkl")
    if os.path.exists(history_path) and is_cache_valid(history_path):
        print(f"Loading {ticker} from cache..")
        df = pd.read_pickle(history_path)
        return df

    prices_response = api_get(f"historical-price-full/{ticker}", params)
    prices_data = prices_response.get("historical", [])

    prices_df = pd.DataFrame(prices_data)
    prices_df["date"] = pd.to_datetime(prices_df["date"])
    prices_df = prices_df.sort_values(by="date")

    df = prices_df[["date", "adjClose"]]
    df = df.rename(columns={"adjClose": "close"})
    # first_close = df["close"].iloc[0]
    # df["close"] = df["close"] / first_close * 100
    # set the date as the index
    df.set_index("date", inplace=True)
    df.to_pickle(history_path)
    
    # Set cache expiry (1 week)
    set_cache_expiry(history_path, 7 * 24 * 3600)
    
    return df

