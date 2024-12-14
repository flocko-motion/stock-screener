import os
import shutil
import traceback

from lib import Ticker
import lib


# Ticker.get("AAPL").analyze()
# exit(0)

protocol_file = os.path.join(os.path.dirname(__file__), "protocol.log")


def write_protocol(text):
    print(text)
    with open(protocol_file, "a") as f:
        f.write(text + "\n")

def clear_protocol():
    if os.path.exists(protocol_file):
        os.remove(protocol_file)

clear_protocol()
write_protocol("Starting stock-screener.py")

class StockScreener:# write to protocol file

    tickers = {}

    @classmethod
    def for_all_tickers(cls, caption: str, func):
        i = 0

        for ticker in cls.tickers.keys():
            i += 1
            company = cls.tickers[ticker]
            try:
                print(f"\n-----[{caption} {i}/{len(cls.tickers.keys())}: {ticker} {company}]----------------\n")
                func(Ticker.get(ticker))
            except Exception as e:
                write_protocol(f"Error during action {caption} for {ticker} {company}: {e}")
                traceback.print_exc()

    @classmethod
    def load(cls):
        cls.for_all_tickers("Load", lambda ticker: ticker.load_financial_data())

    @classmethod
    def analyze(cls):
        cls.for_all_tickers("Analyze", lambda ticker: ticker.analyze())

    @classmethod
    def process_single_asset(cls, ticker):
        t = Ticker.get(ticker)
        t.load_financial_data()
        t.analyze()
        cls.tickers[ticker] = t

    @classmethod
    def build_html(cls):
        html_dir = os.path.join(os.path.dirname(__file__), "html")
        plots_dir = os.path.join(html_dir, "plots")
        if not os.path.exists(html_dir):
            os.makedirs(html_dir)
        if os.path.exists(plots_dir):
            shutil.rmtree(plots_dir)        
            
        df = Ticker.init_df()
        cls.for_all_tickers("Build HTML", lambda ticker: ticker.add_to_html(html_dir, df))
        df.to_csv(os.path.join(html_dir, "data.csv"), index=False)




    @classmethod
    def populate_tickers_list(cls):
        cls.tickers = lib.stockanalysis_get_constituents()


StockScreener.process_single_asset("ARM")
StockScreener.process_single_asset("AAPL")
StockScreener.build_html()
exit(0)

# StockScreener.populate_tickers_list()
StockScreener.load()
StockScreener.analyze()
StockScreener.build_html()