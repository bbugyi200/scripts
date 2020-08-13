"""Writes a weather report to some bar using a FIFO."""

import re
import subprocess as sp  # noqa: F401
import sys
import time
from typing import NamedTuple, Optional, Sequence

import gutils
from loguru import logger as log


@gutils.catch
def main(argv: Sequence[str] = None) -> int:
    if argv is None:
        argv = sys.argv

    args = parse_cli_args(argv)

    gutils.logging.configure(__file__, debug=args.debug, verbose=args.verbose)

    return run(args)


class Arguments(NamedTuple):
    debug: bool
    verbose: bool
    zipcode: str


def parse_cli_args(argv: Sequence[str]) -> Arguments:
    parser = gutils.ArgumentParser()
    parser.add_argument(
        'zipcode', nargs='?', default='08060', help='zip code of location'
    )

    args = parser.parse_args(argv[1:])
    kwargs = dict(args._get_kwargs())

    return Arguments(**kwargs)


def run(args: Arguments) -> int:
    raw_output = run_weather_report(args.zipcode)

    loc = get_group('Current conditions at (.*)\n', raw_output)
    temp = get_temp(raw_output)
    sky = get_group(r'Sky conditions: ([A-z\s]+)$', raw_output)
    wind = get_wind(raw_output)

    assert loc is not None
    report = format_report(loc, temp, sky, wind)
    print(report)

    return 0


def run_weather_report(zipcode: str) -> str:
    """Runs the 'weather-report' command.

    Returns:
        Raw output of weather-report command.
    """
    cmd_list = ['weather-report']
    opts = ['--setpath', '/usr/share/weather-util', zipcode, '--no-cache']
    cmd_list.extend(opts)

    for i in range(6):
        child = sp.Popen(cmd_list, stdout=sp.PIPE, stderr=sp.DEVNULL)
        out = child.communicate()[0]
        rc = child.returncode

        if rc == 0:
            log.debug('weather-report Attempt #{}: SUCCESS'.format(i + 1))
            break

        log.debug('weather-report Attempt #{}: FAILURE'.format(i + 1))
        time.sleep(2 ** i)

    return out.decode().strip()


def get_temp(raw_output: str) -> str:
    """Returns temperature."""
    temp = get_group(r'Temperature: ([0-9]+\.[0-9]) F', raw_output)
    if temp is None:
        return "N/A"
    else:
        return f'{round(float(temp))} F'


def get_wind(raw_output: str) -> Optional[str]:
    """Returns wind description."""
    wind = get_group(r'Wind: .*?([0-9\-]+ MPH)', raw_output)

    if wind is None:
        wind = get_group(r'Wind: (.*)', raw_output)

    return wind


def get_group(pttrn: str, string: str) -> Optional[str]:
    """Returns the first group matched from a regex pattern."""
    match = re.search(pttrn, string, re.M)
    if match:
        return match.groups()[0]
    else:
        return None


def format_report(
    loc: str, temp: str, sky: Optional[str], wind: Optional[str]
) -> str:
    """Formats weather report."""
    report_fmt = '{}  |  TEMP: {}'
    report = report_fmt.format(loc, temp)

    if sky is not None:
        report = '{}  |  SKY: {}'.format(report, sky)

    if wind is not None:
        report = '{}  |  WIND: {}'.format(report, wind)

    return report


if __name__ == "__main__":
    sys.exit(main())
