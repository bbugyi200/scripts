#!/bin/python
import sys
import os
import pickle

fpath = '/home/bryan/Dropbox/scripts/python/objs/default_dirs'

default_dirs = dict()
if not os.path.isfile(fpath):
    with open(fpath, 'wb+') as f:
        pickle.dump(default_dirs, f)
else:
    with open(fpath, 'rb') as f:
        default_dirs = pickle.load(f)


action = sys.argv[1]
sname = sys.argv[2]


if action == '--get':
    print(default_dirs.get(sname, '/home/bryan'), end='')
elif action == '--put':
    default_dirs[sname] = sys.argv[3]
    with open(fpath, 'wb') as f:
        pickle.dump(default_dirs, f)
