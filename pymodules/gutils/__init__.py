""" Global Utilities """

import inspect
import os
import subprocess as sp

import gutils.g_logging as logging  # noqa: F401
import gutils.g_xdg as xdg  # noqa: F401
import gutils.shared as shared


class StillAliveException(Exception):
    """ Raised when Old Instance of Script is Still Running """
    def __init__(self, pid):
        self.pid = pid


def create_pidfile():
    """ Writes PID to File """
    PIDFILE = "{}/pid".format(xdg.getdir('runtime', stack=inspect.stack()))
    if os.path.isfile(PIDFILE):
        old_pid = int(open(PIDFILE, 'r').read())
        try:
            os.kill(old_pid, 0)
        except OSError as e:
            pass
        except ValueError as e:
            if old_pid != '':
                raise
        else:
            raise StillAliveException(old_pid)

    pid = os.getpid()
    open(PIDFILE, 'w').write(str(pid))


def shell(cmd, cast=str):
    """ Run Shell Command """
    out = sp.check_output(cmd, shell=True)
    return cast(out.decode().strip())


def notify(*args):
    """ Sends Desktop Notification """
    assert len(args) > 0, 'No notification message specified.'

    cmd_list = ['notify-send']
    cmd_list.extend([shared.scriptname(inspect.stack())])
    cmd_list.extend(args)

    sp.Popen(cmd_list)


def textme(msg):
    """ Sends SMS Message to my Cell Phone """
    sp.check_call(['textme', msg], stdout=sp.DEVNULL, stderr=sp.STDOUT)
