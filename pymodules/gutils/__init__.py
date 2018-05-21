""" Global Utilities

--- Public Interface ---
Modules:
    logging: Provides a template for setting up generic logging in python scripts.
    xdg: Provides an easy way to retrieve (and, if necessary, create) the directories specified
        by the XDG standard.
    debug: Debugging utilities.
    sp: Utilities for spawning subprocesses.

Exceptions:
    StillAliveException: raised when a PID file is unable to be overwritten due to the previous
        instance of the script still being alive.

Functions:
    create_pidfile: creates a PID file.
    ArgumentParser: wrapper for argparse.ArgumentParser.
"""

import argparse
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


def ArgumentParser(description):
    """ Wrapper for argparse.ArgumentParser """
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--debug', action='store_true', help='enable debugging mode')
    return parser
