from typing import Optional
import pandas as pd

from .. import BasketItem
from ..plugin import OutputPlugin, OutputData
from ...financial import Symbol


class Crop(OutputPlugin):
    def __init__(self, alias: Optional[str] = None):
        super().__init__(alias=alias)

    def output_all(self, data: 'OutputData'):
        print(f"Cropping {len(data.items())} symbols to common date range...")
        
        # Collect all date ranges directly into DataFrame
        starts = []
        ends = []
        
        for symbol_ticker, symbol_data in data.items().items():
            for field_name, df in symbol_data.items():
                if df.empty:
                    continue
                    
                starts.append(df['date'].min())
                ends.append(df['date'].max())
        
        if not starts:
            print("No data to crop")
            return data
        
        # Calculate maximum common date range (intersection)
        date_ranges = pd.DataFrame({'start': starts, 'end': ends})
        common_start = date_ranges['start'].max()
        common_end = date_ranges['end'].min()
        
        print(f"Common date range: {common_start.strftime('%Y-%m-%d')} to {common_end.strftime('%Y-%m-%d')}")
        
        # Crop all dataframes to common range and normalize if needed
        cropped_count = 0
        for series_data in data.items().values():
            for field_name, df in series_data.items():
                if df.empty:
                    continue
                    
                # Crop to common range
                cropped_df = df[(df['date'] >= common_start) & (df['date'] <= common_end)]
                
                # Normalize to base 100 if it's an index type
                if cropped_df.attrs.get('type') == 'index':
                    data_col = cropped_df.columns[1]  # Second column is the data
                    first_value = cropped_df[data_col].iloc[0]
                    if first_value != 0:  # Avoid division by zero
                        cropped_df[data_col] = (cropped_df[data_col] / first_value) * 100
                
                series_data[field_name] = cropped_df
                cropped_count += 1
        
        print(f"Cropped {cropped_count} time series to common range")
        return data 