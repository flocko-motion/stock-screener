import os

import pandas as pd
import requests
import json

from lib.cache import get_cache_path
from lib.ticker_info import TickerInfo
from lib.watchdog import watchdog

# Read the API key from the file
key_file_path = os.path.join(os.path.dirname(__file__), '..', 'api-keys', 'financialmodelingprep.key')
with open(key_file_path, 'r') as file:
    API_KEY = file.read().strip()

def load_ticker(ticker: str):
    ticker = ticker.replace(".", "-")
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

def api_get(endpoint, params=None):
    if params is None:
        params = {}
    params["apikey"] = API_KEY
    url = f"https://financialmodelingprep.com/api/v3/{endpoint}"
    response = requests.get(url, params)
    data = response.json()
    return data

def search(query: str):
    return api_get(f"search", {"query":query})

def etf_holder(ticker: str):
    return api_get(f"etf-holder/{ticker}")

def load_ticker_fundamentals(ticker: str):
    # Path to cache the fundamentals
    fundamentals_path = get_cache_path(ticker, "fmp_fundamentals", "pkl")
    if os.path.exists(fundamentals_path):
        print(f"Loading {ticker} fundamentals from cache..")
        return pd.read_pickle(fundamentals_path)

    # Fetch fundamentals
    url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={API_KEY}"
    response = requests.get(url)
    fundamentals_data = response.json()
    if response.status_code != 200:
        print(f"Error fetching fundamentals data for {ticker}: {fundamentals_data}")
        return None

    if not fundamentals_data:
        print(f"No fundamentals data found for {ticker}.")
        return None

    # Convert to DataFrame for easier caching and usage
    df = None
    try:
        df = pd.DataFrame(fundamentals_data)
    except Exception as e:
        print(f"Error converting fundamentals data to DataFrame: {e}")
        print(fundamentals_data)
        raise e

    # Cache the data
    df.to_pickle(fundamentals_path)
    return df

@watchdog(timeout=10, retries=3)
def load_ticker_history(ticker: str):
    history_path = get_cache_path(ticker, "fmp_history", "pkl")
    if os.path.exists(history_path):
        print(f"Loading {ticker} from cache..")
        df = pd.read_pickle(history_path)
        return df

    # Optional parameters (date range)
    params = {
        "from": "2000-01-01",
        # "to": "2023-12-31"
    }

    # Fetch historical prices
    prices_url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?apikey={API_KEY}"
    prices_response = requests.get(prices_url, params)
    prices_data = prices_response.json().get("historical", [])
    if prices_response.status_code != 200:
        print(f"Error data for {ticker} from {prices_url}")
        raise Exception(prices_data)

    prices_df = pd.DataFrame(prices_data)
    prices_df["date"] = pd.to_datetime(prices_df["date"])
    prices_df = prices_df.sort_values(by="date")

    df = prices_df[["date", "adjClose"]]
    df = df.rename(columns={"adjClose": "close"})
    first_close = df["close"].iloc[0]
    df["close"] = df["close"] / first_close * 100
    # set the date as the index
    df.set_index("date", inplace=True)
    df.to_pickle(history_path)
    return df

# load_ticker("AAPL")