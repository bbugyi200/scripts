#!/bin/python
from os import popen, getenv
import datetime as dt
import re

current = popen("hamster current").read()

today = dt.datetime.now() - dt.timedelta(0.25)
stoday = today.strftime("%Y-%m-%d")
idx = (today.weekday() + 1) % 7
sat = today - dt.timedelta((7+idx-6) % 7)
ssat = sat.strftime("%Y-%m-%d")

ham_list_day = popen("hamster list %s" % stoday).read()
ham_list_week = popen("hamster list %s" % ssat).read()

reg = re.compile("Study: (\d\.\dh)")

try:
    day_time = reg.search(ham_list_day).groups()[0]
except AttributeError:
    day_time = "0.0h"

try:
    week_time = reg.search(ham_list_week).groups()[0]
except AttributeError:
    week_time = "0.0h"

if len(current.split()) > 2:
    current = ' '.join(current.split()[2:])
    activity = current[:current.find("@")]

    ham_search_act = popen("hamster search %s %s" % (activity, stoday)).read()

    try:
        act_time = reg.search(ham_search_act).groups()[0]
    except AttributeError:
        act_time = "0.0h"

    output = "H%s   (%s / %s / %s)\n" % (current, act_time, day_time, week_time)
else:
    output = "HNo Activity  (%s / %s)\n" % (day_time, week_time)


with open(getenv("PANEL_FIFO"), "w") as f:
    f.write(output)

print(output)
