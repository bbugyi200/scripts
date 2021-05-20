"""
Freeze select files (i.e. save their contents and their relative directories).

These files can then later be "unfrozen" (i.e. copied back to their relative
directories).
"""

import argparse
from dataclasses import dataclass
from functools import partial
from pathlib import Path
import shutil
import sys
from typing import Iterable, Sequence

from bugyi import cli
from bugyi.core import main_factory
from loguru import logger as log


@dataclass(frozen=True)
class Arguments(cli.Arguments):
    freeze: bool
    unfreeze: bool
    icedir: Path
    target_files: Iterable[Path]


def parse_cli_args(argv: Sequence[str]) -> Arguments:
    parser = cli.ArgumentParser()
    g1 = parser.add_mutually_exclusive_group()
    g1.add_argument("--freeze", action="store_true", help="Freeze files.")
    g1.add_argument("--unfreeze", action="store_true", help="Un-Freeze files.")
    parser.add_argument(
        "icedir",
        type=Path,
        help="The directory that frozen files are saved to.",
    )
    parser.add_argument(
        "target_files",
        nargs=argparse.REMAINDER,
        type=Path,
        help="The files you want to freeze.",
    )

    args = parser.parse_args(argv[1:])
    kwargs = dict(args._get_kwargs())

    if not kwargs["freeze"] and not kwargs["unfreeze"]:
        raise parser.error(
            "Exactly one of the options --freeze or --unfreeze MUST be"
            " specified."
        )

    return Arguments(**kwargs)


def run(args: Arguments) -> int:
    if args.freeze:
        icefunc = partial(freeze, args.icedir, args.target_files)
    else:
        assert args.unfreeze
        icefunc = partial(unfreeze, args.icedir)

    return icefunc()


def freeze(icedir: Path, file_paths: Iterable[Path]) -> int:
    for path in file_paths:
        if path.is_absolute():
            log.error("Absolute paths are not allowed: {}", path)
            return 1

    shutil.rmtree(icedir, ignore_errors=True)

    for path in file_paths:
        ice_parent = icedir / path.parent
        ice_parent.mkdir(parents=True, exist_ok=True)
        ice_path = ice_parent / path.name

        _shutil_copy(path, ice_path)

    return 0


def unfreeze(icedir: Path) -> int:
    for path in icedir.rglob("*"):
        if path.is_file():
            src = path

            dest = Path(".") / path.relative_to(icedir)
            dest.parent.mkdir(parents=True, exist_ok=True)

            _shutil_copy(src, dest.absolute())
    return 0


def _shutil_copy(src: Path, dest: Path) -> None:
    log.info("Copying {} -> {}...", src, dest)
    shutil.copy(src, dest)


main = main_factory(parse_cli_args, run)
if __name__ == "__main__":
    sys.exit(main())
