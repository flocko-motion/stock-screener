# Step 1: Data Loading
import colorsys
import shutil
from matplotlib import dates as mdates
from matplotlib import patches
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import time
import os
from datetime import datetime, timedelta
import math
# import lib.yahoo_finance as fin_db
import lib.financialmodelingprep as fin_db
from lib.image_processing import compress_png
from lib.cache import get_cache_time, get_cache_path
from lib.yahoo_finance import yahoo_ticker
from lib.watchdog import watchdog



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
        self.cache_file_price_history = get_cache_path(self.ticker, "price_history", "png")
        self.cache_file_cagr_histogram = get_cache_path(self.ticker, "cagr_histogram", "png")
        self.history_cache = None
        self.history_monthly_cache = None
        self.rolling_cagr_df = None
        self.total_cagr_cache = None
        self.yearly_data_cache = None

    def analyze(self):
        if self.history is None or self.info is None:
            print("No data - skipping")
            return
        time_start = time.time()
        history = self.history()
        time_end = time.time()
        if history is None:
            print(f"Loading failed: {time_end - time_start:.2f} seconds")
            return 
        else:
            print(f"Loading data: {time_end - time_start:.2f} seconds")
        self.plot_cagr_histogram()
        self.plot_price_history()

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
        print(f"{self.ticker} - loading financial data")

        try:
            self.info, price_history = fin_db.load_ticker(self.ticker)
        except Exception as e:
            raise Exception(f"Error loading {self.ticker} data: {e}")

        price_history = price_history[price_history.index >= date_epoch_start]
        price_zero = price_history.iloc[0]["close"]
        if price_zero == 0:
            raise Exception(f"First 'close' for {self.ticker} is 0")
        price_history["close"] = price_history["close"] * 100 / price_zero
        return price_history

    @classmethod
    def gain_to_color(cls, gain, brightness=0.95):
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

        # Convert HSV to RGB
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, brightness)

        # Convert RGB to hex
        r_hex = int(r * 255)
        g_hex = int(g * 255)
        b_hex = int(b * 255)

        return f'#{r_hex:02X}{g_hex:02X}{b_hex:02X}'

    def add_to_html(self, html_dir, df) -> bool:
        if not os.path.exists(self.cache_file_price_history) or not os.path.exists(self.cache_file_cagr_histogram):
            print(f"Skipping {self.ticker} - no plot")
            return False
        plots = {
            "price": self.cache_file_price_history,
            "hist": self.cache_file_cagr_histogram,
        }
        for plot_name, plot_file in plots.items():
            shutil.copyfile(plot_file, self.html_image_path(html_dir, plot_name, "full"))
            if not os.path.exists(self.html_image_path(html_dir, plot_name, "thumb")):
                compress_png(plot_file, self.html_image_path(html_dir, plot_name, "thumb"), new_width=600)
        #         return False
        # shutil.copyfile(self.cache_file_price_history, self.html_image_path(html_dir, "price", "full"))
        # shutil.copyfile(self.cache_file_cagr_histogram, self.html_image_path(html_dir, "hist", "full"))
        self.add_data_to_df(df, html_dir)
        return True

    def plot_dir(self, html_dir) -> str :
        path = os.path.join(html_dir, "plots")
        os.makedirs(path, exist_ok=True)
        return path

    def html_image_path(self, html_dir, image_name, size="full") -> str:
        return os.path.join(self.plot_dir(html_dir), f"{self.ticker}_{image_name}_{size}.png")


    @classmethod
    def init_df(cls):
        df = pd.DataFrame(columns=['Ticker', 'CAGR', 'Age', 'Years in Profit', 'Years in Loss', 'Histogram Stddev', 'Histogram Mean', 'Market Cap', 'Beta', 'Plot', 'Histogram', 'Sector'])
        df.set_index('Ticker', inplace=True)
        return df

    def add_data_to_df(self, df, html_dir):
        df.loc[self.ticker] = [
            (self.get_cagr() - 1) * 100,
            self.get_age(),
            self.get_years_profit(),
            self.get_years_loss(),
            self.get_histogram_stddev(),
            self.get_histogram_mean(),
            self.info.market_cap / 1_000_000_000,
            self.info.beta,
            self.html_image_path("", "price", "thumb"),
            self.html_image_path("", "hist", "thumb"),
            self.info.sector + " / " + self.info.industry
        ]

    def get_cagr(self) -> float:
        return self.total_cagr()

    def get_age(self) -> int:
        years = set(self.get_years())
        age = 0
        while (datetime.now().year - age - 1) in years:
            age += 1
        return age

    def get_years(self):
        return self.history().index.year.unique()

    def get_years_profit(self) -> int:
        yearly_df = self.yearly_data()
        return (yearly_df['Gain'] > 0).sum()

    def get_years_loss(self) -> int:
        yearly_df = self.yearly_data()
        return (yearly_df['Gain'] < 0).sum()

    def get_histogram_stddev(self) -> float:
        return self.rolling_cagr()["1Y CAGR"].std()

    def get_histogram_mean(self):
        cagr_values = self.rolling_cagr()["1Y CAGR"]
        # calculate geometric mean
        return np.prod(1 + cagr_values) ** (1 / len(cagr_values)) - 1


    def yearly_data(self):
        if not (self.yearly_data_cache is None):
            return self.yearly_data_cache

        price_history = self.history()
        df = pd.DataFrame(columns=['Year', 'Gain'])
        df.set_index('Year', inplace=True)

        for year in self.get_years():
            yearly_data = price_history[price_history.index.year == year]

            if len(yearly_data) < 2:
                continue  # Skip years with insufficient data

            # Calculate gain multiplier (end of year divided by start of year)
            gain = yearly_data.iloc[-1]["close"] / yearly_data.iloc[0]["close"] - 1
            df.loc[year] =  [ gain ]

        self.yearly_data_cache = df
        return df


    @watchdog(10, 3)
    def plot_cagr_histogram(self):
        output_file = f"{self.cache_file_cagr_histogram}"
        if os.path.exists(output_file):
            print(f"{self.ticker} - histogram plot exists")
            return

        print(f"Plotting histogram for {self.ticker}")
        time_start = time.time()

        rolling_cagr_df = self.rolling_cagr()
        custom_bins = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        rolling_cagr_values = rolling_cagr_df['1Y CAGR Class']

        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax1.hist(
            [
                rolling_cagr_values[rolling_cagr_values < 0],
                rolling_cagr_values[rolling_cagr_values >= 0],
            ],
            bins=custom_bins,
            edgecolor="#CCCCCC",
            alpha=0.75,
            stacked=True,
            color=['#FFAAAA', '#AAFFAA'],
        )

        total_cagr_class = self.cagr_to_class(self.total_cagr(), float=True)
        ax1.axvline(0, color='gray', linestyle=':', linewidth=1, label='Zero CAGR')

        cagr_color = Ticker.gain_to_color(self.total_cagr(), brightness=0.4)
        ax1.axvline(
            total_cagr_class,
            color=Ticker.gain_to_color(self.total_cagr(), brightness=0.4),
            linestyle='--',
            linewidth=5,
            label=f'Total CAGR: {(self.total_cagr() - 1):.2%}',
        )

        ax1.text(
            total_cagr_class,
            ax1.get_ylim()[1] * 0.9,  # Position near the top of the plot
            f'{(self.total_cagr() -1) * 100:.2f}%',
            color=cagr_color,
            fontsize=24,  # Larger font size for emphasis
            fontweight='bold',
            ha='center',  # Center the text horizontally on the line
            va='center',  # Vertically align the text
            bbox=dict(facecolor='white', alpha=0.8, edgecolor="#AAAAAA")  # Add a white background to the label
        )

        ax1.set_title(f'{self.ticker} ({self.info.name}) CAGR Histogram', fontsize=14)
        ax1.set_xlabel('CAGR', fontsize=12)
        ax1.set_ylabel('Frequency', fontsize=12)
        ax1.set_xlim(-10, 10)
        ax1.grid(axis='y', linestyle='--', alpha=0.7)

        x_ticks = range(-10, 12)
        x_labels = [f'{Ticker.class_to_cagr_pct(x)}' for x in x_ticks]
        ax1.set_xticks(ticks=x_ticks)
        ax1.set_xticklabels(labels=x_labels)
        ax1.legend(loc='upper left')

        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        # plt.show()
        plt.close()

        print(f"Histogram plotting took {time.time() - time_start:.2f} seconds")

    @watchdog(10, 3)
    def plot_price_history(self):
        output_file = f"{self.cache_file_price_history}"
        if os.path.exists(output_file):
            print(f"{self.ticker} - price history plot exists")
            return

        print(f"Plotting price history for {self.ticker}")
        time_start = time.time()

        price_history = self.history()
        min_price = 50
        max_price = 100000
        df_by_year = self.yearly_data()

        fig, ax2 = plt.subplots(figsize=(10, 6))

        from matplotlib.dates import date2num


        for year in self.get_years():
            gain = df_by_year.loc[year]["Gain"]
            color = self.__class__.gain_to_color(gain + 1)

            start_date = datetime(year, 1, 1, 0, 0)
            end_date = datetime(year, 12, 31, 23, 59)

            start_date_num = date2num(start_date)
            end_date_num = date2num(end_date)

            ax2.add_patch(
                patches.Rectangle(
                    (start_date_num, min_price),
                    (end_date - start_date).days,
                    max_price - min_price,
                    color=color,
                    alpha=0.2,
                    zorder=-1,
                )
            )

        ax2.plot(
            price_history.index.to_pydatetime(),
            price_history['close'],
            color='green',
            linestyle='-',
            linewidth=1.5,
            label='Price History',
        )

        ax2.set_title(f'{self.ticker} ({self.info.name}) - Price History', fontsize=14)
        ax2.set_ylabel('Price', fontsize=12)
        ax2.set_xlabel('Year', fontsize=12)
        ax2.grid(axis='y', linestyle='--', alpha=0.7)
        ax2.xaxis_date()
        fig.autofmt_xdate()

        y_ticks = []
        for i in range(int(np.floor(np.log10(min_price))), int(np.ceil(np.log10(max_price))) + 1):
