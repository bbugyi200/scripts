"""Automates Logging Initialization"""

import contextlib
import inspect
import logging
import types
import sys

from systemd.journal import JournalHandler

import gutils.shared as shared


def getEasyLogger(name):
    """ Initializes Log Handlers

    Args:
        name: name of the logger to create and return.

    Returns:
        A logging.Logger object.
    """
    log = logging.getLogger(name)

    jh = JournalHandler()
    sh = logging.StreamHandler()

    formatter = getFormatter(frame=inspect.stack()[1].frame)
    jh.setFormatter(formatter)
    sh.setFormatter(formatter)

    jh.setLevel(logging.ERROR)
    sh.setLevel(logging.INFO)
    log.setLevel(logging.DEBUG)

    log.addHandler(jh)
    log.addHandler(sh)

    return log


def getFormatter(*, frame=None, verbose=False):
    """ Get log formatter.

    Args:
        frame (optional): frame obect (see inspect module).
        verbose: True if a more verbose log format is desired.

    Returns:
        logging.Formatter object.
    """
    if frame is None:
        frame = inspect.stack()[1].frame

    base_formatting = _get_log_fmt(frame)

    if verbose:
        formatter = logging.Formatter('[%(process)s] (%(asctime)s) {}'.format(base_formatting),
                                      datefmt='%Y-%m-%d %H:%M:%S')
    else:
        formatter = logging.Formatter(base_formatting)

    return formatter


@contextlib.contextmanager
def context(log, *, debug=False, quiet=False):
    """ Exception handling context manager.

    Logs any exceptions that are thrown. Allows the reuse of common exception handling logic.

    Args:
        log: logging.Logger object.
        debug: True if debugging is enabled.
        quiet: True if debug messages should be sent to log file ONLY.
    """
    if debug:
        # must slice stack ([1:]) to cut off contextlib module
        enableDebugMode(log, stack=inspect.stack()[1:], quiet=quiet)

    try:
        yield
    except RuntimeError as e:
        log.error(str(e))
        sys.exit(1)
    except Exception as e:
        log.exception('{}: {}'.format(type(e).__name__, str(e)))
        raise


def enableDebugMode(log, *, stack=None, quiet=False):
    """ Enables debug mode.

    Adds a FileHandler. Sets the logging level of this handler and any existing StreamHandlers
    to DEBUG.

    Args:
        log: logging.Logger object.
        stack (optional): stack object (see inspect module).
        quiet: True if debug messages should be sent to log file ONLY.
    """
    if stack is None:
        stack = inspect.stack()

    frame = stack[1].frame

    if not quiet:
        for handler in log.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(logging.DEBUG)

    # return early if a FileHandler already exists
    for handler in log.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.setLevel(logging.DEBUG)
            return

    log_file = '/var/tmp/{}.log'.format(shared.scriptname(stack))
    fh = logging.FileHandler(log_file)
    formatter = getFormatter(frame=frame, verbose=True)
    fh.setFormatter(formatter)
    fh.setLevel(logging.DEBUG)
    log.addHandler(fh)

    log.debug('Debugging mode enabled.')


def _get_log_fmt(frame):
    """ Get Logging Format String

    Returns a log formatting string, which can be used as the first argument to
    the logging.Formatter constructor.

    Args:
        frame: frame object (see inspect module).
    """
    basic_formatting = '[%(levelname)s] %(message)s'
    thread_formatting = '[%(levelname)s] <%(threadName)s> %(message)s'

    if _has_threading(frame):
        return thread_formatting
    else:
        return basic_formatting


def _has_threading(frame):
    """ Determines whether or not the given frame has the 'threading' module in scope

    Args:
        frame: frame object (see inspect module).
    """
    try:
        return isinstance(frame.f_globals['threading'], types.ModuleType)
    except KeyError as e:
        return False
