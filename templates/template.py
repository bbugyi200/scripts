#!/usr/bin/env python

import argparse
import logging
import os

from systemd.journal import JournalHandler

log = logging.getLogger(__name__)


def main():
    pass


if __name__ == "__main__":
    formatter = logging.Formatter('(%(asctime)s) [%(levelname)s] %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    sh.setLevel(logging.ERROR)
    jh = JournalHandler()
    jh.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    jh.setLevel(logging.INFO)
    fh = logging.FileHandler('/var/tmp/{}.log'.format(os.path.basename(__file__)))
    fh.setFormatter(formatter)
    fh.setLevel(logging.DEBUG)
    log.setLevel(logging.DEBUG)
    log.addHandler(sh)
    log.addHandler(jh)
    log.addHandler(fh)

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
