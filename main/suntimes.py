"""Writes sunset time to STDOUT"""

import datetime as dt
import enum
import os
import re
import sys
from typing import NamedTuple, Sequence, TypeVar

from bs4 import BeautifulSoup
import gutils
from gutils.io import eprint
from gutils.result import Err, Ok, Result, init_err_helper
from loguru import logger as log  # pylint: disable=unused-import
import requests


scriptname = os.path.basename(os.path.realpath(__file__))
USER_AGENT = {
    'User-Agent': (
        'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.3 (KHTML,'
        ' like Gecko) Chrome/6.0.472.63 Safari/534.3'
    )
}


class WebScrapingError(Exception):
    """Error occurred while attempting to scrape a web page."""


_T = TypeVar("_T")
WErr = init_err_helper(WebScrapingError)
WResult = Result[_T, WebScrapingError]


@gutils.catch
def main(argv: Sequence[str] = None) -> int:
    if argv is None:
        argv = sys.argv

    args = parse_cli_args(argv)

    gutils.logging.configure(__file__, debug=args.debug, verbose=args.verbose)

    return run(args)


class RiseOrSet(enum.Enum):
    RISE = "rise"
    SET = "set"

    def __str__(self) -> str:
        return str(self.value)


class Arguments(NamedTuple):
    debug: bool
    verbose: bool
    rise_or_set: RiseOrSet


def parse_cli_args(argv: Sequence[str]) -> Arguments:
    parser = gutils.ArgumentParser()
    parser.add_argument(
        'rise_or_set',
        choices=list(RiseOrSet),
        type=RiseOrSet,
        help='Get sunrise or sunset?',
    )

    args = parser.parse_args(argv[1:])
    kwargs = dict(args._get_kwargs())

    return Arguments(**kwargs)


def run(args: Arguments) -> int:
    time_string_r = get_time_string(args.rise_or_set)
    if isinstance(time_string_r, Err):
        eprint(f"[ERROR] Unable to determine sun{args.rise_or_set} time.")

        if args.debug:
            e = time_string_r.err()

            eheader = f"----- {type(e).__name__} -----"
            bar = "-" * len(eheader)

            eprint("\n{0}\n{1}\n{0}\n{2}".format(bar, eheader, str(e)))

        return 1

    time_string = time_string_r.ok()
    print(time_string)

    return 0


def get_time_string(rise_or_set: RiseOrSet) -> WResult[str]:
    url = 'https://www.google.com/search?q=sun{}+times'.format(rise_or_set)
    google_soup = _get_soup(url)
    return _get_ts_from_google_search(google_soup, rise_or_set)


def _get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=USER_AGENT)
    soup = BeautifulSoup(resp.text, "lxml")
    return soup


def _get_ts_from_google_search(
    soup: BeautifulSoup, rise_or_set: RiseOrSet
) -> WResult[str]:
    am_or_pm = 'AM' if rise_or_set is RiseOrSet.RISE else 'PM'
    pttrn = '[0-9][0-9]?:[0-9][0-9] {}'.format(am_or_pm)

    time_divs = soup.find_all(["div", "span"], text=re.compile(pttrn))

    if not time_divs:
        return WErr(
            "Unable to find a match in the following HTML source using"
            f" pattern {pttrn!r}:\n\n{soup.prettify()}"
        )

    time_tag = time_divs[0]
    match = re.search(f"({pttrn})", time_tag.text)
    assert match is not None

    raw_time_string = match.groups()[0]
    dt_suntime = dt.datetime.strptime(raw_time_string, '%I:%M %p')

    time_string = dt_suntime.strftime('%H:%M')
    return Ok(time_string)


if __name__ == "__main__":
    sys.exit(main())
