""" Utility Functions that Make use of the subprocess Module """

import inspect
import subprocess as sp

import gutils.shared as shared


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
