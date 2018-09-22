"""Return Colorized Strings using ASCII Color Escape Codes"""


def _colorizer_factory(N):
    def colorizer(msg):
        return '%s%s%s' % ('\033[{}m'.format(N), msg, '\033[0m')
    return colorizer


black = _colorizer_factory(30)
red = _colorizer_factory(31)
green = _colorizer_factory(32)
yellow = _colorizer_factory(33)
blue = _colorizer_factory(34)
magenta = _colorizer_factory(35)
cyan = _colorizer_factory(36)
white = _colorizer_factory(37)
