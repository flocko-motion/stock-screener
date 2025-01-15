import re
import json
import threading
import traceback
from abc import ABC, abstractmethod

import lib.financialmodelingprep as fmp

class JsonSerializable(ABC):
    @abstractmethod
    def to_dict(self):
        pass

class Variable:
	def __init__(self, name: str, value):
		self.name = name
		self.value = value


class Symbol(JsonSerializable):

	symbols = {}


	@classmethod
	def get(cls, ticker: str):
		if ticker not in cls.symbols:
			cls.symbols[ticker] = Symbol(ticker)
		return cls.symbols[ticker]


	def __init__(self, ticker: str):
		if not isinstance(ticker, str):
			raise ValueError(f"Invalid ticker value: {ticker}")

		tokens =  ticker.split(":", 1)

		self.ticker = tokens[0]

		exchange = None if len(tokens) < 2 else tokens[1]

		profiles = fmp.profile(self.ticker)
		if profiles is None:
			raise ValueError(f"No profile data found for ticker '{self.ticker}'.")
		profile = None
		if len(profiles) > 1:
			if exchange is not None:
				for p in profiles:
					if p["exchangeShortName"] == exchange:
						profile = p
						break
				else:
					raise ValueError(f"No profile found for ticker '{self.ticker}' on exchange '{exchange}'. Did you mean: " + ", ".join([p["exchangeShortName"] for p in profile]) + " ?")
			raise ValueError(f"Multiple profiles found for ticker '{self.ticker}', did you mean: " + ", ".join([p["symbol"] + ":" + p["exchangeShortName"] for p in profile]) + " ?")
		elif len(profiles) == 1:
			try:
				profile = profiles[0]
			except Exception as e:
				raise ValueError(f"Error parsing profile data for ticker '{self.ticker}': {e}")
		# else:
		# 	raise ValueError(f"No profile found for ticker '{self.ticker}:{exchange}'.")

		if len(profiles) == 0 or exchange == "CRYPTO":
			profiles = fmp.quote(self.ticker)
			if profiles is None or len(profiles) == 0:
				raise ValueError(f"No profile data found for ticker '{self.ticker}'.")
			profile = profiles[0]
			profile["exchangeShortName"] = "CRYPTO"
			profile["mktCap"] = profile["marketCap"] if "marketCap" in profile else None
			profile["currency"] = profile["symbol"][-3:]
			profile["companyName"] = profile["name"]
			profile["sector"] = ""
			profile["country"] = ""
			profile["isEtf"] = False
			profile["isFund"] = False
			profile["isTrading"] = profile["price"] is not None and profile["price"] > 0


		self.exchange = profile["exchangeShortName"] if "exchangeShortName" in profile else None
		self.currency = profile["currency"] if "currency" in profile else None
		self.name = profile["companyName"] if "companyName" in profile else None
		self.price = profile["price"] if "price" in profile else None
		self.market_cap = profile["mktCap"] if "mktCap" in profile else None
		self.beta = profile["beta"] if "beta" in profile else None
		self.sector = profile["sector"] if "sector" in profile else None
		self.country = profile["country"] if "country" in profile else None
		self.ipo = profile["ipoDate"] if "ipoDate" in profile else None
		self.is_etf = profile["isEtf"] if "isEtf" in profile else None
		self.is_fund = profile["isFund"] if "isFund" in profile else None
		self.is_trading = profile["isTrading"] if "isTrading" in profile else None

	def __str__(self):
		return self.ticker + ":" + self.exchange

	def type_string(self):
		if self.is_etf:
			return "ETF"
		if self.is_fund:
			return "Fund"
		if self.exchange == "CRYPTO":
			return "Crypto"
		return "Stock"

	def profile_string(self):
		return f"{self.ticker}:{self.exchange} {self.name}\n" \
			+ f"{self.type_string()} {self.sector if self.sector is not None else ''} {self.country if self.country is not None else ''} {self.ipo if self.ipo is not None else ''}\n" \
			+ f"{self.currency} {self.price} (MktCap:  {self.currency} {self.market_cap})"

	def to_dict(self):
		return {
			"class": "Symbol",
			"ticker": self.ticker,
			"exchange": self.exchange,
			"currency": self.currency,
			"name": self.name,
			"price": self.price,
			"market_cap": self.market_cap,
			"beta": self.beta,
			"sector": self.sector,
			"country": self.country,
			"ipo": self.ipo,
			"is_etf": self.is_etf,
			"is_fund": self.is_fund,
			"is_trading": self.is_trading
		}


class Position(JsonSerializable):
	def __init__(self, symbol: Symbol, quantity: float = 1):
		self.symbol = symbol
		self.quantity = quantity

	def to_dict(self):
		return {
			"class": "Position",
			"symbol": self.symbol.to_dict()
		}

