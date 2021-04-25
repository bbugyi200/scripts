"""
Installs provided python packages if they do not already exist.
"""

import os
from shutil import which
import subprocess as sp
import sys
from typing import NamedTuple, Optional, Sequence

import bugyi
from bugyi import cli
from bugyi.core import catch


@catch
def main(argv: Sequence[str] = None) -> int:
    if argv is None:
        argv = sys.argv

    args = parse_cli_args(argv)
    bugyi.logging.configure(__file__, debug=args.debug, verbose=args.verbose)

    return run(args)


class Arguments(NamedTuple):
    debug: bool
    verbose: bool
    python_packages: Sequence[str]
    python_versions: Sequence[float]
    one_at_a_time: bool


def parse_cli_args(argv: Sequence[str]) -> Arguments:
    parser = cli.ArgumentParser()
    parser.add_argument(
        "-V",
        "--python-version",
        action="append",
        dest="python_versions",
        metavar="MAJOR.MINOR",
        type=float,
        help=(
            "A valid python version number (e.g. 2.7, 3.6, 3.7, etc....). This"
            " option can be provided more than once."
        ),
    )
    parser.add_argument(
        "-1",
        "--one-at-a-time",
        action="store_true",
        help="Install each Python pacakge individually.",
    )
    parser.add_argument(
        "python_packages",
        metavar="PYPACK",
        nargs="+",
        type=str,
        help="Python packages to install (if not already installed).",
    )

    args = parser.parse_args(argv[1:])

    if args.python_versions is None:
        parser.error(
            "At least one python version number must be provided (using the -v"
            " option)."
        )

    kwargs = dict(args._get_kwargs())
    return Arguments(**kwargs)


def run(args: Arguments) -> int:
    is_first_pyver = True
    for pyver in args.python_versions:
        if not _python_version_exists(pyver):
            raise SystemExit(f"[ERROR]: python{pyver} is not installed.")

        if is_first_pyver:
            is_first_pyver = False
        else:
            print()

        print(f"===== Python {pyver} =====")
        _install_pypacks(
            args.python_packages, pyver, one_at_a_time=args.one_at_a_time
        )

    return 0


def _install_pypacks(
    pypacks: Sequence[str], pyver: float, one_at_a_time: bool = True
) -> None:
    all_pypacks = [] if pyver < 3.0 else ["pip"]
    all_pypacks.extend(pypacks)

    python = f"python{pyver}"
    pip_install_cmd = [python, "-m", "pip", "install", "--user"]
    if pyver >= 3.0:
        pip_install_cmd.append("-U")

    pypacks_installed = 0
    for pypack in all_pypacks:
        if not one_at_a_time and not pypack.startswith("/"):
            continue

        pypacks_installed += 1
        print(
            f"----- Upgrading {pypack}"
            f" ({pypacks_installed}/{len(all_pypacks)})..."
        )

        if pypack.startswith("/"):
            cwd: Optional[str] = pypack
            os.system("rm -rf *.egg-info")
            pip_args = ["-e", "."]
        else:
            cwd = None
            pip_args = [pypack]

        pip_cmd_list = list(pip_install_cmd)
        pip_cmd_list.extend(pip_args)
        ps = sp.Popen(pip_cmd_list, cwd=cwd)
        ps.communicate()

    if one_at_a_time:
        return

    normal_pypacks = [
        pypack for pypack in all_pypacks if not pypack.startswith("/")
    ]
    if pypacks_installed > 0:
        print(f"----- Upgrading Remaining {len(normal_pypacks)} Packages")

    pip_cmd_list = list(pip_install_cmd)
    pip_cmd_list.extend(normal_pypacks)
    ps = sp.Popen(pip_cmd_list)
    ps.communicate()


def _python_version_exists(pyver: float) -> bool:
    if which(f"python{pyver}") is None:
        return False
    return True


if __name__ == "__main__":
    sys.exit(main())
