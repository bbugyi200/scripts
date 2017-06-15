""" UpdtCheck.py """

import os
import sys
from dateutil.parser import parse
from datetime import datetime

MAX=7

cmd_output = os.popen('grep -e ".*starting full.*" /var/log/pacman.log | tail -1 | cut -d "[" -f2 | cut -d "]" -f1')
date_str = cmd_output.read().rstrip()
last_updt = parse(date_str)
delta = datetime.today() - last_updt

if delta.days >= MAX:
    sys.exit(1)
else:
    sys.exit(0)
