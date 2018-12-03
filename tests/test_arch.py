"""Tests for 'arch' Script"""

import datetime as dt
import importlib.util
import importlib.machinery
import shutil
import sys  # noqa
import os  # noqa
import unittest.mock as mock

loader = importlib.machinery.SourceFileLoader("arch", "/home/bryan/Dropbox/bin/main/arch")
spec = importlib.util.spec_from_loader("arch", loader)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

import pytest  # noqa

temp_dir = '/tmp/test_arch'
arch_dir = '{}/archive'.format(temp_dir)
arch_tar = '{}/.archive.tar.gz'.format(temp_dir)
foo_path = '{}/foo'.format(temp_dir)
bar_path = '{}/bar'.format(temp_dir)


@pytest.fixture(scope='function', autouse=True)
def file_raw():
    os.mkdir(temp_dir)
    os.chdir(temp_dir)
    with open('foo', 'w') as f:
        f.write('')

    yield

    shutil.rmtree(temp_dir)


@pytest.mark.usefixtures("file_raw")
class TestA:
    def test_archive(self):
        m.archive(['foo'])
        assert os.path.isfile('{}/foo'.format(arch_dir))

    def test_restore(self):
        with pytest.raises(RuntimeError):
            m.restore(['foo'])
