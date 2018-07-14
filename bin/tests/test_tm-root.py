"""Tests for tm-root script"""

import importlib.util
import importlib.machinery
import unittest.mock as mock

loader = importlib.machinery.SourceFileLoader("tmroot", "/home/bryan/Dropbox/scripts/bin/main/tm-root")
spec = importlib.util.spec_from_loader("tmroot", loader)
tmroot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tmroot)

import pytest  # noqa


def test_get_all_windows():
    """Tests that window map (dictionary) is correct"""
    assert 'home' in tmroot.get_all_windows("Terminal")


@pytest.mark.parametrize('window_map,expected', [
    ({'root': '/home/pig/test/dir'}, '/home/pig/test/dir'),
    ({'root': '~/test/dir'}, '/home/bryan/test/dir'),
    ({'badkey': None}, '/home/bryan'),
])
def test_get_rootdir(window_map, expected):
    """Tests that root directory is retrieved properly"""
    assert expected == tmroot.get_rootdir("Terminal", window_map)