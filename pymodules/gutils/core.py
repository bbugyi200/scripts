"""Core Classes and Functions

This module contains the core classes and functions of this package. The contents of this module
are intended to be imported directly into the package's global namespace.
"""

import argparse
import inspect
import os
import subprocess as sp

import gutils.g_xdg as xdg
import gutils.shared as shared

__all__ = ['GUtilsError', 'StillAliveException', 'create_pidfile', 'mkfifo', 'ArgumentParser',
           'notify', 'xtype', 'xkey']


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


def mkfifo(FIFO_PATH):
    """ Creates named pipe if it does not already exist.

    Args:
        FIFO_PATH (str): the full file path where the named pipe will be created.
    """
    try:
        os.mkfifo(FIFO_PATH)
    except OSError as e:
        pass


def ArgumentParser(*args, opt_args=[], description=None, formatter_class=None, **kwargs):
    """ Wrapper for argparse.ArgumentParser.

    Args:
        opt_args ([str]): A list of optional arguments to add to the parser.
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
    if 'quiet' in opt_args:
        parser.add_argument('-q', '--quiet', action='store_true',
                            help='use with --debug to send debug messages to log file ONLY')

    return parser


def notify(*args, urgency=None):
    """ Sends desktop notification with calling script's name as the notification title.

    Args:
        *args: arguments to be passed to the notify-send command.
    """
    try:
        assert len(args) > 0, 'No notification message specified.'
        assert urgency in (None, 'low', 'normal', 'high'), 'Invalid Urgency: {}'.format(urgency)
    except AssertionError as e:
        raise ValueError(str(e))

    cmd_list = ['notify-send']
    cmd_list.extend([shared.scriptname(inspect.stack())])

    if urgency is not None:
        cmd_list.extend(['-u', urgency])

    cmd_list.extend(args)

    sp.check_call(cmd_list)


def xtype(keys, *, delay=None):
    """Wrapper for `xdotool type`

    Args:
        keys (str): Keys to type.
        delay (optional): Typing delay.
    """
    if delay is None:
        delay = 150

    keys = keys.strip('\n')

    sp.check_call(['xdotool', 'type', '--delay', str(delay), keys])


def xkey(key):
    """Wrapper for `xdotool key`"""
    sp.check_call(['xdotool', 'key', key])
