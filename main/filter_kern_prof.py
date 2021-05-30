"""
Filters output of kernprof
"""

import fileinput
import re
import sys
from typing import List, NamedTuple, Sequence

from bugyi import cli
from bugyi.core import main_factory
from loguru import logger as log  # pylint: disable=unused-import


class Arguments(NamedTuple):
    debug: bool
    verbose: bool


def parse_cli_args(argv: Sequence[str]) -> Arguments:
    parser = cli.ArgumentParser()

    args = parser.parse_args(argv[1:])

    kwargs = dict(args._get_kwargs())
    return Arguments(**kwargs)


def _function_line_list_key(function_lines: Sequence[str]) -> float:
    match = re.match(r"(?:# )?Total time: ([0-9\.]+) s", function_lines[0])
    if match:
        return -float(match.group(1))
    else:
        raise RuntimeError(f"Bad first line:  {function_lines[0]}")


def run(_args: Arguments) -> int:
    in_uncalled_function = found_first_line = False
    new_lines: List[str] = []
    function_line_lists: List[List[str]] = []
    line_list = new_lines
    for line in fileinput.input():
        if not found_first_line and not line.strip().startswith(
            "Wrote profile results to"
        ):
            continue

        found_first_line = True

        if line.strip().startswith("Total time:"):
            in_uncalled_function = bool(line.strip() == "Total time: 0 s")
            function_line_lists.append([])
            line_list = function_line_lists[-1]

        line = line.replace("Line #", "Line  ")
        if in_uncalled_function:
            line = f"# {line}"

        line_list.append(line)

    for function_lines in sorted(
        function_line_lists, key=_function_line_list_key
    ):
        new_lines.extend(function_lines)

    new_lines.append("# vim: set ft=python:\n")
    for line in new_lines:
        print(line, end="")

    return 0


main = main_factory(parse_cli_args, run)
if __name__ == "__main__":
    sys.exit(main())
