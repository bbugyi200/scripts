#!/usr/bin/env python

""" TEMPLATE """

import argparse
import logging
import os

from systemd.journal import JournalHandler

log = logging.getLogger(__name__)


def main():
    pass


def start_logging(log):
    """ Initializes Log Handlers """
    sh = logging.StreamHandler()
    jh = JournalHandler()
    fh = logging.FileHandler('/var/tmp/{}.log'.format(os.path.basename(__file__)))

    basic_formatting = '[%(levelname)s] %(message)s'
    formatter = logging.Formatter(basic_formatting)
    sh.setFormatter(formatter)
    jh.setFormatter(formatter)
    fh.setFormatter(logging.Formatter('(%(asctime)s) {}'.format(basic_formatting),
                                      datefmt='%Y-%m-%d %H:%M:%S'))

    sh.setLevel(logging.ERROR)
    jh.setLevel(logging.INFO)
    fh.setLevel(logging.DEBUG)
    log.setLevel(logging.DEBUG)

    log.addHandler(sh)
    log.addHandler(jh)
    log.addHandler(fh)


if __name__ == "__main__":
    start_logging(log)

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-d', '--debug', action='store_true', help='enable debugging mode')
    args = parser.parse_args()

    if args.debug:
        for handler in log.handlers:
            handler.setLevel(logging.DEBUG)

    try:
        main()
    except Exception as e:
        log.error('{}: {}'.format(type(e).__name__, str(e)))
        raise
