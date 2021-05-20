"""Add a New Function / Alias to your bashrc / zshrc in Alphabetical Order"""

from dataclasses import dataclass
import os
import re
import subprocess as sp
import sys
from typing import List, Optional, Sequence

from bugyi import cli
from bugyi.core import main_factory
from bugyi.io import emsg
from loguru import logger as log


scriptname = os.path.basename(os.path.realpath(__file__))


@dataclass(frozen=True)
class Arguments(cli.Arguments):
    alias: bool
    marker: str
    name: str
    file_list: List[str]


def parse_cli_args(argv: Sequence[str]) -> Arguments:
    parser = cli.ArgumentParser()

    parser.add_argument(
        'name', metavar='NAME', help='Name of the new function / alias.'
    )
    parser.add_argument(
        '-a',
        '--alias',
        action='store_true',
        help='Define alias instead of function.',
    )
    parser.add_argument(
        '-m',
        '--marker',
        default='DEFAULT',
        help='Marks the start line. Defaults to %(default)r.',
    )
    parser.add_argument(
        "-F",
        "--bash-file",
        action="append",
        dest='file_list',
        metavar='FILE',
        help=(
            'File to search when determining where to add new alias'
            ' definition. This option can be given multiple times.'
        ),
    )

    args = parser.parse_args(argv[1:])
    kwargs = dict(args._get_kwargs())

    return Arguments(**kwargs)


def run(args: Arguments) -> int:
    marker = str.upper(args.marker)
    full_marker = '# def marker: {}'.format(marker)

    if args.alias:
        new_def = f"alias {args.name}=''\n"
        column_number = 9 + len(args.name)
    else:
        new_def = f"{args.name}() {{ :; }}\n"
        column_number = 7 + len(args.name)

    m_filename = None
    m_new_lines = []
    line_number: Optional[int] = None
    marker_idx: Optional[int] = None
    for filename in args.file_list:
        new_lines: List[str] = []
        marker_lines: List[str] = []
        line_list = new_lines
        found_marker = False

        for (i, line) in enumerate(open(filename, 'r')):
            line_list.append(line)

            if found_marker:
                if not line.strip():
                    line_list.pop()
                    line_list = new_lines
                    line_list.append(line)
            elif line.strip() == full_marker:
                found_marker = True
                m_filename = filename
                marker_idx = i + 1
                line_list = marker_lines

            tmp_line = line.replace('alias ', '')
            line_name = re.split(r'[=(]', tmp_line)[0]
            log.trace('line_name => {}', repr(line_name))

            if args.name == line_name.strip():
                emsg('{} is already defined.'.format(args.name))
                sp.check_call(['wim', '-a', args.name])
                return 0

        if found_marker:
            marker_lines.append(new_def)
            marker_lines = sorted(
                marker_lines,
                key=lambda D: D.replace("alias ", "").lstrip("_").lower(),
            )

            assert marker_idx
            new_lines[marker_idx:marker_idx] = marker_lines
            m_new_lines = new_lines

            new_def_idx = marker_lines.index(new_def)
            line_number = marker_idx + new_def_idx + 1

    if m_filename is None:
        raise RuntimeError(
            "No alias/function section could be found with the following"
            f" marker:  {marker}"
        )

    with open(m_filename, 'w') as f:
        f.writelines(m_new_lines)

    cursor_call = f"call cursor({line_number}, {column_number})"
    cmd_list = ['vim', '+startinsert', '-c', cursor_call, m_filename]
    log.trace('cmd_list => {}', repr(cmd_list))

    sp.check_call(cmd_list)

    return 0


main = main_factory(parse_cli_args, run)
if __name__ == "__main__":
    sys.exit(main())
