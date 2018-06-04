#!/usr/bin/env python

""" TEMPLATE """

import subprocess as sp  # noqa: F401

import gutils

#######################################################################################
#  gutils library: https://github.com/bbugyi200/scripts/tree/master/pymodules/gutils  #
#######################################################################################

log = gutils.logging.getEasyLogger(__name__)


if __name__ == "__main__":
    parser = gutils.ArgumentParser()
    args = parser.parse_args()

    with gutils.logging.context(log, debug=args.debug):
        pass
