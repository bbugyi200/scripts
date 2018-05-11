import os

import pytest

import gutils


params = [('config', '/home/bryan/.config/test_xdg'),
          ('data', '/home/bryan/.local/share/test_xdg'),
          ('runtime', '/run/user/1000/test_xdg'),
          ('cache', '/home/bryan/.cache/test_xdg')]


@pytest.mark.parametrize('key,expected', params)
def test_getdir(key,expected):
    assert expected == gutils.xdg.getdir(key)
    os.rmdir(expected)


def test_getdir_failure():
    with pytest.raises(AssertionError):
        gutils.xdg.getdir('bad_key')
