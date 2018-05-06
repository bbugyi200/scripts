#!/usr/bin/env python

""" TEMPLATE """

import argparse
import sys

import gutils

log = gutils.logging.getEasyLogger(__name__)


def main():
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-d', '--debug', action='store_true', help='enable debugging mode')
    args = parser.parse_args()

    if args.debug:
        gutils.logging.enableDebugMode(log)

    try:
        main()
    except RuntimeError as e:
        log.error(str(e))
        sys.exit(1)
    except Exception as e:
        log.error('{}: {}'.format(type(e).__name__, str(e)))
        raise
