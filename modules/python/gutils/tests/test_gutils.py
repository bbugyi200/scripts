import os

import pytest
import unittest.mock as mock

import gutils

params = [('config', '/home/bryan/.config'),
          ('data', '/home/bryan/.local/share'),
          ('runtime', '/var/run/user/1000'),
          ('cache', '/home/bryan/.cache')]


@pytest.mark.parametrize('key,partial', params)
def test_xdg_init(key, partial):
    expected = '{}/{}'.format(partial, 'test_gutils')
    assert expected == gutils.xdg.init(key)
    os.rmdir(expected)


@pytest.mark.parametrize('key,expected', params)
def test_xdg_get(key, expected):
    assert expected == gutils.xdg.get(key)


def test_init_failure():
    with pytest.raises(ValueError):
        gutils.xdg.init('bad_key')


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
