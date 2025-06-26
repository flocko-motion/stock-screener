from typing import Optional

import pandas as pd

from .. import BasketItem
from ..plugin import FieldPlugin, SeriesPlugin, Plugin, OutputPlugin, OutputData
from ...financial import Symbol

class PlotlyEach(OutputPlugin):
    def __init__(self, alias: Optional[str] = None):
        super().__init__(alias=alias)

    def output_item(self, symbol:Symbol, data: dict[str, pd.DataFrame]):
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        if not data:
            return
            
        # Create subplot with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        has_indicators = False
        
        for alias, df in data.items():
            if df.empty:
                continue
                
            # Assume first column is date/time, rest are data
            time_col = df.columns[0]
            data_cols = df.columns[1:]
            
            data_type = df.attrs.get('type', 'index')
            
            for col in data_cols:
                if data_type == 'indicator':
                    # Plot on secondary y-axis
                    fig.add_trace(
                        go.Scatter(
                            x=df[time_col], 
                            y=df[col], 
                            name=df.attrs.get('type', 'title'),
                            line=dict(width=1),
                            opacity=0.7
                        ),
                        secondary_y=True
                    )
                    has_indicators = True
                else:  # 'index' type - price data
                    fig.add_trace(
                        go.Scatter(
                            x=df[time_col], 
                            y=df[col], 
                            name=df.attrs.get('type', 'title'),
                            line=dict(width=2)
                        ),
                        secondary_y=False
                    )
        
        # Configure primary y-axis (price data) - logarithmic scale
        fig.update_yaxes(title_text="Value", type="log", secondary_y=False)
        
        # Configure secondary y-axis if indicators exist
        if has_indicators:
            fig.update_yaxes(
                title_text="Indicators", 
                range=[-1.1, 1.1],
                secondary_y=True
            )
            # Add zero line for indicators
            fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, secondary_y=True)
        
        # Configure x-axis and layout - format as dates
        fig.update_xaxes(
            title_text="Date",
            tickformat="%Y-%m",
            dtick="M3"  # Show every 3 months
        )
        fig.update_layout(
            title=f"{symbol.ticker} {symbol.name}",
            hovermode='x unified',
            width=700,
            height=500
        )
        
        fig.show()


class PlotlyAll(OutputPlugin):
    def __init__(self, alias: Optional[str] = None):
        super().__init__(alias=alias)


    def output_all(self, data: 'OutputData'):
        print(data)

