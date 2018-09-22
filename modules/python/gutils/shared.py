"""Internal Shared Utilities for gutils Package"""

import os


def scriptname(stack):
    """ Returns the Filename of the Calling Module

    Args:
        stack: object returned by 'inspect.stack'

    Returns:
        Filename with .py extension stripped off.
    """
    return os.path.basename(stack[1].filename.rstrip('.py'))
