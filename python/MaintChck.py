#!/bin/python
import os
import pandas as pd
import sys
import sys
from dateutil.parser import parse
from datetime import datetime


if sys.argv[1] == "--update":
    MAX=7

    cmd_output = os.popen('grep -e ".*starting full.*" /var/log/pacman.log | tail -1 | cut -d "[" -f2 | cut -d "]" -f1')
    date_str = cmd_output.read().rstrip()
    last_updt = parse(date_str)
    delta = datetime.today() - last_updt

    print(delta.days)
    if delta.days >= MAX:
        sys.exit(1)
    else:
        sys.exit(0)

elif sys.argv[1] == "--cleanup":
    MAX=30

    date_str = open('/home/bryan/.cleanup-tmstmp.log', 'r').read().rstrip()
    last_clean = parse(date_str)
    delta = datetime.today() - last_clean

    if delta.days >= MAX:
        sys.exit(1)
    else:
        sys.exit(0)
