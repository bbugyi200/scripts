import gutils


def test_getdir():
    assert gutils.xdg.getdir('config') == '/home/bryan/.config/test_xdg'
    assert gutils.xdg.getdir('data') == '/home/bryan/.local/share/test_xdg'
    assert gutils.xdg.getdir('runtime') == '/run/user/1000/test_xdg'
    assert gutils.xdg.getdir('cache') == '/home/bryan/.cache/test_xdg'
