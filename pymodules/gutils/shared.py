""" Internal Shared Utilities for gutils Package """

import os


def scriptname(stack):
    """ Returns the Filename of the Calling Module

    @stack: object returned by 'inspect.stack'
    """
    return os.path.basename(stack[1].filename.rstrip('.py'))
