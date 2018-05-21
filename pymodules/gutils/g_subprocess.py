""" Utility Functions that Make use of the subprocess Module """

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
    """ Sends Desktop Notification

    Args:
        *args: arguments to be passed to the notify-send command.
    """
    assert len(args) > 0, 'No notification message specified.'

    cmd_list = ['notify-send']
    cmd_list.extend([shared.scriptname(inspect.stack())])
    cmd_list.extend(args)

    sp.Popen(cmd_list)
