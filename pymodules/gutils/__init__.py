""" Global Utilities """

import inspect
import os
import subprocess as sp

import gutils.g_logging as logging  # noqa: F401
import gutils.g_xdg as xdg  # noqa: F401


class StillAliveException(Exception):
    pid = -1


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
            e = StillAliveException()
            e.pid = old_pid
            raise e

    pid = os.getpid()
    open(PIDFILE, 'w').write(str(pid))


def shell(cmd, cast=str):
    """ Run Shell Command """
    out = sp.check_output(cmd, shell=True)
    return cast(out.decode().strip())
