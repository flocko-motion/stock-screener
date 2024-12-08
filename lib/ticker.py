# Step 1: Data Loading
import colorsys
import shutil

from lib.cache import get_cache_time, get_cache_path
from lib.yahoo_finance import yahoo_ticker
from lib.watchdog import watchdog

import yaml
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import time
import os
from datetime import datetime, timedelta
import math
import lib.yahoo_finance as fin_db

from matplotlib import patches

date_epoch_start = datetime(2009, 1, 1)

cagr_class_exponent = 1.10

class Ticker:

    tickers = {}




    @classmethod
    def get(cls, ticker: str):
        if ticker not in cls.tickers:
            cls.tickers[ticker] = cls(ticker)
        return cls.tickers[ticker]

    def __init__(self, ticker: str):
        self.ticker = ticker
        self.info = None
        get_cache_time()
        self.cache_file_history = get_cache_path(self.ticker, "history", "csv")
        self.cache_file_info = get_cache_path(self.ticker, "meta", "yaml")
        self.cache_file_plot = get_cache_path(self.ticker, "plot", "png")
        self.history_cache = None
        self.history_monthly_cache = None
        self.rolling_cagr_df = None
        self.total_cagr_cache = None

    def analyze(self):
        time_start = time.time()
        self.history()
        time_end = time.time()
        print(f"Loading data: {time_end - time_start:.2f} seconds")
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

    def info_save(self, info):
        try:
            yaml.dump(info, open(self.cache_file_info, "w"))
            self.info_load()
        except Exception as e:
            print(f"Error saving info for {self.ticker}: {e}")
            raise e

    def info_load(self):
        self.info = yaml.load(open(self.cache_file_info, "r"), Loader=yaml.FullLoader)



    def load_financial_data(self):
        print(f"{self.ticker} - loading from Yahoo Finance")

        ticker_info, price_history =fin_db.load_ticker(self.ticker)
        self.info_save(ticker_info)

        if len(price_history) == 0:
            raise ValueError(f"No data found for the given stock symbol: {self.ticker}")

        price_history.index = pd.to_datetime(price_history.index, errors='coerce', utc=True)

        price_history = price_history.dropna(subset=['Close'])
        price_history = price_history[price_history.index >= pd.to_datetime(date_epoch_start, utc=True)]
        for i in ["Open", "High", "Low", "Close"]:
            price_history[i] = price_history[i] / price_history[i].iloc[0] * 100
        return price_history

    @classmethod
    def gain_to_color(cls, gain):
        # Ensure the gain is a float for consistent calculation
        gain = float(gain)

        # Define parameters for hue calculation
        center_gain = 1.10
        lower_bound = 0.5
        upper_bound = 2.0

        if gain < center_gain:
            # Gains below 1.10: Map hue from orange (30 degrees) to deep purple (270 degrees)
            # As gain moves from 1.10 to 0.5, hue shifts from 30 to 270.
            min_gain, max_gain = lower_bound, center_gain
            min_hue, max_hue = 70 / 360.0, 10 / 360.0
            hue = max_hue - (max(0, (gain - min_gain) / (max_gain - min_gain))) * (max_hue - min_hue)
        else:
            # Gains above 1.10: Map hue from green (120 degrees) to cyan (180 degrees)
            # As gain moves from 1.10 to 1.8, hue shifts from 120 to 180.
            min_gain, max_gain = center_gain, upper_bound
            min_hue, max_hue = 70 / 360.0, 250 / 360.0
            hue = min_hue + (min(1, (gain - min_gain) / (max_gain - min_gain))) * (max_hue - min_hue)

        # Set saturation and value (brightness) high for background visibility
        saturation = 0.9
        value = 0.95

        # Convert HSV to RGB
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)

        # Convert RGB to hex
        r_hex = int(r * 255)
        g_hex = int(g * 255)
        b_hex = int(b * 255)

        return f'#{r_hex:02X}{g_hex:02X}{b_hex:02X}'

    def add_to_html(self):
        plots_dir = os.path.join(os.path.dirname(__file__), "html", "plots")
        os.makedirs(plots_dir, exist_ok=True)
        plot_path = os.path.join(plots_dir, f"{self.ticker}_plot.png")
        if not os.path.exists(self.cache_file_plot):
            print(f"Skipping {self.ticker} - no plot")
            return
        shutil.copyfile(self.cache_file_plot, plot_path)

        html_file_path = os.path.join(os.path.dirname(__file__), "html", "index.html")
        # Attach the saved plot to index.html
        with open(html_file_path, "a") as html_file:
            # Append an <img> tag pointing to the saved plot
            html_file.write(
                f'<img src="plots/{self.ticker}_plot.png" alt="{self.ticker} plot" style="width:100%; max-width:600px;">\n')

    @watchdog(10, 3)
    def plot_cagr_histogram(self):
        if os.path.exists(self.cache_file_plot):
            print(f"{self.ticker} - plot exists")
            return

        print(f"plotting {self.ticker}")
        time_start = time.time()
        rolling_cagr_df = self.rolling_cagr()
        # Plot the price history on the second axis (ax2)
        price_history = self.history()
        min_price = 50
        max_price = 100000
        years = price_history.index.year.unique()  # Get unique years from the price history

        print(f"Rolling CAGR calculation took {time.time() - time_start:.2f} seconds")

        time_start = time.time()

        # Create figure with two subplots, one for histogram and one for price history
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 6), gridspec_kw={'width_ratios': [1, 1]})

        # Plot the histogram on the first axis (ax1)
        custom_bins = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        rolling_cagr_values = rolling_cagr_df['1Y CAGR Class']
        ax1.hist([rolling_cagr_values[rolling_cagr_values < 0], rolling_cagr_values[rolling_cagr_values >= 0]],
                 bins=custom_bins, edgecolor='gray', alpha=0.75, stacked=True, color=['red', 'green'])

        # Add vertical lines for zero CAGR and total CAGR
        total_cagr_class = self.cagr_to_class(self.total_cagr(), float=True)
        ax1.axvline(0, color='gray', linestyle='-', linewidth=2, label=f'Zero CAGR')
        ax1.axvline(total_cagr_class, color='black', linestyle='--', linewidth=4,
                    label=f'Total CAGR: {(self.total_cagr() - 1):.2%}')
        ax1.set_title(f'{self.info["name"]} - CAGR Histogram', fontsize=14)
        ax1.set_xlabel('CAGR', fontsize=12)
        ax1.set_ylabel('Frequency', fontsize=12)
        ax1.set_xlim(-10, 15)
        ax1.grid(axis='y', linestyle='--', alpha=0.7)

        # Generate custom labels using a formula
        x_ticks = range(-10, 12)
        x_labels = [f'{Ticker.class_to_cagr_pct(x)}' for x in x_ticks]
        ax1.set_xticks(ticks=x_ticks)
        ax1.set_xticklabels(labels=x_labels)
        ax1.legend(loc='upper left')

        print(f"Histogram construction: {time.time() - time_start:.2f} seconds")

        time_start = time.time()


        for year in years:
            yearly_data = price_history[price_history.index.year == year]
            if len(yearly_data) < 2:
                continue  # Skip years with insufficient data

            # Calculate gain multiplier (end of year divided by start of year)
            gain = yearly_data['Close'].iloc[-1] / yearly_data['Close'].iloc[0]

            # Get color for the given year's gain
            color = self.__class__.gain_to_color(gain)

            # Define the rectangle representing the year, using pd.Timedelta for width
            start_date = yearly_data.index[0]
            end_date = yearly_data.index[-1]
            width = (end_date - start_date).days

            # Set y to the bottom of the axis and make height cover the full range
            y_min, y_max = ax2.get_ylim()  # Get the current y-axis limits

            # Add the rectangle patch to ax2
            ax2.add_patch(patches.Rectangle(
                (start_date, y_min),  # Starting position (x, y)
                pd.Timedelta(days=width),  # Width in days
                height=max_price, # y_max - y_min,  # Full height to cover from y_min to y_max
                color=color,
                alpha=0.2,  # Transparency
                zorder=-1  # Put it in the background
            ))

        ax2.plot(price_history.index, price_history['Close'], color='green', linestyle='-', linewidth=1.5,
                 label='Price History')
        ax2.set_title(f'{self.info["name"]} - Price History', fontsize=14)
        ax2.set_ylabel('Price', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.grid(axis='y', linestyle='--', alpha=0.7)

        # Format the x-axis labels to show dates clearly without overlapping
        # ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
        # ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fig.autofmt_xdate()  # Automatically format x labels for better readability

        # Add a legend to the price history
        ax2.legend(loc='upper right')
        ax2.set_yscale('log')

        # Manually set y-axis ticks for better readability with more labels
        y_ticks = []
        for i in range(int(np.floor(np.log10(min_price))), int(np.ceil(np.log10(max_price))) + 1):
            y_ticks.extend([1 * 10 ** i, 2 * 10 ** i, 5 * 10 ** i])
        # Filter y_ticks to ensure they lie within the range [min_price, max_price]
        y_ticks = [tick for tick in y_ticks if min_price <= tick <= max_price]

        ax2.set_yticks(y_ticks)
        ax2.set_ylim(min_price, max_price)
        ax2.set_xlim(date_epoch_start, datetime.now())

        # Set y-axis labels to normal numeric format without exponential notation
        ax2.get_yaxis().set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,}'))


        print(f"Price history construction: {time.time() - time_start:.2f} seconds")

        time_start = time.time()

        # Tight layout to ensure proper spacing between subplots
        plt.tight_layout()

        plt.savefig(self.cache_file_plot, dpi=300, bbox_inches='tight')  # Save with high resolution and trimmed whitespace

        plt.show()

        plt.close()

        print(f"Plotting: {time.time() - time_start:.2f} seconds")

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
    def cagr_to_class(cls, cagr, float=False):
        c = (math.log(cagr) / math.log(cagr_class_exponent))
        if float:
            return c
        return round(c)

    @classmethod
    def class_to_cagr(cls, cagr_class):
        return cagr_class_exponent ** cagr_class

    @classmethod
    def class_to_cagr_pct(cls, cagr_class):
        return cls.dec_to_pct(cls.class_to_cagr(cagr_class))

    @classmethod
    def dec_to_pct(cls, dec):
        return f"{round((dec -1) * 100)}%"



# ^SPX
def print_gain_colors():
    def frange(start, stop, step):
        while start <= stop:
            yield start
            start += step


    # Generate gain values
    gain_values = [round(x, 2) for x in list(frange(0.5, 2.05, 0.05))]

    # Create a plot to visualize the colors corresponding to each gain value
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot each gain as a colored bar
    for i, gain in enumerate(gain_values):
        color = Ticker.gain_to_color(gain)
        rect = patches.Rectangle((i, 0), 1, 1, color=color)
        ax.add_patch(rect)
        ax.text(i + 0.5, 0.5, f'{gain:.2f}', va='center', ha='center', fontsize=8, color='black')

    # Set limits and labels for the axes
    ax.set_xlim(0, len(gain_values))
    ax.set_ylim(0, 1)
    ax.axis('off')  # Hide the axis for better visual effect

    plt.title('Gain-to-Color Visualization')
    plt.show()
