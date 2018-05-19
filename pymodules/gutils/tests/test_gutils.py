import os

import pytest

import gutils

params = [('config', '/home/bryan/.config/test_gutils'),
          ('data', '/home/bryan/.local/share/test_gutils'),
          ('runtime', '/run/user/1000/test_gutils'),
          ('cache', '/home/bryan/.cache/test_gutils')]


@pytest.mark.parametrize('key,expected', params)
def test_getdir(key,expected):
    assert expected == gutils.xdg.getdir(key)
    os.rmdir(expected)


def test_getdir_failure():
    with pytest.raises(AssertionError):
        gutils.xdg.getdir('bad_key')


params = [('echo "Hi There!"', str, 'Hi There!'),
          ('echo 5', int, 5)]


@pytest.mark.parametrize('cmd,cast,expected', params)
def test_shell(cmd,cast,expected):
    assert expected == gutils.shell(cmd,cast)


def test_notify():
    gutils.notify('Test Notification', timeout=2)


def test_notify_failure():
    with pytest.raises(AssertionError):
        gutils.notify('Bad Timeout Value', timeout=2.5)
