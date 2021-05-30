"""Interface for System Maintenance Tasks"""

from dataclasses import dataclass
import datetime as dt
import enum
import os
from pathlib import Path
import signal
import subprocess as sp
import sys
import textwrap
from types import FrameType
from typing import Final, MutableSequence, Optional, Sequence

from bugyi import cli, xdg
from bugyi.core import main_factory, secret as get_secret
from bugyi.io import getch, imsg
from loguru import logger as log  # pylint: disable=unused-import


TS_FMT: Final = "%Y%m%d%H%M%S"


class Action(enum.Enum):
    UPDATE = enum.auto()
    CLEANUP = enum.auto()
    MAINT_CHECK = enum.auto()


@dataclass(frozen=True)
class Arguments(cli.Arguments):
    action: Action
    dsl: Optional[str]
    max_days: Optional[str]
    pretend: bool


def parse_cli_args(argv: Sequence[str]) -> Arguments:
    parser = cli.ArgumentParser()

    parser.add_argument(
        "-M",
        "--max-days",
        nargs="?",
        help=(
            "Max number of days without update before complaining. This "
            "option is only checked when used with the '--maint-check' option."
        ),
    )

    g1 = parser.add_mutually_exclusive_group()
    g1.add_argument(
        "-u",
        "--update",
        dest="action",
        action="store_const",
        const=Action.UPDATE,
        help="Update the machine.",
    )
    g1.add_argument(
        "-c",
        "--cleanup",
        dest="action",
        action="store_const",
        const=Action.CLEANUP,
        help="Run cleanup tasks.",
    )
    g1.add_argument(
        "-m",
        "--maint-check",
        dest="action",
        action="store_const",
        const=Action.MAINT_CHECK,
        help="Check if any maintenance is due.",
    )

    g2 = parser.add_mutually_exclusive_group()
    g2.add_argument(
        "-D",
        "--days-since-last",
        dest="dsl",
        choices=["local", "remote"],
        help=(
            "Prints the number of days its been since the specified "
            "maintenance task was last performed. This option takes an "
            'argument indicating what machine(s) to check. "local" indicates '
            'the local machine and "remote" indicates all remote machines.'
        ),
    )
    g2.add_argument(
        "-P",
        "--pretend",
        dest="pretend",
        action="store_true",
        help="Prints the command list instead of executing it.",
    )

    args = parser.parse_args(argv[1:])
    kwargs = dict(args._get_kwargs())

    if args.action is None:
        parser.error(
            "Exactly one of the following options MUST be specified:"
            " [-u | -c | -m]"
        )

    if args.action == Action.MAINT_CHECK and args.max_days is None:
        parser.error(
            "The -M|--max-days option MUST be provided when -m|--maint-check"
            " is specified."
        )

    return Arguments(**kwargs)


def run(args: Arguments) -> int:
    signal.signal(signal.SIGINT, keyboard_interrupt_handler)
    signal.signal(signal.SIGQUIT, keyboard_interrupt_handler)

    cmd_list = []
    cmd_opts = []

    if args.action == Action.UPDATE:
        escript = "eupdate"
    elif args.action == Action.CLEANUP:
        escript = "ecleanup"
    elif args.action == Action.MAINT_CHECK:
        escript = "emaint_check"
        assert args.max_days is not None, (
            "Logic error in CLI argument parsing logic: The --maint-check"
            " option should require that the --max-days option also be"
            " specified."
        )
        cmd_opts.append(args.max_days)
    else:
        raise RuntimeError("No maintenance task specified.")

    cmd_list.append(escript)
    cmd_list.extend(cmd_opts)

    data_dir = xdg.init_full_dir("data")
    local_hostname = os.uname().nodename

    cmd_dir = "/{}/{}/{}".format(data_dir, local_hostname, escript)
    local_tsfile = Path("{}/timestamp".format(cmd_dir))

    if args.pretend:
        print(escript)
        sys.exit(0)
    elif args.dsl:
        process_dsl(args.dsl, local_tsfile, local_hostname, data_dir, escript)
        sys.exit(0)

    # Just used to force myself to use emanage. :)
    #
    # Requires that the secret.sh file be sourced into every script that could
    # be called here.
    secret = get_secret()
    cmd_list.extend([secret])

    fp_count = "{}/count".format(cmd_dir)
    append_count_to_cmd_list(fp_count, escript, cmd_list)

    try:
        sp.check_call(cmd_list)
    except sp.CalledProcessError as e:
        # The 'confirm' script will exit with return code of 1 if key other
        # than 'y' or 'n' (like 'x') is pressed.
        if e.returncode != 1:
            raise e
    else:
        write_timestamp(local_tsfile)

    return 0


def keyboard_interrupt_handler(
    signum: signal.Signals, frame: FrameType  # pylint: disable=unused-argument
) -> None:
    """Signal handler for keyboard shortcuts that terminate the program."""
    signame = {signal.SIGINT: "SIGINT", signal.SIGQUIT: "SIGQUIT"}[signum]

    print()
    imsg("{} signal detected. Terminating...".format(signame))
    sys.exit(128 + signum)


def process_dsl(
    dsl: str,
    local_tsfile: Path,
    local_hostname: str,
    data_dir: Path,
    escript: str,
) -> None:
    if dsl == "local":
        days = _days_since_last(local_tsfile)
        print(days)
    elif dsl == "remote":
        remote_hostnames = [
            H for H in os.listdir(data_dir) if H != local_hostname
        ]
        remote_ts_files = [
            Path("{}/{}/{}/timestamp".format(data_dir, H, escript))
            for H in remote_hostnames
        ]

        for H, fp in zip(remote_hostnames, remote_ts_files):
            days = _days_since_last(fp)
            print("{}:{}".format(H, days))


def _days_since_last(fp_timestamp: Path) -> int:
    try:
        date_string = open(fp_timestamp, "r").read().rstrip()
        last_clean = dt.datetime.strptime(date_string, TS_FMT)
        delta = dt.datetime.today() - last_clean
        days = delta.days
    except FileNotFoundError:
        days = 99999

    return days


def append_count_to_cmd_list(
    fp_count: str, escript: str, cmd_list: MutableSequence[str]
) -> None:
    if os.path.exists(fp_count):
        with open(fp_count, "r") as f:
            count = f.read().strip()

        if int(count) > 0:
            prompt = (
                ">>> Would you like to resume `{}` "
                "where you left off (y), "
                "redo the last command (r), or "
                "start a new session (n)?: ".format(escript)
            )
            choice = getch("\n".join(textwrap.wrap(prompt, 80)))

            if choice == "y":
                cmd_list.append(count)
            elif choice == "r":
                cmd_list.append(str(int(count) - 1))
            elif choice != "n":
                sys.exit(0)


def write_timestamp(fp: Path) -> None:
    """Writes Timestamp to a File"""
    dp = os.path.dirname(fp)
    if not os.path.exists(dp):
        os.makedirs(dp)

    with open(fp, "w") as f:
        now = dt.datetime.now()
        f.write(now.strftime(TS_FMT))


main = main_factory(parse_cli_args, run)
if __name__ == "__main__":
    main()
