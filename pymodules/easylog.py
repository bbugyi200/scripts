""" Automates Logging Initialization """

import inspect
import logging
import os

from systemd.journal import JournalHandler


def getEasyLogger(name):
    """ Initializes Log Handlers """
    log = logging.getLogger(name)

    sh = logging.StreamHandler()
    jh = JournalHandler()
    fh = logging.FileHandler('/var/tmp/{}.log'.format(os.path.basename(inspect.stack()[1].filename.rstrip('.py'))))

    basic_formatting = '[%(levelname)s] %(message)s'
    formatter = logging.Formatter(basic_formatting)
    sh.setFormatter(formatter)
    jh.setFormatter(formatter)
    fh.setFormatter(logging.Formatter('[%(process)s] (%(asctime)s) {}'.format(basic_formatting),
                                      datefmt='%Y-%m-%d %H:%M:%S'))

    sh.setLevel(logging.ERROR)
    jh.setLevel(logging.INFO)
    fh.setLevel(logging.DEBUG)
    log.setLevel(logging.DEBUG)

    log.addHandler(sh)
    log.addHandler(jh)
    log.addHandler(fh)

    return log
