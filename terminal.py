
import traceback

# for side effect: enable arrow key history in input()
import readline


from lib import terminal, Ticker

cmd = None
variables = terminal.Variables()
persistence = terminal.Persistence()

while cmd not in ["exit", "quit"]:
	cmd = input(": ")
	try:
		res = terminal.shell(cmd, variables, persistence)
		if res is not None:
			print(res)
	except Exception as e:
		print(f"{type(e).__name__}: {e}")
		continue