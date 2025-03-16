from setuptools import setup, find_packages

setup(
    name='stock-screener',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'pillow',
        'requests',
        'beautifulsoup4',
        'matplotlib',
        'pandas',
        'numpy',
        'yfinance',
		'lark-parser',
    ],
)