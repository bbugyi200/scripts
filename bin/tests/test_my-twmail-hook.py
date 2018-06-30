"""Tests for my-twmail-hook"""

import datetime as dt
import importlib.util
import importlib.machinery
import os
import unittest.mock as mock

loader = importlib.machinery.SourceFileLoader("twmail", "/home/bryan/Dropbox/scripts/bin/main/my-twmail-hook")
spec = importlib.util.spec_from_loader("twmail", loader)
twmail = importlib.util.module_from_spec(spec)
spec.loader.exec_module(twmail)

import pytest  # noqa


def test_main(sp_mock):
    twargs = ['+inbox', '+note']
    description = "Mr Pig is fat and stinky"
    _set_body(twargs, description)

    twmail.main()
    sp_mock.call.assert_called_with(['task', 'add', *twargs, description])


def test_parse_body(sp_mock):
    twargs = ['+inbox', 'due:today']
    dirty_description = "''\\  the foo went to the bar. ''\n"
    clean_description = "The foo went to the bar."

    _set_body(twargs, dirty_description)

    actual_twargs, actual_description = twmail.parse_body(_get_body(twargs, dirty_description))

    assert actual_twargs == twargs
    assert actual_description == clean_description


def test_maybe_correct_date_true(sp_mock):
    twargs = ['+inbox']
    date = _format_date(dt.datetime.now() - dt.timedelta(days=1))
    twmail.maybe_correct_date(twargs, date)
    assert sp_mock.call.called


def test_maybe_correct_date_false(sp_mock):
    twargs = ['+inbox']
    date = _format_date(dt.datetime.now())
    twmail.maybe_correct_date(twargs, date)
    assert not sp_mock.call.called

    twargs = ['+today']
    date = _format_date(dt.datetime.now() - dt.timedelta(days=1))
    twmail.maybe_correct_date(twargs, date)
    assert not sp_mock.call.called


def _set_body(twargs, description):
    _add_tw_env_var('body', _get_body(twargs, description))


def _get_body(twargs, description):
    return '{} -- {}'.format(' '.join(twargs), description)


@pytest.fixture
def sp_mock():
    twmail.sp = mock.MagicMock()
    return twmail.sp


@pytest.fixture(autouse=True)
def add_tw_env_vars(env_dict):
    for key, val in env_dict.items():
        _add_tw_env_var(key, val)


def _add_tw_env_var(var, val):
    env_var = 'TWMAIL_' + var.upper()
    os.environ[env_var] = val


@pytest.fixture
def env_dict():
    return {
        'from': 'bryanbugyi34@gmail.com',
        'date': _format_date(dt.datetime.now()),
        'message_id': '65601F7D-3828-48CE-9523-D317127C31BA@gmail.com',
        'to': 'bmbinbox34@gmail.com',
        'subject': 'TaskWarrior',
    }


def _format_date(date_dt):
    return date_dt.strftime('%Y-%m-%dT%H:%M:%S-04:00')
