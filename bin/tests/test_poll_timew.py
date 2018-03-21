import imp

import pytest

m = imp.load_source('poll-timew', '/home/bryan/Dropbox/scripts/bin/xmonad/poll-timew')


def test_style_time():
    assert m.style_time('01:23:45') == '1.4h'


def test_get_tag_time():
    assert m.get_tag_time('other', 'day') == '0:38:56'
    assert m.get_tag_time('blahsdfsfds', 'week') == '0:00:00'


outputs = ['Tracking Dev Dev.Test "Testing Stuff"\nStarted sdflkdsjflskdfj\nCurrent sdfkds slksjdfl\nTotal          1:51:28', 'Tracking "Project: ProjectA" Tag Tag.Sub.AndMore\nStarted klsjdflskjfsdf\nCurrent sdlkfjsdklfjsd\nTotal          2:19:02', 'Tracking "Migrate from watson to timew" Meta\nsdflkjsldfklj\n sdfljksdlkfj  00:30:57\n\n']

expected_values = [('Testing Stuff', 'Dev', '1.9h'), ('ProjectA', 'Tag', '2.3h'), ('Migrate from watson to timew', 'Meta', '0.5h')]


@pytest.mark.parametrize('output, expected', list(zip(outputs, expected_values)))
def test_parse_status(output, expected):
    project, tag, currtime = m.parse_status(output)

    assert project == expected[0]
    assert tag == expected[1]
    assert currtime == expected[2]
