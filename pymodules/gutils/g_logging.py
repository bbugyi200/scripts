"""Automates Logging Initialization"""

import contextlib
import inspect
import logging
import types
import sys

import gutils.shared as shared


def getEasyLogger(name):
    """Initializes Log Handlers

    Args:
        name: name of the logger to create and return.

    Returns:
        A logging.Logger object.
    """
    log = logging.getLogger(name)
    add_vdebug_level(logging)

    log.setLevel(logging.VDEBUG)

    formatter = getFormatter(frame=inspect.stack()[1].frame)

    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    sh.setLevel(logging.INFO)
    log.addHandler(sh)

    return log


def add_vdebug_level(logging):
    """Adds custom logging level for verbose debug logs."""
    VDEBUG_LEVEL_NUM = 5
    logging.addLevelName(VDEBUG_LEVEL_NUM, "VDEBUG")

    def vdebug(self, message, *args, **kwargs):
        if self.isEnabledFor(VDEBUG_LEVEL_NUM):
            self._log(VDEBUG_LEVEL_NUM, message, args, **kwargs)

    logging.Logger.vdebug = vdebug
    logging.VDEBUG = VDEBUG_LEVEL_NUM


def getFormatter(*, frame=None, verbose=False):
    """Get log formatter.

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
def context(log, *, debug=False, verbose=False, quiet=False):
    """Exception handling context manager.

    Logs any exceptions that are thrown. Allows the reuse of common exception handling logic.

    Args:
        log: logging.Logger object.
        debug: True if debugging is enabled.
        verbose: True if verbose output is enabled (enables VDEBUG level messages).
        quiet: True if debug messages should be sent to log file ONLY.
    """
    if debug:
        # must slice stack ([1:]) to cut off contextlib module
        enableDebugMode(log, verbose=verbose, stack=inspect.stack()[1:], quiet=quiet)

    try:
        yield
    except RuntimeError as e:
        log.error(str(e))
        sys.exit(1)
    except Exception as e:
        log.exception('{}: {}'.format(type(e).__name__, str(e)))
        raise


def enableDebugMode(log, *, verbose=False, stack=None, quiet=False):
    """Enables debug mode.

    Adds a FileHandler. Sets the logging level of this handler and any existing StreamHandlers
    to DEBUG.

    Args:
        log: logging.Logger object.
        verbose: True if vdebug logging level is to be enabled.
        stack (optional): stack object (see inspect module).
        quiet: True if debug messages should be sent to log file ONLY.
    """
    if stack is None:
        stack = inspect.stack()

    frame = stack[1].frame
    level = logging.VDEBUG if verbose else logging.DEBUG

    for handler in log.handlers:
        if not isinstance(handler, logging.StreamHandler) or not quiet:
            handler.setLevel(level)

    # return early if a FileHandler already exists
    for handler in log.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.setLevel(level)
            return

    log_file = '/var/tmp/{}.log'.format(shared.scriptname(stack))
    fh = logging.FileHandler(log_file)
    formatter = getFormatter(frame=frame, verbose=True)
    fh.setFormatter(formatter)
    fh.setLevel(level)
    log.addHandler(fh)

    log.debug('Debugging mode enabled.')


def _get_log_fmt(frame):
    """Get Logging Format String

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
    """Determines whether or not the given frame has the 'threading' module in scope

    Args:
        frame: frame object (see inspect module).
    """
    try:
        return isinstance(frame.f_globals['threading'], types.ModuleType)
    except KeyError:
        return False
