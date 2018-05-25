""" Utility Functions that Make use of the subprocess Module

===== Public Interface =====
    Functions: shell, notify
"""

import inspect
import subprocess as sp

import gutils.shared as shared


def shell(cmd, cast=str):
    """ Run Shell Command

    Args:
        cmd (str): command.
        cast (type): type-cast function.

    Returns:
        Output of shell command, casted to the desired type using the @cast function.
    """
    out = sp.check_output(cmd, shell=True)
    return cast(out.decode().strip())


def notify(*args):
    """ Sends desktop notification with calling script's name as the notification title.

    Args:
        *args: arguments to be passed to the notify-send command.
    """
    assert len(args) > 0, 'No notification message specified.'

    cmd_list = ['notify-send']
    cmd_list.extend([shared.scriptname(inspect.stack())])
    cmd_list.extend(args)

    sp.check_call(cmd_list)
