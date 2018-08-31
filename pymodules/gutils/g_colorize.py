"""Return Colorized Strings using ASCII Color Escape Codes"""


def black(msg):
    return _colorize(msg, 30)


def red(msg):
    return _colorize(msg, 31)


def green(msg):
    return _colorize(msg, 32)


def yellow(msg):
    return _colorize(msg, 33)


def blue(msg):
    return _colorize(msg, 34)


def magenta(msg):
    return _colorize(msg, 35)


def cyan(msg):
    return _colorize(msg, 36)


def white(msg):
    return _colorize(msg, 37)


def _colorize(msg, N):
    return '%s%s%s' % (_get_ccode(N), msg, _get_ccode(0))


def _get_ccode(N):
    return '\033[{}m'.format(N)
