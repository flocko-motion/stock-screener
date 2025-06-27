import os
import sys
from datetime import datetime
from urllib.parse import urlencode

import pandas as pd
import requests
import threading
import time

from typing import Dict, Any

from .cache import (
    get_cache_path, 
    cache_api_response, 
    is_cache_valid, 
    set_cache_expiry
)
from .watchdog import watchdog

DEBUG = False

# Read the API key from the file
key_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'api-keys', 'financialmodelingprep.key')

def log_debug(out, channel=sys.stdout):
    if DEBUG:
        print(out, channel)

def log_err(out):
    print(out)

try:
    with open(key_file_path, 'r') as file:
        API_KEY = file.read().strip()
    
    # Print the first few characters of the API key for debugging
    log_debug(f"FMP API key loaded successfully. Length: {len(API_KEY)}, First chars: {API_KEY[:3]}...", channel=sys.stderr)
    
    # Crash immediately if API key is empty or too short
    if not API_KEY or len(API_KEY) < 10:
        log_debug(f"ERROR: Invalid FMP API key found in {key_file_path}. Key is empty or too short.", channel=sys.stderr)
        sys.exit(1)
except Exception as e:
    log_debug(f"ERROR loading FMP API key from {key_file_path}: {str(e)}", channel=sys.stderr)
    sys.exit(1)

# Initialize a lock and a variable to store the last request time
rate_limit_lock = threading.Lock()
last_request_time = 0
use_cache = False

class ApiLimitationException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

class ApiBadRequestException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

RATE_LIMIT_INTERVAL = (60 / 300) * 2  # 600/m should be allowed, we slow down by a factor to be safe
log_debug(f"FMP rate limit interval set to {RATE_LIMIT_INTERVAL} seconds", channel=sys.stderr)

def rate_limit_enforce():
    """Enforce rate limiting between requests."""
    global last_request_time
    with rate_limit_lock:
        current_time = time.time()
        elapsed_time = current_time - last_request_time
        last_request_time = time.time()

    if elapsed_time < RATE_LIMIT_INTERVAL:
        sleep_interval = RATE_LIMIT_INTERVAL - elapsed_time
        # debug_print(f"sleep {sleep_interval} seconds")
        time.sleep(sleep_interval)


def rate_limit_recover():
    with rate_limit_lock:
        seconds = 60
        print("")
        for s in range(seconds):
            print(f"\rFMP API rate limit exceeded - recover {seconds - s} s              ", end='', flush=True)
            time.sleep(1)
            print(f"\rFMP API rate limit recovered for {seconds} s                        ")


def api_get(endpoint, params=None, max_retries=5, base_delay=3):
    """
    Make an API request to the FMP API with rate limiting and caching.
    
    Args:
        endpoint: The API endpoint to request
        params: Optional parameters for the request
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
        
    Returns:
        The JSON response from the API
        
    Raises:
        ApiBadRequestException: For 400 status code
        ApiLimitationException: For 402 status code
        Exception: For other errors after retries
    """
    url = f"https://financialmodelingprep.com/{endpoint}"
    request_params = (params or {}).copy()
    request_params["apikey"] = API_KEY

    def handle_response(response):
        if response.status_code == 200:
            return response.json()
        if response.status_code == 400:
            raise ApiBadRequestException(response.content)
        if response.status_code == 402:
            raise ApiLimitationException(response.content)
        raise Exception(f"API error: {response.status_code} - {response.content}")

    def make_request():
        rate_limit_enforce()
        log_debug(f"Fetching {url}?{urlencode(request_params)}")
        return requests.get(url, params=request_params)


    def fetch_data():
        for attempt in range(max_retries):
            try:
                response = make_request()
                return handle_response(response)
            except ApiLimitationException:
                rate_limit_recover()
                continue
            except ApiBadRequestException:
                raise
            except requests.exceptions.ConnectionError as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Connection failed after {max_retries} attempts: {e}")
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                log_err(f"Connection error, retrying in {delay}s: {e}")
                time.sleep(delay)
            except Exception as e:
                if "API error: 429" in str(e):
                    rate_limit_recover()
                    continue
                raise Exception(f"Request failed: {type(e)} {e}")
        raise Exception("failed to fetch data")

    if use_cache:
        return cache_api_response(endpoint, params, fetch_data)
    else:
        return fetch_data()

def search(query: str):
    return api_get(f"api/v3/search", {"query":query})

def screen(mcap_min: int = None, mcap_max: int = None, type: str = "all", sector: str = None, industry: str = None, country: str = None, exchange: str = None, limit: int = 1000) -> list[str]:
    params: Dict[str, Any] = {
        "limit": limit,
    }
    if mcap_min:
        params["marketCapMoreThan"] = mcap_min
    if mcap_max:
        params["marketCapLowerThan"] = mcap_max
    if type == "etf":
        params["isEtf"] = True
    elif type == "fund":
        params["isFund"] = True
    elif type == "stock":
        params["isStock"] = True
    if sector:
        params["sector"] = sector
    if industry:
        params["industry"] = industry
    if country:
        params["country"] = country
    if exchange:
        params["exchange"] = exchange
    res = api_get(f"stable/company-screener", params)
    return [item.get("symbol") for item in res]

