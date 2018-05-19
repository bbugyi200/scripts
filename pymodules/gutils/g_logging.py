""" Automates Logging Initialization """

import inspect
import logging

from systemd.journal import JournalHandler

import gutils.shared as shared

_basic_formatting = '[%(levelname)s] %(message)s'
_thread_formatting = '[%(levelname)s] <%(threadName)s> %(message)s'


def getEasyLogger(name, *, threads=False):
    """ Initializes Log Handlers """
    log = logging.getLogger(name)

    if threads:
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


def enableDebugMode(log, *, threads=False):
    """ Sets Log Level of StreamHandler Handlers to DEBUG """
    if threads:
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
