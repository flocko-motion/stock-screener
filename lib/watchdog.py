import threading
import time
from functools import wraps


class WatchdogTimeoutError(Exception):
	"""Custom exception raised when the function exceeds the allowed timeout."""
	pass


def watchdog(timeout: int, retries: int):
	"""
	A decorator to run a function in a separate thread with a timeout and retry mechanism.

	:param timeout: Maximum time (in seconds) the function is allowed to run.
	:param retries: Number of times to retry the function if it exceeds the timeout.
	"""

	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			last_exception = None
			for attempt in range(retries + 1):
				result = [None]
				exception = [None]

				def target():
					try:
						result[0] = func(*args, **kwargs)
					except Exception as e:
						exception[0] = e

				thread = threading.Thread(target=target)
				thread.start()
				thread.join(timeout)

				if thread.is_alive():
					# If the thread is still running after the timeout, kill it
					thread.join(0)  # Force thread termination
					print(f"Attempt {attempt + 1} failed due to timeout.")
				elif exception[0]:
					# If an exception occurred within the function, propagate it
					last_exception = exception[0]
					print(f"Attempt {attempt + 1} failed with exception: {exception[0]}")
				else:
					# Successfully completed
					return result[0]

				time.sleep(0.5)  # Optional delay between retries

			# If all attempts fail, raise the last exception or timeout error
			if last_exception:
				raise last_exception
			raise WatchdogTimeoutError(f"Function `{func.__name__}` failed after {retries + 1} attempts.")

		return wrapper

	return decorator