def profile(ticker: str):
    res = api_get(f"stable/profile", {"symbol":ticker})
    if len(res) == 0:
        raise ValueError(f"No profile for {ticker}")
    elif len(res) > 1:
        raise ValueError(f"More than one profile for {ticker}")
    return res[0]

def profile_index(ticker: str):
    items = api_get(f"stable/quote", {"symbol":ticker})
    if len(items) == 0:
        raise ValueError("symbol not found")
    if len(items) > 1:
        raise ValueError("multiple symbols found")
    return items[0]

def profile_etf(ticker: str):
    items = api_get(f"stable/etf/info", {"symbol": ticker})
    if len(items) == 0:
        raise ValueError("symbol not found")
    if len(items) > 1:
        raise ValueError("multiple symbols found")
    return items[0]

def profile_crypto(ticker: str):
    items = api_get(f"stable/cryptocurrency-list", {"symbol": ticker})
    item = next((item for item in items if item.get("symbol") == ticker), None)
    if item is None:
        raise ValueError("symbol not found")
    return item

def quote(ticker):
    res = api_get(f"stable/quote", {"symbol":ticker})
    if len(res) == 0:
        raise ValueError(f"No quote for {ticker}")
    if len(res) > 1:
        raise ValueError("multiple symbols found")
    return res[0]

def outlook(ticker):
    """ combined info on a stock or ETF """
    res = api_get(f"api/v4/company-outlook", {"symbol":ticker})
    return res


def search_name(query: str):
    return api_get(f"stable/search-name", {"query":query})

def tradeable_symbols():
    return api_get(f"api/v3/available-traded/list")

def all_stocks():
    res = api_get(f"stable/stock-list")
    return [item.get("symbol") for item in res]

def all_etfs():
    res = api_get(f"stable/etf-list")
    return [item.get("symbol") for item in res]

def all_cryptos():
    res = api_get(f"stable/cryptocurrency-list")
    return [item.get("symbol") for item in res]

def etf_holder(ticker: str):
    return api_get("funds/disclosure-holders-latest",{"symbol":ticker})

def clean_time_series_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean time series data by removing NaN values at the beginning and end,
    and interpolating NaN values in the middle of the series.
    
    Args:
        df: DataFrame with 'date' and OHLC columns
        
    Returns:
        Cleaned DataFrame with NaN values handled
    """
    if df.empty:
        return df
    
    df_clean = df.copy()
    price_columns = ['open', 'high', 'low', 'avg', 'close']
    available_price_columns = [col for col in price_columns if col in df_clean.columns]
    
    if not available_price_columns:
        return df_clean
    
    # Remove rows where ALL price columns are NaN
    df_clean = df_clean.dropna(subset=available_price_columns, how='all')
    
    if df_clean.empty:
        return df_clean
    
    # Interpolate NaN values in the middle of the series
    for col in available_price_columns:
        df_clean[col] = df_clean[col].interpolate(method='linear')
    
    # Ensure OHLC relationships are maintained after interpolation
    if all(col in df_clean.columns for col in ['open', 'high', 'low', 'close']):
        # Ensure high is at least as high as open and close
        df_clean['high'] = df_clean[['high', 'open', 'close']].max(axis=1)
        # Ensure low is at most as low as open and close  
        df_clean['low'] = df_clean[['low', 'open', 'close']].min(axis=1)
        
        # Recalculate average after OHLC adjustments
        if 'avg' in df_clean.columns:
            df_clean['avg'] = (df_clean['open'] + df_clean['high'] + df_clean['low'] + df_clean['close']) / 4
    
    return df_clean

def price_history(ticker: str, date_from: datetime | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Fetch full history without date parameters
    params = {
        "symbol": ticker,
        "from":(date_from - pd.DateOffset(months=1)).strftime("%Y-%m-%d") if date_from else "1900-01-01",
    }
    prices_data = api_get(f"stable/historical-price-eod/dividend-adjusted", params)

    prices_df = pd.DataFrame(prices_data)
    prices_df["date"] = pd.to_datetime(prices_df["date"])
    prices_df = prices_df.sort_values(by="date")

    df = prices_df[["date", "adjOpen", "adjHigh", "adjLow", "adjClose"]]
    df = df.rename(columns={"adjOpen": "open", "adjHigh": "high", "adjLow":"low", "adjClose": "close"})
    df.set_index("date", inplace=True)
    df.sort_values("date")
    
    # Calculate average price (OHLC/4)
    df['avg'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4

    df_monthly = df.resample('ME').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'avg': 'mean',
        'close': 'last'
    }).reset_index()
    df_monthly = df_monthly[df_monthly['date'] < pd.Timestamp(datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0))]
    if date_from:
        df_monthly = df_monthly[df_monthly['date'] >= date_from]
    df_monthly = clean_time_series_data(df_monthly)

    df_weekly = df.resample('W').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'avg': 'mean',
        'close': 'last'
    }).reset_index()
    df_weekly = df_weekly[df_weekly['date'] < pd.Timestamp(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))]
    if date_from:        
        df_weekly = df_weekly[df_weekly['date'] >= date_from]
    df_weekly = clean_time_series_data(df_weekly)

    return df_monthly, df_weekly


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
