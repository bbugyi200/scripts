"""XDG Utilities"""

import getpass
import inspect
import os

import gutils.shared as shared
import gutils

_user = getpass.getuser()

_xdg_vals = {'config': ('XDG_CONFIG_HOME', '/home/{}/.config'),
             'data': ('XDG_DATA_HOME', '/home/{}/.local/share'),
             'runtime': ('XDG_RUNTIME_DIR', '/tmp'),
             'cache': ('XDG_CACHE_HOME', '/home/{}/.cache')}


def init(userdir, stack=None):
    """ Get XDG User Directory.

    Args:
        userdir (str): one of the four defined XDG user directories ('config', 'data', 'runtime',
            or 'cache').
        stack (optional): stack object (see inspect module)

    Returns:
        Full user directory path, as specified by the XDG standard.
    """
    if stack is None:
        stack = inspect.stack()

    scriptname = shared.scriptname(stack)

    full_xdg_dir = '{}/{}'.format(get(userdir), scriptname)
    gutils.create_dir(full_xdg_dir)

    return full_xdg_dir


def get(userdir):
    userdir = userdir.lower()
    userdir_opts = {'config', 'data', 'runtime', 'cache'}
    if userdir not in userdir_opts:
        raise ValueError("Argument @userdir MUST be one of the following "
                         "options: {}".format(userdir_opts))

    envvar, dirfmt = _xdg_vals[userdir]
    xdg_dir = _get(envvar, dirfmt)
    return xdg_dir


def _get(envvar, dirfmt):
    if envvar in os.environ:
        xdg_dir = os.environ[envvar]
    else:
        if '{}' not in dirfmt:
            xdg_dir = dirfmt
        else:
            xdg_dir = dirfmt.format(_user)

    return xdg_dir
