import os

import pytest
import unittest.mock as mock

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
    with pytest.raises(ValueError):
        gutils.xdg.getdir('bad_key')


params = [('echo "Hi There!"', str, 'Hi There!'),
          ('echo 5', int, 5)]


@pytest.mark.parametrize('cmd,cast,expected', params)
def test_shell(cmd,cast,expected):
    assert expected == gutils.subprocess.shell(cmd,cast)


def test_notify():
    gutils.subprocess.notify('Test Notification', '-t', '2000')


def test_notify_failure():
    with pytest.raises(AssertionError):
        gutils.subprocess.notify()


@mock.patch('sys.exit')
def test_context_runtime(exit):
    log = mock.Mock()
    with gutils.logging.context(log):
        raise RuntimeError('Error Message')
    log.error.assert_called()


def test_context_generic():
    log = mock.Mock()
    with pytest.raises(Exception), gutils.logging.context(log):
        raise Exception
    log.error.assert_called()
