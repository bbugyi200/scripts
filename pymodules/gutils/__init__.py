""" Global Utilities

Public Modules:
    logging: Provides a template for setting up generic logging in python scripts.
    xdg: Provides an easy way to retrieve (and, if necessary, create) the directories specified
        by the XDG standard.
    debug: Debugging utilities.
    sp: Utilities for spawning subprocesses.
"""

import gutils.g_logging as logging  # noqa: F401
import gutils.g_xdg as xdg  # noqa: F401
import gutils.g_debug as debug  # noqa: F401
import gutils.g_subprocess as sp  # noqa: F401
from gutils.core import *  # noqa: F401, F403
