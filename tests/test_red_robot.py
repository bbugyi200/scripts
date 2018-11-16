"""Tests for red_robot Script"""

import datetime as dt
import importlib.util
import importlib.machinery
import os
import shutil
import unittest.mock as mock

loader = importlib.machinery.SourceFileLoader("red_robot", "/home/bryan/Dropbox/bin/main/red_robot")
spec = importlib.util.spec_from_loader("red_robot", loader)
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)

import pytest  # noqa


def test_envvar():
    assert 'bbugyi200' == S.envvar('username')


def test_scan__PASS(remove_posts):
    post_values = [{'title': 'T1', 'url': 'U1', 'subreddit': 'subreddit1',
                    'text': None, 'fname': 'A.subreddit1'},
                   {'title': 'T2', 'url': 'U2', 'subreddit': 'subreddit2',
                    'text': None, 'fname': 'B.subreddit2'},
                   {'title': 'T3', 'url': None, 'subreddit': 'subreddit3',
                    'text': 'Markdown Text', 'fname': 'C.subreddit3'}]

    A = '{}/{}'.format(S.dp_pending, post_values[0]['fname'])
    B = '{}/{}'.format(S.dp_pending, post_values[1]['fname'])
    C = '{}/{}'.format(S.dp_pending, post_values[2]['fname'])

    post_contents = ['title: {}\nurl: {}'.format(post_values[0]['title'], post_values[0]['url']),
                     'title: {}\nurl: {}'.format(post_values[1]['title'], post_values[1]['url'])]

    with open(A, 'w') as f:
        f.write(post_contents[0])

    with open(B, 'w') as f:
        f.write(post_contents[1])

    with open(C, 'w') as f:
        f.write('title: {}\ntext: {}'.format(post_values[2]['title'], post_values[2]['text']))

    for i, D in enumerate(S.scan(S.dp_pending, S.dp_completed)):
        assert D['title'] == post_values[i]['title']
        assert D['url'] == post_values[i]['url']
        assert D['text'] == post_values[i]['text']
        assert D['subreddit'] == post_values[i]['subreddit']

        fp_pending = '{}/{}'.format(S.dp_pending, post_values[i]['fname'])
        assert not os.path.exists(fp_pending)


def test_scan__FAIL(remove_posts):
    fp_pending = '{}/{}'.format(S.dp_pending, 'NoTitle.subreddit')
    with open(fp_pending, 'w') as f:
        f.write('url: U')

    with pytest.raises(RuntimeError):
        list(S.scan(S.dp_pending, S.dp_completed))


def test_too_early__PASS(now):
    assert not S.too_early(now, '19910304')


def test_too_early__FAIL(now):
    assert S.too_early(now, '20250101')


def test_scan__MULTI_SUBREDDIT(remove_posts):
    contents = """url: "https://github.com/bbugyi200/cookie"
title:
    bash: "cookie: A Bash Script that Generates Files from Templates"
    linux: "cookie: A Template-based File Generator for Linux Admins"
"""
    with open('{}/{}'.format(S.dp_pending, 'test.post'), 'w') as f:
        f.write(contents)

    count = 0
    for D in S.scan(S.dp_pending, S.dp_completed):
        count += 1

    assert 2 == count


@pytest.fixture
def now():
    return dt.datetime.now()


@pytest.fixture
def remove_posts():
    dir_paths = [S.dp_pending, S.dp_completed]
    for dp in dir_paths:
        temp_dir = '/tmp/red_robot/{}'.format(os.path.basename(dp))
        if not os.path.exists(temp_dir):
            os.system('mkdir -p {}'.format(temp_dir))

        if not os.path.exists(dp):
            os.system('mkdir -p {}'.format(dp))

        for fn in os.listdir(dp):
            fp = '{}/{}'.format(dp, fn)
            shutil.move(fp, '{}/{}'.format(temp_dir, fn))
            if os.path.exists(fp):
                os.remove(fp)

    yield

    for dp in dir_paths:
        temp_dir = '/tmp/red_robot/{}'.format(os.path.basename(dp))
        for fname in os.listdir(dp):
            os.remove('{}/{}'.format(dp, fname))

        shutil.rmtree(dp)
        os.system('mv -f {} {}'.format(temp_dir, dp))

    shutil.rmtree('/tmp/red_robot')
