"""Core Classes and Functions

This module contains the core classes and functions of this package. The contents of this module
are intended to be imported directly into the package's global namespace. All public functions /
classes in this module MUST be added to __all__ or they will NOT be made available.
"""

import argparse
import atexit
import errno
import inspect
import os
import random
import string
import subprocess as sp
import sys
import termios
import tty

import gutils.g_xdg as xdg
import gutils.shared as shared

__all__ = [
    'ArgumentParser',
    'GUtilsError',
    'StillAliveException',
    'create_dir',
    'create_pidfile',
    'getch',
    'imsg',
    'mkfifo',
    'notify',
    'secret',
    'shell',
    'xkey',
    'xtype',
]


def ArgumentParser(*args, opt_args=[], description=None, **kwargs):
    """ Wrapper for argparse.ArgumentParser.

    Args:
        opt_args ([str]): A list of optional arguments to add to the parser.
        description (optional): Describes what the script does.

    Returns:
        An argparse.ArgumentParser object.
    """
    if description is None:
        try:
            frame = inspect.stack()[1].frame
            description = frame.f_globals['__doc__']
        except KeyError:
            pass

    parser = argparse.ArgumentParser(*args,
                                     description=description,
                                     **kwargs)
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debugging mode.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output.')
    if 'quiet' in opt_args:
        parser.add_argument('-q', '--quiet', action='store_true',
                            help='Use with --debug to send debug messages to log file ONLY')

    return parser


def create_dir(directory):
    """ Create directory if it does not already exist.

    Args:
        directory: full directory path.
    """
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def create_pidfile():
    """ Writes PID to file, which is created if necessary.

    Raises:
        StillAliveException: if old instance of script is still alive.
    """
    PIDFILE = "{}/pid".format(xdg.init('runtime', stack=inspect.stack()))
    if os.path.isfile(PIDFILE):
        old_pid = int(open(PIDFILE, 'r').read())
        try:
            os.kill(old_pid, 0)
        except OSError:
            pass
        except ValueError:
            if old_pid != '':
                raise
        else:
            raise StillAliveException(old_pid)

    pid = os.getpid()
    open(PIDFILE, 'w').write(str(pid))


def getch(prompt=None):
    """Reads a single character from stdin.

    Args:
        prompt (optional): prompt that is presented to user.

    Returns:
        The single character that was read.
    """
    if prompt:
        sys.stdout.write(prompt)

    sys.stdout.flush()

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def imsg(msg):
    """Gentoo User Message"""
    print('>>> {}'.format(msg))


class GUtilsError(Exception):
    """ Base-class for all exceptions raised by this package. """


def mkfifo(FIFO_PATH):
    """ Creates named pipe if it does not already exist.

    Args:
        FIFO_PATH (str): the full file path where the named pipe will be created.
    """
    try:
        os.mkfifo(FIFO_PATH)
    except OSError:
        pass


def notify(*args, title=None, urgency=None):
    """ Sends desktop notification with calling script's name as the notification title.

    Args:
        *args: Arguments to be passed to the notify-send command.
        title (opt): Notification title.
        urgency (opt): Notification urgency.
    """
    try:
        assert len(args) > 0, 'No notification message specified.'
        assert urgency in (None, 'low', 'normal', 'high'), 'Invalid Urgency: {}'.format(urgency)
    except AssertionError as e:
        raise ValueError(str(e))

    if title is None:
        title = shared.scriptname(inspect.stack())

    cmd_list = ['notify-send']
    cmd_list.extend([title])

    if urgency is not None:
        cmd_list.extend(['-u', urgency])

    cmd_list.extend(args)

    sp.check_call(cmd_list)


def secret():
    """Get Secret String for Use with secret.sh Script"""
    secret = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
    fp = '/tmp/{}.secret'.format(shared.scriptname(inspect.stack()))

    @atexit.register
    def remove_secret_file():
        """Exit Handler that Removes Secret File"""
        try:
            os.remove(fp)
        except OSError:
            pass

    with open(fp, 'w') as f:
        f.write(secret)

    return secret


def shell(*cmds):
    """Run Shell Command(s)"""
    sp.check_call('; '.join(cmds), shell=True)


class StillAliveException(GUtilsError):
    """ Raised when Old Instance of Script is Still Running """
    def __init__(self, pid):
        self.pid = pid


def xkey(key):
    """Wrapper for `xdotool key`"""
    sp.check_call(['xdotool', 'key', key])


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
