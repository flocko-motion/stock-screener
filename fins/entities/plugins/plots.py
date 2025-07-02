from typing import Optional

import pandas as pd

from .. import BasketItem
from ..plugin import OutputPlugin, OutputData
from ...financial import Symbol


class PlotEach(OutputPlugin):
    def __init__(self, alias: Optional[str] = None):
        self._register_call_args(alias=alias)
        super().__init__(alias=alias)

    def output_item(self, symbol: Symbol, data: dict[str, pd.DataFrame]):
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        
        if not data:
            return
            
        fig, price_axis = plt.subplots(figsize=(6, 4))
        indicator_axis = None
        yoy_axis = None
        log_axis = None
        
        for alias, df in data.items():
            if df.empty:
                continue
                
            # Assume first column is date/time, rest are data
            time_col = df.columns[0]
            data_cols = df.columns[1:]
            
            # Ensure date column is datetime
            if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
                df[time_col] = pd.to_datetime(df[time_col], unit='s' if df[time_col].dtype in ['int64', 'float64'] else None)
            
            data_type = df.attrs.get('type', 'index')
            
            for col in data_cols:
                series_name = df.attrs.get('title', f"{alias}_{col}")
                
                if data_type == 'index':  # 'index' type - price data
                    price_axis.plot(df[time_col], df[col], label=series_name, linewidth=2)
                elif data_type == 'indicator':
                    # Use secondary y-axis for indicators
                    if indicator_axis is None:
                        indicator_axis = price_axis.twinx()
                        indicator_axis.set_ylim(-1.1, 1.1)
                        indicator_axis.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
                        indicator_axis.set_ylabel('Indicators', color='blue')
                    
                    indicator_axis.plot(df[time_col], df[col], label=series_name, alpha=0.7, linewidth=1)
                    
                elif data_type == 'yoy':
                    # Use dedicated y-axis for Year-over-Year data
                    if yoy_axis is None:
                        yoy_axis = price_axis.twinx()
                        yoy_axis.set_ylim(-0.5, 0.5)  # -50% to +50%
                        yoy_axis.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
                        yoy_axis.set_ylabel('Year-over-Year (%)', color='green')
                        # Format as percentage
                        yoy_axis.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x*100:.0f}%'))
                    
                    yoy_axis.plot(df[time_col], df[col], label=series_name, alpha=0.8, linewidth=1.5, color='green')
                    
                elif data_type == 'log':
                    # Use dedicated y-axis for Log data
                    if log_axis is None:
                        log_axis = price_axis.twinx()
                        log_axis.set_ylim(-5, 10)
                        log_axis.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
                        log_axis.set_ylabel('Log Scale', color='orange')
                    
                    log_axis.plot(df[time_col], df[col], label=series_name, alpha=0.8, linewidth=1.5, color='orange')
                else: 
                    raise ValueError(f"Unknown data type: {data_type}")    
        
        # Configure primary axis (price data) - logarithmic scale with fixed range
        price_axis.set_yscale('log')
        price_axis.set_ylim(10, 1000000)
        price_axis.set_ylabel('Price ($)')
        price_axis.set_xlabel('Date')
        price_axis.grid(True, alpha=0.6, which='major')
        price_axis.grid(True, alpha=0.25, which='minor')
        price_axis.legend(loc='upper left')
        
        # Format additional axes if they exist
        if indicator_axis is not None:
            indicator_axis.legend(loc='upper right')
        if yoy_axis is not None:
            yoy_axis.legend(loc='center right')
        if log_axis is not None:
            log_axis.legend(loc='lower right')
        
        # Format x-axis dates - yearly labels, monthly ticks
        price_axis.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        price_axis.xaxis.set_major_locator(mdates.YearLocator(base=2))
        price_axis.xaxis.set_minor_locator(mdates.YearLocator())
        plt.xticks(rotation=60, fontsize=8)
        
        plt.title(f"{symbol.ticker} {symbol.name}")
        plt.tight_layout()
        plt.show()


class PlotAll(OutputPlugin):
    def __init__(self, alias: Optional[str] = None):
        self._register_call_args(alias=alias)
        super().__init__(alias=alias)


    def output_all(self, data: 'OutputData'):
        print(data)

