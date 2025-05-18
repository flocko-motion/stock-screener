"""
Column implementations.

All column types are automatically discovered and registered by the Column base class.
Access them through Column.list() or Column.get(name).
"""

from ...financial import Symbol

from .dividend_yield import YieldColumn
from .mcap import McapColumn
from .npm import NpmColumn
from .pe import PeColumn
from .peg import PegColumn
from .roe import RoeColumn
from .vol import VolColumn


def column_from_dict(data: dict) -> 'Column':
	data_copy = data.copy()
	class_name = data_copy.pop("class", None)

	if not class_name:
		raise ValueError("Class name not provided in data dictionary")

	if class_name in globals():
		cls = globals()[class_name]
		return cls.from_dict(data_copy)  # Pass the data without the "class" key

	raise ValueError(f"Class {class_name} not found")