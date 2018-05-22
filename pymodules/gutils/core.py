""" Core Classes and Functions

This module contains the core classes and functions of this package. The contents of this module
are intended to be imported directly into the package's global scope.
"""

import argparse
import inspect
import os

import gutils.g_xdg as xdg

__all__ = ['GUtilsError', 'StillAliveException', 'create_pidfile', 'ArgumentParser']


class GUtilsError(Exception):
    """ Base-class for all exceptions raised by this package. """


class StillAliveException(GUtilsError):
    """ Raised when Old Instance of Script is Still Running """
    def __init__(self, pid):
        self.pid = pid


def create_pidfile():
    """ Writes PID to file, which is created if necessary.

    Raises:
        StillAliveException: if old instance of script is still alive.
    """
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


def ArgumentParser(*args, description=None, formatter_class=None, **kwargs):
    """ Wrapper for argparse.ArgumentParser.

    Args:
        description (optional): Describes what the script does.
        formatter_class (optional): A class for customizing the help output.

    Returns:
        An argparse.ArgumentParser object.
    """
    if description is None:
        try:
            frame = inspect.stack()[1].frame
            description = frame.f_globals['__doc__']
        except KeyError as e:
            pass

    if formatter_class is None:
        formatter_class = argparse.ArgumentDefaultsHelpFormatter

    parser = argparse.ArgumentParser(*args,
                                     description=description,
                                     formatter_class=formatter_class,
                                     **kwargs)
    parser.add_argument('-d', '--debug', action='store_true', help='enable debugging mode')
    return parser
