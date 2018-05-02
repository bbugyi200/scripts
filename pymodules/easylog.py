""" Automates Logging Initialization """

import inspect
import logging
import os

from systemd.journal import JournalHandler


def getEasyLogger(name):
    """ Initializes Log Handlers """
    log = logging.getLogger(name)

    jh = JournalHandler()
    sh = logging.StreamHandler()
    fh = logging.FileHandler('/var/tmp/{}.log'.format(os.path.basename(inspect.stack()[1].filename.rstrip('.py'))))

    basic_formatting = '[%(levelname)s] %(message)s'
    formatter = logging.Formatter(basic_formatting)
    jh.setFormatter(formatter)
    sh.setFormatter(formatter)
    fh.setFormatter(logging.Formatter('[%(process)s] (%(asctime)s) {}'.format(basic_formatting),
                                      datefmt='%Y-%m-%d %H:%M:%S'))

    jh.setLevel(logging.ERROR)
    sh.setLevel(logging.INFO)
    fh.setLevel(logging.DEBUG)
    log.setLevel(logging.DEBUG)

    log.addHandler(jh)
    log.addHandler(sh)
    log.addHandler(fh)

    return log
