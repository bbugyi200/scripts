""" Automates Logging Initialization """

import inspect
import logging
import types

from systemd.journal import JournalHandler

import gutils.shared as shared

_basic_formatting = '[%(levelname)s] %(message)s'
_thread_formatting = '[%(levelname)s] <%(threadName)s> %(message)s'


def getEasyLogger(name):
    """ Initializes Log Handlers """
    log = logging.getLogger(name)

    if _has_threading(inspect.stack()[1].frame):
        base_formatting = _thread_formatting
    else:
        base_formatting = _basic_formatting

    jh = JournalHandler()
    sh = logging.StreamHandler()

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
    if _has_threading(inspect.stack()[1].frame):
        base_formatting = _thread_formatting
    else:
        base_formatting = _basic_formatting

    for handler in log.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(logging.DEBUG)

    stack = inspect.stack()
    log_file = '/var/tmp/{}.log'.format(shared.scriptname(stack))

    fh = logging.FileHandler(log_file)
    fh.setFormatter(logging.Formatter('[%(process)s] (%(asctime)s) {}'.format(base_formatting),
                                      datefmt='%Y-%m-%d %H:%M:%S'))
    fh.setLevel(logging.DEBUG)
    log.addHandler(fh)

    log.debug('Debugging mode enabled.')


def _has_threading(frame):
    """ Determines Whether or not the Given Frame has the 'threading' Module in Scope """
    try:
        return isinstance(frame.f_globals['threading'], types.ModuleType)
    except KeyError as e:
        return False
