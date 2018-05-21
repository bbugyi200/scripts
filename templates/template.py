#!/usr/bin/env python

""" TEMPLATE """

import subprocess as sp  # noqa: F401

import gutils

log = gutils.logging.getEasyLogger(__name__)


def main():
    pass


if __name__ == "__main__":
    parser = gutils.ArgumentParser(__doc__)
    args = parser.parse_args()

    with gutils.logging.context(log, debug=args.debug):
        main()
