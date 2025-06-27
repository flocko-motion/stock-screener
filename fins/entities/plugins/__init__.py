"""
Plugin implementations.

All plugin types extend either Plugin or FieldPlugin base classes.
"""

# FieldPlugin implementations (DataFrame-based)
from .cagr import Cagr
from .crop import Crop
from .industry import Industry
from .name import Name
from .last_price_update import LastUpdatePrice
from .last_profile_update import LastUpdateProfile
from .update import Update
from .price import MonthlyClose, WeeklyClose
from .plots import PlotEach, PlotAll
from .sector import Sector

# Legacy plugin implementations (commented out until migrated to FieldPlugin)
# from .cagr import CagrColumn
# from .dividend_yield import YieldColumn
# from .mcap import McapColumn
# from .name import NameColumn
# from .npm import NpmColumn
# from .pe import PeColumn
# from .peg import PegColumn
# from .roe import RoeColumn
# from .sector import SectorColumn
# from .vol import VolColumn

__all__ = [
    'Cagr',
    'Crop',
    'Industry',
    'LastUpdateProfile',
    'LastUpdatePrice',
    'MonthlyClose',
    'Name',
    'PlotAll',
    'PlotEach',
    'Sector',
    'Update',
    'WeeklyClose',
]


