"""Writes a weather report to some bar using a FIFO."""

import datetime as dt
import re
import subprocess as sp  # noqa: F401
import sys
import time
from typing import NamedTuple, Optional, Sequence

import gutils
from gutils.io import eprint
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
    weather_cmd: str
    attempts: int
    timeout: int
    max_delay: int


def parse_cli_args(argv: Sequence[str]) -> Arguments:
    parser = gutils.ArgumentParser()
    parser.add_argument(
        "zipcode", nargs="?", default="08060", help="zip code of location"
    )
    parser.add_argument(
        "--weather-cmd",
        default="weather",
        help=(
            "The command used to retrieve the weather report from the"
            " command-line."
        ),
    )
    parser.add_argument(
        "-n",
        "--attempts",
        type=int,
        default=7,
        help=(
            "How many times should we attempt to run this command in the event"
            " of failure/timeout?"
        ),
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=30,
        help=(
            "How long should we wait (in seconds) for the this command to"
            " complete?"
        ),
    )
    parser.add_argument(
        "--max-delay",
        default=300,
        type=int,
        help="The maximum sleep time between command attempts.",
    )

    args = parser.parse_args(argv[1:])
    kwargs = dict(args._get_kwargs())

    return Arguments(**kwargs)


def run(args: Arguments) -> int:
    raw_output = run_weather_cmd(
        args.weather_cmd,
        args.zipcode,
        attempts=args.attempts,
        timeout=args.timeout,
        max_delay=args.max_delay,
    )
    if raw_output is None:
        eprint(f"[ERROR] The {args.weather_cmd!r} command failed.")
        return 1

    loc = get_group("Current conditions at (.*)\n", raw_output)
    temp = get_temp(raw_output)
    humidity = get_humidity(raw_output)
    sky = get_group(r"Sky conditions: ([A-z\s]+)$", raw_output)
    wind = get_wind(raw_output)

    assert loc is not None
    report = format_report(loc, temp, sky, wind, humidity)
    print(report)

    return 0


def run_weather_cmd(
    weather_cmd: str,
    zipcode: str,
    *,
    attempts: int,
    timeout: int,
    max_delay: int,
) -> Optional[str]:
    """Runs the 'weather' command.

    Returns:
        Raw output of 'weather' command.
    """
    cmd_list = [weather_cmd]
    opts = ["--setpath", "/usr/share/weather-util", zipcode, "--no-cache"]
    cmd_list.extend(opts)

    def log_cmd(msg: str) -> None:
        msg = "{!r} command: {}".format(weather_cmd, msg)
        log.debug(msg)

    rc = None
    for i in range(attempts):
        if i > 0:
            # delay => 10s, 20s, 40s, 80s, ..., max_delay
            delay = min(max_delay, 2 ** (i - 1) * 10)
            log.debug(f"Waiting {delay}s before trying again.")
            time.sleep(delay)

        log_cmd(f"Attempt #{i + 1}")
        child = sp.Popen(cmd_list, stdout=sp.PIPE, stderr=sp.PIPE)

        try:
            stdout, stderr = child.communicate(timeout=timeout)
        except sp.TimeoutExpired:
            log_cmd(f"TIMEOUT (after {timeout}s)")
        else:
            rc = child.returncode

            output = stdout.decode().strip()

            if rc == 0:
                log_cmd("SUCCESS")
                break

            output += stderr.decode().strip()
            log_cmd(f"FAILURE: {output}")

    if rc == 0:
        return output
    else:
        return None


def get_temp(raw_output: str) -> str:
    """Returns temperature."""
    temp = get_group(r"Temperature: ([0-9]+\.[0-9]) F", raw_output)
    if temp is None:
        return "N/A"
    else:
        return f"{round(float(temp))} F"


def get_humidity(raw_output: str) -> Optional[str]:
    humidity = get_group("Humidity:[ ]*([1-9][0-9]*%)", raw_output)
    return humidity


def get_wind(raw_output: str) -> Optional[str]:
    """Returns wind description."""
    wind = get_group(r"Wind: .*?([0-9\-]+ MPH)", raw_output)

    if wind is None:
        wind = get_group(r"Wind: (.*)", raw_output)

    return wind


def get_group(pttrn: str, string: str) -> Optional[str]:
    """Returns the first group matched from a regex pattern."""
    match = re.search(pttrn, string, re.M)
    if match:
        return match.groups()[0]
    else:
        return None


def format_report(
    _loc: str,
    temp: str,
    sky: Optional[str],
    wind: Optional[str],
    humidity: Optional[str],
) -> str:
    """Formats weather report."""
    report_fmt = "{}   :::   TEMP: {}"
    now = dt.datetime.now()
    timestamp = now.strftime("@%H:%M:%S")
    report = report_fmt.format(timestamp, temp)

    if humidity is not None:
        report = f"{report}  |  HUMIDITY: {humidity}"

    if sky is not None:
        report = f"{report}  |  SKY: {sky}"

    if wind is not None:
        report = f"{report}  |  WIND: {wind}"

    return report


if __name__ == "__main__":
    sys.exit(main())
