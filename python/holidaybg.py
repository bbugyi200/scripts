#!/bin/python

from dateutil.parser import parse
from datetime import datetime, date, timedelta
import sys
import os


def calc_easter(year):
    "Returns Easter as a date object."
    a = year % 19
    b = year // 100
    c = year % 100
    d = (19 * a + b - b // 4 - ((b - (b + 8) // 25 + 1) // 3) + 15) % 30
    e = (32 + 2 * (b % 4) + 2 * (c // 4) - d - (c % 4)) % 7
    f = d + e - 7 * ((a + 11 * d + 22 * e) // 451) + 114
    month = f // 31
    day = f % 31 + 1
    return date(year, month, day)


now = datetime.now().date()
# now = parse('04/01').date()

short = [('pigday', '03/01', 0),
         ('stpatricks', '03/17', 3),
         ('valentines', '02/14', 2),
         ('newyears', '01/01/{}'.format((now + timedelta(2)).year), 1),
         ('aprilfools', '04/01', 0)]

main = [('christmas', '12/25', 15),
        ('halloween', '10/31'),
        ('thanksgiving', '11/25'),
        ('easter', calc_easter(now.year)),
        ('birthday', '03/04'),
        ('fourth', '07/04', 3)]

holidays = short + main

default_max = 7
for H in holidays:
    try:
        MAX = H[2]
    except IndexError:
        MAX = default_max

    try:
        hdate = parse(H[1]).date()
    except TypeError:
        hdate = H[1]

    if now > hdate:
        delta = (now - hdate) * 2
    else:
        delta = hdate - now

    if delta.days <= MAX:
        path = '/home/bryan/Dropbox/photos/backgrounds/holidays/{}.jpg'.format(H[0])
        if os.path.exists(path):
            with open('/tmp/current_bg.txt', 'w') as F:
                F.write(path)

            os.system('feh --bg-center {}'.format(path))
            sys.exit(0)

sys.exit(1)
