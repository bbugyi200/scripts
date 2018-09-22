"""Global Utilities

This package imports core.py into its global namespace. See help(gutils.core) for documentation
on globally defined functions.
"""

import gutils.g_logging as logging  # noqa: F401
import gutils.g_xdg as xdg  # noqa: F401
import gutils.g_debug as debug  # noqa: F401
import gutils.g_colorize as colorize  # noqa: F401
from gutils.core import *  # noqa: F401, F403
