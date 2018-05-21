""" Automates Logging Initialization """

import contextlib
import inspect
import logging
import types
import sys

from systemd.journal import JournalHandler

import gutils
import gutils.shared as shared


def getEasyLogger(name):
    """ Initializes Log Handlers """
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


def enableDebugMode(log):
    """ Sets Log Level of StreamHandler Handlers to DEBUG """
    for handler in log.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(logging.DEBUG)

    stack = inspect.stack()
    log_file = '/var/tmp/{}.log'.format(shared.scriptname(stack))

    fh = logging.FileHandler(log_file)
    base_formatting = _get_log_fmt(inspect.stack()[1].frame)
    fh.setFormatter(logging.Formatter('[%(process)s] (%(asctime)s) {}'.format(base_formatting),
                                      datefmt='%Y-%m-%d %H:%M:%S'))
    fh.setLevel(logging.DEBUG)
    log.addHandler(fh)

    log.debug('Debugging mode enabled.')


def _get_log_fmt(frame):
    """ Get Logging Format String

    Returns a log formatting string, which can be used as the first argument to
    the logging.Formatter constructor.
    """
    basic_formatting = '[%(levelname)s] %(message)s'
    thread_formatting = '[%(levelname)s] <%(threadName)s> %(message)s'

    if _has_threading(frame):
        return thread_formatting
    else:
        return basic_formatting


def _has_threading(frame):
    """ Determines Whether or not the Given Frame has the 'threading' Module in Scope """
    try:
        return isinstance(frame.f_globals['threading'], types.ModuleType)
    except KeyError as e:
        return False


@contextlib.contextmanager
def log_errors(log, *, notify=False):
    """ Exception Context Manager

    Logs any exceptions that are thrown. Allows the reuse of common exception handling logic.
    """
    try:
        yield
    except RuntimeError as e:
        log.error(str(e))
        if notify:
            gutils.sp.notify(str(e))
        sys.exit(1)
    except Exception as e:
        log.error('{}: {}'.format(type(e).__name__, str(e)))
        raise
