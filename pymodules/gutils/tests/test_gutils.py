import os

import pytest
import unittest.mock as mock

import gutils

params = [('config', '/home/bryan/.config/test_gutils'),
          ('data', '/home/bryan/.local/share/test_gutils'),
          ('runtime', '/run/user/1000/test_gutils'),
          ('cache', '/home/bryan/.cache/test_gutils')]


@pytest.mark.parametrize('key,expected', params)
def test_getdir(key, expected):
    assert expected == gutils.xdg.getdir(key)
    os.rmdir(expected)


def test_getdir_failure():
    with pytest.raises(ValueError):
        gutils.xdg.getdir('bad_key')


def test_notify():
    gutils.notify('Test Notification', '-t', '2000')


def test_notify_urgency():
    gutils.notify('Low Urgency Test Notification', urgency='low')


def test_notify_failure():
    with pytest.raises(ValueError):
        gutils.notify()

    with pytest.raises(ValueError):
        gutils.notify('Test Notification', urgency='bad_value')


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
    log.exception.assert_called()


def test_context_debug():
    log = gutils.logging.getEasyLogger(__name__)
    with gutils.logging.context(log, debug=True):
        log.debug('TEST')

    logfile = '/var/tmp/{}.log'.format(os.path.basename(__file__).replace('.py', ''))
    assert os.path.isfile(logfile)
    assert 'TEST' in open(logfile, 'r').read()
