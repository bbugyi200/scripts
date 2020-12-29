"""
Generate a random N character password.
"""

import argparse as ap
import random
import string
import sys
from typing import (
    Any,
    Callable,
    MutableMapping,
    NamedTuple,
    NoReturn,
    Sequence,
)

import gutils
from loguru import logger as log  # pylint: disable=unused-import


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
    password_length: int
    use_uppercase: bool
    use_lowercase: bool
    use_digits: bool
    use_symbols: bool
    reverse: bool
    include_chars: str
    exclude_chars: str


def parse_cli_args(argv: Sequence[str]) -> Arguments:
    if any(opt in argv for opt in ["-r", "--reverse"]):
        store_bool = "store_true"
    else:
        store_bool = "store_false"

    parser = gutils.ArgumentParser()
    parser.add_argument(
        "password_length",
        nargs="?",
        default="12:20",
        help=(
            "The length (in characters) of the password to generate. You can"
            " specify a specific length (e.g. '15') or a lower bound and an"
            " upper bound, separated by a colon, to randomly select the"
            " password length from (e.g. '8:15' will randomly select a"
            " password length between 8 and 15). Defaults to %(default)r."
        ),
    )
    parser.add_argument(
        "-U",
        "--no-uppercase",
        dest="use_uppercase",
        action=store_bool,
        help="Do NOT allow uppercase letters to be included in the password.",
    )
    parser.add_argument(
        "-L",
        "--no-lowercase",
        dest="use_lowercase",
        action=store_bool,
        help="Do NOT allow lowercase letters to be included in the password.",
    )
    parser.add_argument(
        "-D",
        "--no-digits",
        dest="use_digits",
        action=store_bool,
        help="Do NOT allow digits (i.e. 0-9) to be included in the password.",
    )
    parser.add_argument(
        "-S",
        "--no-symbols",
        dest="use_symbols",
        action=store_bool,
        help=(
            "Do NOT allow symbols (e.g. '@', '!', '>', ...) to be included in"
            " the password."
        ),
    )
    parser.add_argument(
        "-r",
        "--reverse",
        action="store_true",
        help="Reverse the effects of the -U, -L, -S, and -D options.",
    )
    parser.add_argument(
        "-i",
        "--include-chars",
        help=(
            "Extra characters to consider when randomly generating a password."
        ),
    )
    parser.add_argument(
        "-x",
        "--exclude-chars",
        help=(
            "Characters to explicitly exclude from the characters which are"
            " considered when randomly generating a password."
        ),
    )

    args = parser.parse_args(argv[1:])
    _validate_cli_args(args, parser.error)

    kwargs = dict(args._get_kwargs())
    _set_password_length(kwargs)

    return Arguments(**kwargs)


def _validate_cli_args(
    args: ap.Namespace, parser_error: Callable[[str], NoReturn]
) -> None:
    if not (
        args.use_uppercase
        or args.use_lowercase
        or args.use_digits
        or args.use_symbols
        or args.include_chars
    ):
        if args.reverse:
            emsg = (
                "Must use at least one of -U, -L, -D, or -S options when the"
                " --reverse option is given, since we cannot create a password"
                " consisting of only characters from the empty set."
            )
        else:
            emsg = (
                "Cannot use ALL of the -U, -L, -D, and -S options, since this"
                " leaves us with no characters that we are allowed to include"
                " in our newly generated password."
            )

        parser_error(emsg)

    last = 0
    for N in args.password_length.split(":", 1):
        try:
            n = int(N)
            assert last < n
            last = n
        except (AssertionError, ValueError):
            parser_error(
                "The 'password_length' argument must be of the form 'L[:U]',"
                " where both 'L' and 'U' are positive nonzero integer values"
                " such that 'U' (if specified) is greater than 'L'."
            )

    if (
        args.include_chars
        and args.exclude_chars
        and any(ch in args.include_chars for ch in args.exclude_chars)
    ):
        parser_error(
            "The character sets specified by the -i and -x options CANNOT"
            " intersect."
        )


def _set_password_length(kwargs: MutableMapping[str, Any]) -> None:
    raw_password_length = kwargs["password_length"]

    if ":" in raw_password_length:
        (lower, upper) = raw_password_length.split(":", 1)
        (plower, pupper) = (
            int(lower),
            int(upper) + 1,
        )
    else:
        plower = int(raw_password_length)
        pupper = plower + 1

    password_length = random.choice(range(plower, pupper))
    kwargs["password_length"] = password_length


def run(args: Arguments) -> int:
    password = _generate_password(args)
    print(password)
    return 0


def _generate_password(args: Arguments) -> str:
    password_chars = ""

    if args.use_uppercase:
        bad_uppercase = "O" if args.use_digits else ""
        password_chars += "".join(
            set(string.ascii_uppercase) - set(bad_uppercase)
        )

    if args.use_lowercase:
        password_chars += string.ascii_lowercase

    if args.use_digits:
        password_chars += string.digits

    if args.use_symbols:
        bad_symbols = "".join(["\\", '"', "'", "`"])
        password_chars += "".join(set(string.punctuation) - set(bad_symbols))

    if args.include_chars:
        password_chars += args.include_chars

    if args.exclude_chars:
        password_chars = "".join(set(password_chars) - set(args.exclude_chars))

    log.debug(f"Password length:  {args.password_length}")
    log.debug(
        f"Number of password characters to choose from:  {len(password_chars)}"
    )

    password = "".join(
        random.choice("".join(set(password_chars)))
        for _ in range(args.password_length)
    )

    return password


if __name__ == "__main__":
    sys.exit(main())
