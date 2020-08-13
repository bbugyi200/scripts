import datetime as dt
import importlib.util
import importlib.machinery
import os
import shutil

loader = importlib.machinery.SourceFileLoader(
    "red_robot", "/home/bryan/Sync/bin/main/red_robot"
)
spec = importlib.util.spec_from_loader("red_robot", loader)
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)

import pytest  # noqa


pytestmark = pytest.mark.skip("The 'praw' module is not installed.")


dp_pending = '/tmp/red_robot/pending'
dp_completed = '/tmp/red_robot/completed'


def test_envvar():
    assert 'bbugyi200' == S.envvar('username')


def test_scan__PASS(remove_posts):
    post_values = [
        {
            'title': 'T1',
            'url': 'U1',
            'subreddit': 'subreddit1',
            'text': None,
            'fname': 'A',
        },
        {
            'title': 'T2',
            'url': 'U2',
            'subreddit': 'subreddit2',
            'text': None,
            'fname': 'B',
        },
        {
            'title': 'T3',
            'url': None,
            'subreddit': 'subreddit3',
            'text': 'Markdown Text',
            'fname': 'C',
        },
    ]

    post_url_fmt = 'title: {}\nurl: {}\nsubreddit: {}'
    post_text_fmt = 'title: {}\ntext: {}\nsubreddit: {}'

    post_contents = []
    post_fps = []
    for i in range(3):
        if post_values[i]['url'] is None:
            post_fmt = post_text_fmt
            url_or_text = 'text'
        else:
            post_fmt = post_url_fmt
            url_or_text = 'url'

        post_contents.append(
            post_fmt.format(
                post_values[i]['title'],
                post_values[i][url_or_text],
                post_values[i]['subreddit'],
            )
        )

        post_fps.append('{}/{}'.format(dp_pending, post_values[i]['fname']))

        with open(post_fps[i], 'w') as f:
            f.write(post_contents[i])

    for _, D in enumerate(S.scan(dp_pending, dp_completed)):
        for j, vals in enumerate(post_values):
            if post_values[j]['fname'] == D['fname']:
                i = j

        assert D['title'] == post_values[i]['title']
        assert D['url'] == post_values[i]['url']
        assert D['text'] == post_values[i]['text']
        assert D['subreddit'] == post_values[i]['subreddit']


def test_scan__COMPLETES_POST(remove_posts):
    fp_post = '{}/{}'.format(dp_pending, 'post')
    with open(fp_post, 'w') as f:
        f.write('title: TITLE\nurl: URL\nsubreddit: SUBREDDIT')

    assert os.path.exists(fp_post)

    list(S.scan(dp_pending, dp_completed))

    assert not os.path.exists(fp_post)


def test_scan__FAIL(remove_posts):
    fp_pending = '{}/{}'.format(dp_pending, 'NoTitle.subreddit')
    with open(fp_pending, 'w') as f:
        f.write('url: U')

    with pytest.raises(RuntimeError):
        list(S.scan(dp_pending, dp_completed))


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
    with open('{}/{}'.format(dp_pending, 'test.post'), 'w') as f:
        f.write(contents)

    count = 0
    for D in S.scan(dp_pending, dp_completed):
        count += 1

    assert 2 == count


@pytest.fixture
def now():
    return dt.datetime.now()


@pytest.fixture
def remove_posts():
    os.system('mkdir -p {}'.format(dp_pending))
    os.system('mkdir -p {}'.format(dp_completed))

    yield

    shutil.rmtree('/tmp/red_robot')
