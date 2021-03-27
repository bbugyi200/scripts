"""SSH into bloomberg servers using 'pexpect'."""

import sys
from typing import NamedTuple, Sequence

from bugyi import subprocess as bsp
from bugyi.core import ArgumentParser, main_factory
from loguru import logger as log  # pylint: disable=unused-import
import pexpect


class Arguments(NamedTuple):
    debug: bool
    host: str
    verbose: bool


def parse_cli_args(argv: Sequence[str]) -> Arguments:
    parser = ArgumentParser()
    parser.add_argument(
        "host", type=_host_type, help="The hostname of the server to SSH into."
    )

    args = parser.parse_args(argv[1:])

    kwargs = dict(args._get_kwargs())
    return Arguments(**kwargs)


def _host_type(arg: str) -> str:
    if arg.endswith(".bloomberg.com"):
        return arg
    else:
        return arg + ".bloomberg.com"


def run(args: Arguments) -> int:
    ssh_pass, _err = bsp.unsafe_popen(
        ["pass", "show", "bloomberg_ssh_password"]
    )

    px = pexpect.spawn(f"ssh {args.host}")
    for _ in range(2):
        i = px.expect(["[Pp]assword: ", "[Ll]ast [Ll]ogin: .*"], timeout=60)
        if i == 0:
            px.sendline(ssh_pass)
        else:
            break

    px.interact()

    return 0


main = main_factory(parse_cli_args, run)
if __name__ == "__main__":
    sys.exit(main())
