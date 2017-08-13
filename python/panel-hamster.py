#!/bin/python
from os import popen, getenv
import datetime as dt
import re

current = popen("hamster current").read()
activity = None
if len(current.split()) > 2:
    current = ' '.join(current.split()[2:])
    activity = current[:current.find("@")]

    today = dt.datetime.now() - dt.timedelta(0.25)
    stoday = today.strftime("%Y-%m-%d")
    reg = re.compile("Study: (\d\.\dh)")
    ham_search = popen("hamster search %s %s" % (activity, stoday)).read()
    ham_list = popen("hamster list %s" % stoday).read()

    act_time = reg.search(ham_search).groups()[0]
    tot_time = reg.search(ham_list).groups()[0]

    output = "H%s   (%s / %s)\n" % (current, act_time, tot_time)
else:
    output = current

with open(getenv("PANEL_FIFO"), "w") as f:
    f.write(output)
