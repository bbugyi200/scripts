""" XDG Utilities """

import errno
import getpass
import inspect
import os

import gutils.shared as shared

_user = getpass.getuser()


def getdir(key, stack=None):
    """ Returns XDG Standard Locations """
    key = key.lower()
    key_opts = {'config', 'data', 'runtime', 'cache'}
    assert key in key_opts, "key MUST be in {}".format(key_opts)

    getters = {'config': _getter_factory('XDG_CONFIG_HOME', '/home/{}/.config/{}'),
               'data': _getter_factory('XDG_DATA_HOME', '/home/{}/.local/share/{}'),
               'runtime': _getter_factory('XDG_RUNTIME_DIR', '/run/user/1000/{}'),
               'cache': _getter_factory('XDG_CACHE_HOME', '/home/{}/.cache/{}')}

    if stack is None:
        stack = inspect.stack()

    return getters[key](stack)


def _getter_factory(envvar, dirfmt):
    """ Returns XDG Getter Function that serves to fetch some XDG Standard Directory """
    def _getter(stack):
        scriptname = shared.scriptname(stack)

        if envvar in os.environ:
            xdg_dir = '{}/{}'.format(os.environ[envvar], scriptname)
        else:
            if dirfmt.count('{}') < 2:
                xdg_dir = dirfmt.format(scriptname)
            else:
                xdg_dir = dirfmt.format(_user, scriptname)

        _create_dir(xdg_dir)
        return xdg_dir
    return _getter


def _create_dir(directory):
    """ Create Directory if it Does Not Already Exist """
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
