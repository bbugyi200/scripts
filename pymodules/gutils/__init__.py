""" Global Utilities

Modules:
    logging: Provides a template for setting up generic logging in python scripts.
    xdg: Provides an easy way to retrieve (and, if necessary, create) the directories specified
        by the XDG standard.
    debug: Debugging utilities.
    sp: Utilities for spawning subprocesses.
    shared: Utility module used by this package internally. Not intended to be used outside of
        this package.
"""

import inspect
import os

import gutils.g_logging as logging  # noqa: F401
import gutils.g_xdg as xdg  # noqa: F401
import gutils.g_debug as debug  # noqa: F401
import gutils.g_subprocess as sp  # noqa: F401


class StillAliveException(Exception):
    """ Raised when Old Instance of Script is Still Running """
    def __init__(self, pid):
        self.pid = pid


def create_pidfile():
    """ Writes PID to File """
    PIDFILE = "{}/pid".format(xdg.getdir('runtime', stack=inspect.stack()))
    if os.path.isfile(PIDFILE):
        old_pid = int(open(PIDFILE, 'r').read())
        try:
            os.kill(old_pid, 0)
        except OSError as e:
            pass
        except ValueError as e:
            if old_pid != '':
                raise
        else:
            raise StillAliveException(old_pid)

    pid = os.getpid()
    open(PIDFILE, 'w').write(str(pid))
