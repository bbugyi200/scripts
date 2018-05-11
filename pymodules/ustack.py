import os
import pickle

import gutils


class UStack:
    def __init__(self):
        self.fpath = '{}/dirstack.pickle'.format(gutils.xdg.getdir('data'))
        if os.path.isfile(self.fpath):
            with open(self.fpath, 'rb') as f:
                self.stack = pickle.load(f)
        else:
            self.stack = list()

    def push(self, directory):
        self.stack.append(directory)
        self.save()

    def pop(self):
        try:
            directory = self.stack.pop()
            self.save()
            return directory
        except IndexError as e:
            return os.getcwd()

    def save(self):
        with open(self.fpath, 'wb+') as f:
            pickle.dump(self.stack, f)