class Portfolio(JsonSerializable):
	def __init__ (self, positions: [Position]):
		self.positions = positions

	def __str__(self):
		out = ""
		if all(position.quantity == 1 for position in self.positions):
			sorted_positions = sorted(self.positions, key=lambda position: position.symbol.ticker)
			for position in sorted_positions:
				try:
					out += f"{position.symbol.ticker:<14} {position.symbol.exchange:<10} {position.symbol.name:<20}\n"
				except Exception as e:
					return f"error formatting position {position}: {e}"
		else:

			sorted_positions = sorted(self.positions, key=lambda position: position.quantity, reverse=True)
			for position in sorted_positions:
				try:
					out += f"{position.quantity:>10.2f}  {position.symbol.ticker:<14} {position.symbol.exchange:<10} {position.symbol.name:<20}\n"
				except Exception as e:
					return f"error formatting position {position}: {e}"

		return out

	def to_dict(self):
		return {
			"class": "Portfolio",
			"positions": [position.to_dict() for position in self.positions]
		}

	@classmethod
	def from_tickers(cls, tickers):
		from concurrent.futures import ThreadPoolExecutor

		# pre-fetch tickers
		def fetch_symbol(ticker):
			try:
				symbol = Symbol.get(ticker)
				return Position(symbol, 1)
			except Exception as e:
				# print stack trace
				traceback.print_exc()
				raise Exception(f"error fetching symbol {ticker}: {e}")

		positions = None
		with ThreadPoolExecutor() as executor:
			positions = list(executor.map(fetch_symbol, tickers))

		return Portfolio(positions)


class Variables:
	def __init__(self):
		self.vars = {}

	def set(self, name: str, value: str):
		self.get(name).value = value

	def get(self, name: str) -> Variable:
		if name not in self.vars:
			self.vars[name] = Variable(name, None)
		return self.vars[name]

class Persistence:
	def __init__(self):
		self.vars = {}

	def set(self, name: str, value: str):
		self.get(name).value = value

	def get(self, name: str) -> Variable:
		if name not in self.vars:
			self.vars[name] = Variable(name, None)
		return self.vars[name]



def shell(cmd: str, variables: Variables, persistence: Persistence):
	tokens = cmd.split(" ")
	if len(tokens) == 0:
		return
	debug = False
	if tokens[0] == "debug":
		debug = True
		tokens = tokens[1:]

	try:
		return parse(tokens, variables, persistence)
	except Exception as e:
		if debug:
			traceback.print_exc()
		return f"{type(e).__name__}: {e}"

def is_ticker_name(token):
    pattern = r'^\^?[A-Z]+(:[A-Z]+)?$'
    return re.match(pattern, token) is not None

def parse(tokens, variables, persistence, result=None):
	op_left = None
	op_right = None
	function = None
	for i in range(len(tokens)):
		token = tokens[i]
		if token == " ":
			continue
		if token is None:
			raise ValueError(f"Unexpected token {i}: {token}")
		if token[0] == '$':
			if op_left is not None:
				raise ValueError(f"Unexpected token {i}: {token}")
			op_left = variables.get(token[1:])
			continue
		if token[0] == '/':
			if op_left is not None:
				raise ValueError(f"Unexpected token {i}: {token}")
			op_left = persistence.get(token[1:])
			result = op_left
			continue
		if token == '=':
			if op_left is None:
				raise ValueError(f"Unexpected token {i}: {token}")
			op_left.value = parse(tokens[i+1:], variables, persistence)
			continue
		if token == "->":
			""" hand over the result of the current operation to the next section in the pipeline """
			if function is not None:
				result = function(op_left, op_right)
			return parse(tokens[i+1:], variables, persistence, result)
		if is_ticker_name(token):
			value = Symbol.get(token)
			if function is None:
				if op_left is not None:
					raise ValueError(f"Unexpected token {i}: {token}")
				op_left = value
				result = value
			else:
				op_right = value
			continue
		if (token.lower() == token) and (token in functions):
			function = functions[token]
			continue
		# some other string value
		op_right = token
	if function is not None:
		result = function(op_left, op_right)
	elif op_left is not None:
		if isinstance(op_left, Variable):
			if result is None:
				result = op_left.value
			else:
				op_left.value = result
	elif function is None and op_left is None and op_right is not None:
		raise ValueError(f"Unexpected token {i}: {op_right}")
	return result

def f_search(a, b):
	if a is not None:
		raise ValueError("Unexpected argument")
	if b is None:
		raise ValueError("Missing argument")
	res = fmp.search(b)
	return res

def f_search_name(a, b):
	if a is not None:
		raise ValueError("Unexpected argument")
	if b is None:
		raise ValueError("Missing argument")
	if len(b) < 3:
		raise ValueError("Search query must be at least 3 characters long.")
	res = fmp.search_name(b)
	if len(res) > 0:
		print(f"Found {len(res)} results.")
		try:
			tickers = [(r["symbol"] + (":" + r["exchangeShortName"] if "exchangeShortName" in r and r["exchangeShortName"] is not None else "")) for r in res]
			return Portfolio.from_tickers(tickers)
		except Exception as e:
			raise e
	return res

def f_add(a, b):
	if a is None or b is None:
		raise ValueError("Missing argument")
	return a + b

def f_list(a, b):
	if a is not None:
		raise ValueError("Unexpected argument")
	fundamentals = fmp.load_ticker_fundamentals(b)
	if fundamentals is None:
		raise ValueError(f"No fundamentals data found for ticker '{b}'.")
	return fundamentals
	pass

def f_chart(a, b):
	if a is not None:
		raise ValueError("Unexpected argument")
	pass

def f_profile(a, b: Symbol):
	if a is not None:
		raise ValueError("Unexpected argument")
	return b.profile_string()


def f_jq(a, b):
	if a is not None:
		raise ValueError("Unexpected argument")
	if b is None:
		raise ValueError("Missing argument")
	json.dumps(b)

functions = {
	"+": f_add,
	"profile": f_profile,
	"list": f_list,
	"chart": f_chart,
	# "search": f_search,
	"search": f_search_name,
	"jq": f_jq,
}