#            y_ticks.extend([1 * 10 ** i, 1.8 * 10 ** i, 3.2 * 10 ** i, 5.6 * 10 ** i])
#            y_ticks.extend([1 * 10 ** i, 2.15 * 10 ** i, 4.64 * 10 ** i])
            y_ticks.extend([1 * 10 ** i, 2 * 10 ** i, 5 * 10 ** i])
        y_ticks = [tick for tick in y_ticks if min_price <= tick <= max_price]

        ax2.set_yscale('log')
        ax2.set_ylim(min_price, max_price)
        ax2.set_yticks(y_ticks)

        years = sorted(price_history.index.year.unique())
        ticks = [pd.Timestamp(f'{year}-01-01') for year in years]
        ticks_numeric = mdates.date2num(ticks)
        ax2.set_xticks(ticks_numeric)
        ax2.set_xticklabels([str(year) for year in years], rotation=45, ha='right')

        ax2.set_xlim(date_epoch_start, datetime.now())
        ax2.get_yaxis().set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
        ax2.legend(loc='upper right')

        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        # plt.show()
        plt.close()


        print(f"Price history plotting took {time.time() - time_start:.2f} seconds")

    # Function to calculate 1-year rolling CAGR
    def calculate_rolling_cagr(self):
        history = self.history_monthly()
        rolling_cagr = []
        rolling_cagr_class = []
        for i in range(12, len(history)):
            start_price = history.iloc[i - 12]
            end_price = history.iloc[i]
            if math.isnan(end_price["close"]) or math.isnan(start_price["close"]):
                rolling_cagr.append(0)
                rolling_cagr_class.append(0)
                continue
            cagr = (end_price["close"] / start_price["close"])  # we're already in annual - so not much to do here
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
    def total_cagr(self) -> float:
        if not (self.total_cagr_cache is None):
            return self.total_cagr_cache
        hist = self.history()
        start_price = hist['close'].iloc[0]
        end_price = hist['close'].iloc[-1]
        num_years = (hist.index[-1] - hist.index[0]).days / 365.25
        self.total_cagr_cache = (end_price / start_price) ** (1 / num_years)
        return self.total_cagr_cache

    @classmethod
    def cagr_to_class(cls, cagr, float=False):
        try:
            c = (math.log(cagr) / math.log(cagr_class_exponent))
            if float:
                return c
            return round(c)
        except:
            raise

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
