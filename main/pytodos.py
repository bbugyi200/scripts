"""Parse TODO comments in python files."""

import fileinput
import re
import sys
from typing import NamedTuple, Sequence

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


def run(_args: Arguments) -> int:
    pyfile_matched = False
    for pyfile in fileinput.input():
        pyfile = pyfile.strip()

        todos_found = 0
        line_num_stack = [-1]

        for i, line in enumerate(open(pyfile)):
            match = re.match(
                r"^[ ]*..?[ ]TODO\(b?bugyi[0-9]*\):[ ](.*)$", line
            )
            if match:
                todo = match.groups()[0]

                todos_found += 1
                if todos_found == 1:
                    if pyfile_matched:
                        print()
                    else:
                        pyfile_matched = True

                    print(f"----- {pyfile}")

                line_num = i + 1
                if line_num_stack[-1] == line_num - 1:
                    prefix = " " * len(str(line_num_stack[0]))
                else:
                    prefix = str(line_num)
                    line_num_stack.clear()

                line_num_stack.append(line_num)

                print(f"{prefix}: {todo}")

    return 0


main = main_factory(parse_cli_args, run)
if __name__ == "__main__":
    sys.exit(main())
