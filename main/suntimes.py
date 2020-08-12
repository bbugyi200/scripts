"""Writes sunset time to STDOUT"""

import datetime as dt
import os
import re
import sys
from typing import NamedTuple, Sequence

import gutils
from loguru import logger as log  # pylint: disable=unused-import
import requests


scriptname = os.path.basename(os.path.realpath(__file__))
USER_AGENT = {
    'User-Agent': (
        'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.3 (KHTML,'
        ' like Gecko) Chrome/6.0.472.63 Safari/534.3'
    )
}


@gutils.catch
def main(argv: Sequence[str] = None) -> int:
    if argv is None:
        argv = sys.argv

    args = parse_cli_args(argv)

    gutils.logging.configure(__file__, debug=args.debug, verbose=args.verbose)

    resp = requests.get(
        'https://www.google.com/search?q=sun{}+times'.format(args.rise_or_set),
        headers=USER_AGENT,
    )
    source = resp.text

    am_or_pm = 'AM' if args.rise_or_set == 'rise' else 'PM'
    pttrn = '>([0-9][0-9]?:[0-9][0-9] {})</(?:div|span)>'.format(am_or_pm)
    match = re.search(pttrn, source)

    if match is None:
        raise RuntimeError(
            'Unable to find match for sun{} time in the HTML source.'.format(
                args.rise_or_set
            )
        )

    time_string = match.groups()[0]
    dt_suntime = dt.datetime.strptime(time_string, '%I:%M %p')

    new_time_string = dt_suntime.strftime('%H:%M')
    print(new_time_string)

    return 0


class Arguments(NamedTuple):
    debug: bool
    verbose: bool
    rise_or_set: str


def parse_cli_args(argv: Sequence[str]) -> Arguments:
    parser = gutils.ArgumentParser()
    parser.add_argument(
        'rise_or_set', choices=('rise', 'set'), help='Get sunrise or sunset?'
    )

    args = parser.parse_args(argv[1:])
    kwargs = dict(args._get_kwargs())

    return Arguments(**kwargs)


if __name__ == "__main__":
    sys.exit(main())
