
import traceback

# for side effect: enable arrow key history in input()
import readline


from lib import terminal, Ticker

cmd = None
variables = terminal.Variables()
persistence = terminal.Persistence()


def vis_symbol(symbol):
	def format_optional(value, prefix="", precision=2):
		return f"{prefix}{value:.{precision}f}" if value is not None else "N/A"

	symbol_info = {
		"Ticker": symbol.get("identifier", "N/A"),
		"Name": symbol.get("name", "N/A"),
		"Info": f"{symbol.get('country', 'N/A')} {symbol.get('asset_type', 'N/A')} "
				f"{symbol.get('sector', 'N/A')}"
				+ (f", IPO {symbol['ipo']}" if symbol.get("ipo") else ""),
		"Price": f"{symbol.get('price', 0):.2f} {symbol.get('currency', 'N/A')}",
		"MCap": 'N/A' if symbol.get('market_cap', 0) is None else f"{symbol.get('market_cap', 0) / 1e9:.2f}B {symbol.get('currency', 'N/A')}",
		"Beta": format_optional(symbol.get("beta"))
	}

	print("\n".join([f"{key}: {value}" for key, value in symbol_info.items()]))


printers = {
	"Symbol": vis_symbol
}

while cmd not in ["exit", "quit"]:
	cmd = input(": ")
	try:
		res = terminal.shell(cmd, variables, persistence)
		if isinstance(res, terminal.JsonSerializable):
			d = res.to_dict()
			if "class" in d:
				if d["class"] in printers:
					try:
						printers[d["class"]](d)
					except Exception as e:
						print(f"Error printing {d['class']}: {e}")
						traceback.print_exc()
				else:
					print("unknown class:", d["class"])
					print(d)
			else:
				print(d)
		elif res is not None:
			print(res)
		else:
			print("[no result]")
		print()
	except Exception as e:
		print(f"{type(e).__name__}: {e}")
		continue