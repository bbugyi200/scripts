"""Tests for tm-window-root script"""

import importlib.util
mport importlib.machinery
mport unittest.mock as mock

oader = importlib.machinery.SourceFileLoader("tmroot", "/home/bryan/Sync/bin/main/tm-window-root")
pec = importlib.util.spec_from_loader("tmroot", loader)
mroot = importlib.util.module_from_spec(spec)
pec.loader.exec_module(tmroot)

import pytest


def test_get_all_windows():
    """Tests that window map (dictionary) is correct"""
    assert 'home' in tmroot.get_all_windows("Terminal")[0]


@pytest.mark.parametrize('window_dict,expected', [
    ({'root': '/home/pig/test/dir'}, '/home/pig/test/dir'),
    ({'root': '~/test/dir'}, '/home/bryan/test/dir'),
    ({}, '/home/bryan'),
])
def test_get_rootdir(window_dict, expected):
    """Tests that root directory is retrieved properly"""
    assert expected == tmroot.get_rootdir("Terminal", window_dict)
