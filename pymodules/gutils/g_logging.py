""" Automates Logging Initialization """

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

    base_formatting = _get_log_fmt(inspect.stack()[1].frame)
    formatter = logging.Formatter(base_formatting)
    jh.setFormatter(formatter)
    sh.setFormatter(formatter)

    jh.setLevel(logging.ERROR)
    sh.setLevel(logging.INFO)
    log.setLevel(logging.DEBUG)

    log.addHandler(jh)
    log.addHandler(sh)

    return log


@contextlib.contextmanager
def context(log, *, debug=False):
    """ Exception handling context manager.

    Logs any exceptions that are thrown. Allows the reuse of common exception handling logic.

    Args:
        log: logging.Logger object.
        debug: True if debugging is enabled.
    """
    if debug:
        enableDebugMode(log, frame=inspect.stack()[1].frame)

    try:
        yield
    except RuntimeError as e:
        log.error(str(e))
        sys.exit(1)
    except Exception as e:
        log.error('{}: {}'.format(type(e).__name__, str(e)))
        raise


def enableDebugMode(log, *, frame=None):
    """ Enables debug mode.

    Adds a FileHandler. Sets the logging level of this handler and any existing StreamHandlers
    to DEBUG.

    Args:
        log: logging.Logger object.
        frame: frame object (see inspect module).
    """
    for handler in log.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(logging.DEBUG)

    stack = inspect.stack()
    log_file = '/var/tmp/{}.log'.format(shared.scriptname(stack))

    fh = logging.FileHandler(log_file)

    if frame is None:
        frame = stack[1].frame

    base_formatting = _get_log_fmt(frame)
    fh.setFormatter(logging.Formatter('[%(process)s] (%(asctime)s) {}'.format(base_formatting),
                                      datefmt='%Y-%m-%d %H:%M:%S'))
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
