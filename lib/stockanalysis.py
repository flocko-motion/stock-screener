"""
Import data from stockanalysis.com
"""
import os

import requests
from bs4 import BeautifulSoup

from lib.cache import get_cache_path

indexes = {
    # "SPX": 'https://stockanalysis.com/list/sp-500-stocks/',
    "NASDAQ": 'https://stockanalysis.com/list/nasdaq-stocks/',
    "NYSE": 'https://stockanalysis.com/list/nyse-stocks/',
    # "MEGACAPS": 'https://stockanalysis.com/list/mega-cap-stocks/',
    # "LARGECAPS": 'https://stockanalysis.com/list/large-cap-stocks/',
    # "MIDCAPS": 'https://stockanalysis.com/list/mid-cap-stocks/',
    # "DEUTSCHEBOERSE": 'https://stockanalysis.com/list/deutsche-boerse-xetra/',
    # "LSE": 'https://stockanalysis.com/list/london-stock-exchange/',
}

def stockanalysis_get_constituents() -> dict:
    print("loading lists of tickers from stockanalysis.com")
    constituents = {}
    for index in indexes:
        constituents.update(get_constituents(index))
    print(f"found {len(constituents)} tickers")
    return constituents

def get_constituents(index: str) -> dict:
    if index not in indexes:
        raise ValueError(f"Index '{index}' not known")

    html_path = get_cache_path(index, "stockanalysis", "html")
    response_text = None
    if not os.path.exists(html_path):
        url = indexes[index]
        print(f"loadin constituents for {index} from {url}")
        response = requests.get(url)
        response.raise_for_status()  # Ensure the request was successful
        if response.status_code != 200:
            raise ValueError(f"Could not fetch data from {url}")
        with open(html_path, "w") as f:
            f.write(response.text)
        response_text = response.text
    else:
        print(f"loadin constituents for {index} from cache")
        with open(html_path, "r") as f:
            response_text = f.read()

    soup = BeautifulSoup(response_text, 'html.parser')
    table = soup.find('table', {'id': 'main-table'})

    constituents = {}

    for row in table.tbody.find_all('tr'):
        cells = row.find_all('td')
        symbol = cells[1].text.strip()
        company_name = cells[2].text.strip()
        constituents[symbol] = company_name

    return constituents
