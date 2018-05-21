#!/usr/bin/env python

""" TEMPLATE """

import argparse
import subprocess as sp  # noqa: F401

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

    with gutils.logging.log_errors(log):
        main()
