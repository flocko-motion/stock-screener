# Step 1: Data Loading
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import time
import os
from datetime import datetime, timedelta
import math

date_epoch_start = datetime(2009, 1, 1)


class Ticker:

    tickers = {}

    @classmethod
    def get(cls, ticker):
        if ticker not in cls.tickers:
            cls.tickers[ticker] = cls(ticker)
        return cls.tickers[ticker]

    def __init__(self, ticker):
        self.name = ticker
        self.ticker = ticker
        self.cache_file = os.path.join(os.path.dirname(__file__), "cache", f"{ticker}_{print(datetime.now().strftime('%Y-%m'))}.csv")
        self.history_cache = None
        self.history_monthly_cache = None
        self.rolling_cagr_df = None
        self.total_cagr_cache = None

    def analyze(self):
        self.plot_cagr_histogram()

    def history(self):
        if self.history_cache is None:
            self.history_cache = self.load_financial_data()
        return self.history_cache

    def history_monthly(self):
        if self.history_monthly_cache is None:
            self.history_monthly_cache = self.history().resample('MS').last()
        return self.history_monthly_cache

    def rolling_cagr(self):
        if self.rolling_cagr_df is None:
            self.rolling_cagr_df = self.calculate_rolling_cagr()
        return self.rolling_cagr_df

    def load_financial_data(self):
        if os.path.exists(self.cache_file):
            print(f"{self.ticker} - loading from cache")
            price_history = pd.read_csv(self.cache_file, index_col='Date', parse_dates=True)
        else:
            print(f"{self.ticker} - loading from Yahoo Finance")
            # Fetch adjusted data from Yahoo Finance
            ticker_info = yf.Ticker(self.ticker)
            time.sleep(2)  # Adding a 2-second delay between requests to avoid being rate-limited
            price_history = ticker_info.history(period="max", auto_adjust=True) # , currency="EUR")
            if len(price_history) == 0:
                raise ValueError("No data found for the given stock symbol")
            price_history.to_csv(self.cache_file)  # Save the data to avoid reloading frequently

        price_history.index = pd.to_datetime(price_history.index, errors='coerce', utc=True)
        price_history = price_history.dropna(subset=['Close'])
        price_history = price_history[price_history.index >= pd.to_datetime(date_epoch_start, utc=True)]
        return price_history

    # Function to plot the histogram of rolling CAGR with total CAGR line
    def plot_cagr_histogram(self):
        print(f"plotting {self.ticker}")
        rolling_cagr_df = self.rolling_cagr()
        plt.figure(figsize=(10, 6))
        plt.hist(rolling_cagr_df['1Y CAGR Class'], bins=20, edgecolor='gray', alpha=0.75)
        # plt.axvline(self.cagr_to_class(self.total_cagr()), color='red', linestyle='dashed', linewidth=2,
        #             label=f'SPX CAGR: {Ticker.get("^SPX").total_cagr():.2%}')
        total_cagr_class = self.cagr_to_class(self.total_cagr())
        plt.axvline(total_cagr_class, color='red', linestyle='dashed', linewidth=2,
                    label=f'Total CAGR: {(self.total_cagr() - 1):.2%}')
        plt.title(f'{self.name}', fontsize=14)
        plt.xlabel('CAGR', fontsize=12)
        plt.ylabel('Frequency', fontsize=12)
        x_min = -15
        x_max = 30
        plt.xlim(x_min, x_max)

        # Generate custom labels using a formula
        x_ticks = range(x_min, x_max)
        x_labels = [f'{round((self.class_to_cagr(x) - 1) * 100)}' for x in x_ticks]  # Example formula: multiply by 2 and add a percentage sign

        # Set custom x-axis ticks and labels
        plt.xticks(ticks=x_ticks, labels=x_labels)

        plt.legend()
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.show()

    # Function to calculate 1-year rolling CAGR
    def calculate_rolling_cagr(self):
        history = self.history_monthly()
        rolling_cagr = []
        rolling_cagr_class = []
        for i in range(12, len(history)):
            start_price = history.iloc[i - 12]
            end_price = history.iloc[i]
            cagr = (end_price.Close / start_price.Close)  # we're already in annual - so not much to do here
            rolling_cagr.append(cagr)
            rolling_cagr_class.append(Ticker.cagr_to_class(cagr))
        # Create a DataFrame with the results
        rolling_cagr_df = pd.DataFrame({
            'Date': history.index[0:-12],
            '1Y CAGR': rolling_cagr,
            '1Y CAGR Class': rolling_cagr_class,
        })
        return rolling_cagr_df

    # Function to calculate total CAGR from start to end
    def total_cagr(self):
        if not (self.total_cagr_cache is None):
            return self.total_cagr_cache
        hist = self.history()
        start_price = hist['Close'].iloc[0]
        end_price = hist['Close'].iloc[-1]
        num_years = (hist.index[-1] - hist.index[0]).days / 365.25
        self.total_cagr_cache = (end_price / start_price) ** (1 / num_years)
        return self.total_cagr_cache

    @classmethod
    def cagr_to_class(cls, cagr):
        return round(math.log(cagr) / math.log(1.025))

    @classmethod
    def class_to_cagr(cls, cagr_class):
        return 1.025 ** cagr_class



# ^SPX



Ticker.get("AAPL").analyze()
Ticker.get("ZURVY").analyze()
