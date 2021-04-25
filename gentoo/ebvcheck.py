"""Ebuild Version Check for Portage Overlay.

Uses app-portage/euscan to verify that ebuilds in the specified portage overlay
are up to date.
"""

import json
import os
import queue
import re
import string
from subprocess import PIPE, Popen
import sys
import threading
import time
from typing import Callable, Dict, List, NamedTuple, Optional, Sequence, Set

import bugyi
from bugyi import cli
from bugyi.core import catch
from loguru import logger as log
import numpy as np
import requests


KeyFunc = Callable[[str], float]
RepologyProject = List[Dict[str, str]]
RepologyProjectGroup = Dict[str, RepologyProject]


REPOLOGY = "https://repology.org/api/v1/{}".format
REPOLOGY_PROJECT_MAP = {
    "dev-util/ix": "ix",
    "dev-ruby/xdg": "ruby:xdg",
    "dev-python/tldr-python-client": "tldr",
    "dev-python/python-stdlib-list": "python:stdlib-list",
}
REPOLOGY_REPO_MAP = {"dev-python/tldr-python-client": "arch"}


class POpenError(Exception):
    """Raised when a Popen(...) subprocess returns a nonzero exit code."""


def popen_error(
    ps: Popen, stdout: Optional[bytes], stderr: Optional[bytes]
) -> POpenError:
    assert ps.returncode != 0

    out = None if stdout is None else stdout.decode().strip()
    err = None if stderr is None else stderr.decode().strip()

    if isinstance(ps.args, str):
        cmd = ps.args
    else:
        cmd = ' '.join(ps.args)  # type: ignore

    return POpenError(
        f"The following subprocess command failed:\n\t{cmd!r}"
        f"\n\nReturn Code: {ps.returncode}"
        f"\n\n===== STDOUT =====\n{out}"
        f"\n\n===== STDERR =====\n{err}"
    )


class PkgContainer:
    """Thread-Safe Set-Like Container for Portage Packages."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.packages: Set[str] = set()
        self.current_id = 0

    def add(self, pkg: str) -> int:
        with self.lock:
            if pkg in self.packages:
                raise ValueError

            self.packages.add(pkg)
            self.current_id += 1
            return self.current_id

    def remove(self, pkg: str) -> None:
        with self.lock:
            try:
                self.packages.remove(pkg)
            except KeyError:
                pass


class MessageManager:
    """Prints package statuses to STDOUT in a thread-safe manner.

    Used to make sure that ebuild status messages are reported in alphabetical
    order instead of at random. Also prevents race condition. E.g. status
    messages from two different packages could try to print to STDOUT at the
    same exact time, resulting in mangled text.
    """

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.last_id = 0
        self.pending: Dict[int, str] = {}

    def print(self, msg: str, id_number: int) -> None:
        with self.lock:
            if id_number == self.last_id + 1:
                self.last_id += 1
                self.release(msg)
                self.check_pending()
            else:
                log.debug(
                    'Freezing package ID: #{} (last_id == #{})',
                    id_number,
                    self.last_id,
                )
                self.pending[id_number] = msg

    def check_pending(self) -> None:
        next_id = self.last_id + 1
        if next_id in self.pending:
            msg = self.pending.pop(next_id)

            self.last_id += 1
            self.release(msg)

            self.check_pending()

    def release(self, msg: str) -> None:
        if msg != '':
            print(msg)
            status = 'checked'
        else:
            status = 'skipped'

        log.debug('Releasing package ID: {} ({})', self.last_id, status)

    def noop(self, id_number: int) -> None:
        with self.lock:
            self.pending[id_number] = ''
            self.check_pending()


pkg_container = PkgContainer()
message_manager = MessageManager()
pkg_queue: 'queue.Queue[str]' = queue.Queue()
threads: List[threading.Thread] = []


@catch  # noqa: C901
def main(argv: Sequence[str] = None) -> None:
    if argv is None:
        argv = sys.argv

    args = parse_cli_args(argv)

    bugyi.logging.configure(__file__, debug=args.debug, verbose=args.verbose)
    if not args.color:
        for attr in dir(bugyi.colorize):
            if not attr.startswith('_'):
                setattr(bugyi.colorize, attr, lambda x: x)

    all_files = get_all_files(args.overlay_dir)
    all_ebuild_paths = [f for f in all_files if f.endswith('.ebuild')]

    # ebuilds in this list are of the form 'CATEGORY/PACKAGE-VERSION.ebuild'
    all_ebuilds = [
        '/'.join([ebuild_path_list[-3], ebuild_path_list[-1]])
        for ebuild_path_list in [
            ebpath.split('/') for ebpath in all_ebuild_paths
        ]
    ]
    log.trace('all_ebuilds: {}', all_ebuilds)

    msg_fmt = (
        'Ebuild Version Check will be run for the following overlay: {}\n'
    )
    if args.verbose:
        print(msg_fmt.format(os.path.basename(args.overlay_dir)))

    pkg_queue.maxsize = args.max_thread_count
    for ebuild in sorted(all_ebuilds):
        pkg = re.sub(r'-([0-9])+\..*ebuild$', '', ebuild)

        try:
            id_number = pkg_container.add(pkg)
        except ValueError:
            continue

        log.debug('ID: {}', id_number)

        if args.max_thread_count > 1:
            t = threading.Thread(
                target=check_pkg,
                args=(pkg, id_number, args.live, args.offline),
                daemon=True,
            )
            t.start()
            threads.append(t)
        else:
            check_pkg(pkg, id_number, args.live, args.offline)

    if args.max_thread_count > 1:
        pkg_queue.join()

    if args.verbose:
        print(
            '\nFinished. {} packages checked.'.format(
                len(pkg_container.packages)
            )
        )


class Arguments(NamedTuple):
    debug: bool
    verbose: bool
    overlay_dir: str
    max_thread_count: int
    color: bool
    live: bool
    offline: bool


def parse_cli_args(argv: Sequence[str]) -> Arguments:
    parser = cli.ArgumentParser()
    parser.add_argument(
        '-D',
        dest='overlay_dir',
        default='/var/db/repos/bbugyi',
        help=(
            'Location (directory path) of the portage overlay. Defaults to'
            ' %(default)s.'
        ),
    )
    parser.add_argument(
        '-T',
        '--max-thread-count',
        type=int,
        default=3,
        help='Max number of threads to start. Defaults to %(default)s.',
    )
    parser.add_argument(
        '--color',
        choices=('y', 'n'),
        default="y",
        help='Colorize output? Defaults to %(default)r.',
    )
    parser.add_argument(
        '--live-builds',
        dest='live',
        action='store',
        choices=('y', 'n'),
        default="n",
        help=(
            'Print status for live ebuilds (ebuilds with version 9999).'
            ' Defaults to %(default)r.'
        ),
    )
    parser.add_argument(
        '--offline',
        choices=('y', 'n'),
        default="n",
        help=(
            'Print status for packages that are not installed on this machine.'
            ' Defaults to %(default)r.'
        ),
    )

    args = parser.parse_args(argv[1:])

    kwargs = dict(args._get_kwargs())
    kwargs["color"] = args.color == "y"
    kwargs["live"] = args.live == "y"
    kwargs["offline"] = args.offline == "y"

    return Arguments(**kwargs)


def check_pkg(  # noqa: C901
    pkg: str,
    id_number: int,
    show_live_pkgs: bool = False,
    show_offline_pkgs: bool = False,
) -> None:
    log.trace('pkg: {}', pkg)
    pkg_queue.put(pkg)

    try:
        cmd_fmt = (
            "eix --nocolor --format '<installedversions:NAMEVERSION>' {} |"
            " head -n 1"
        )
        cmd = cmd_fmt.format(pkg)
        ps = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        (stdout, stderr) = ps.communicate()

        if ps.returncode != 0:
            raise popen_error(ps, stdout, stderr)

        out = stdout.decode().strip()
        msg_fmt = '{}:: {}'
        if not re.match(
            r'[A-z\-\d]+/[A-z\-\d]+-[\d\.]+(_[A-z_]+\d*)?(-r\d*)?$', out
        ):
            if show_offline_pkgs:
                message_manager.print(
                    msg_fmt.format(
                        pkg, bugyi.colorize.magenta('NOT INSTALLED')
                    ),
                    id_number,
                )
            else:
                pkg_container.remove(pkg)
                message_manager.noop(id_number)
            return

        version = out.split('-')[-1]
        if version == '9999':
            if show_live_pkgs:
                message_manager.print(
                    msg_fmt.format(pkg, bugyi.colorize.blue('LIVE BUILD')),
                    id_number,
                )
            else:
                pkg_container.remove(pkg)
                message_manager.noop(id_number)
            return

        latest_version_A = latest_version_B = get_latest_version(pkg)
        if latest_version_A is None:
            log.debug('{} UNKNOWN (#{}).'.format(pkg, id_number))
            message_manager.print(
                msg_fmt.format(pkg, bugyi.colorize.yellow('UNKNOWN')),
                id_number,
            )
        else:
            if latest_version_A != version:
                latest_version_B = get_latest_version(pkg, key=fuzzy_key(pkg))

            if version not in [latest_version_A, latest_version_B]:
                log.debug('{} FAILED (#{}).'.format(pkg, id_number))
                if latest_version_A == latest_version_B:
                    new_version = latest_version_A
                else:
                    new_version = f"{latest_version_A} OR {latest_version_B}"

                fail_msg = msg_fmt.format(
                    pkg,
                    bugyi.colorize.red(
                        'FAILED  (New Version: {})'.format(new_version)
                    ),
                )

                message_manager.print(fail_msg, id_number)
            else:
                log.debug('{} PASSED (#{}).'.format(pkg, id_number))
                message_manager.print(
                    msg_fmt.format(pkg, bugyi.colorize.green('PASSED')),
                    id_number,
                )
    finally:
        pkg_queue.get()
        pkg_queue.task_done()


def get_all_files(directory: str) -> List[str]:
    F = []
    for root, _dirs, files in os.walk(directory):
        for name in files:
            F.append(os.path.join(root, name))
    return F


def get_latest_version(
    full_pkg: str, key: KeyFunc = len, disable_cache: bool = False,
) -> Optional[str]:
    if "/" in full_pkg:
        (_category, pkg) = full_pkg.split("/", 1)
    else:
        pkg = full_pkg

    pkg_attr = full_pkg.replace("-", "_").replace("/", "__")

    self = get_latest_version
    if not disable_cache and hasattr(self, pkg_attr):
        data = getattr(self, pkg_attr)
    else:
        if full_pkg in REPOLOGY_PROJECT_MAP:
            project_name = REPOLOGY_PROJECT_MAP[full_pkg]
            data = {project_name: repology_project(project_name)}
        else:
            data = all_repology_projects(pkg)

    if not hasattr(self, pkg_attr):
        setattr(self, pkg_attr, data)

    result = None
    for pkg_key in sorted(data, key=key):
        if full_pkg in REPOLOGY_REPO_MAP:
            repo = REPOLOGY_REPO_MAP[full_pkg]
            for D in data[pkg_key]:
                if D['repo'] == repo:
                    result = D['version']
                    break

            if result:
                break

        version_set = {
            D["version"]
            for D in data[pkg_key]
            if "." in D["version"]
            and set(D["version"]).issubset(set(string.digits + "."))
        }
        result = max(version_set)
        break

    return result


def repology_project(name: str) -> RepologyProject:
    resp = requests.get(REPOLOGY(f"project/{name}"))
    result = json.loads(resp.text)
    return result


def all_repology_projects(search: str) -> RepologyProjectGroup:
    result = repology_project_group(search)

    tmp = result
    while len(tmp) == 200:
        tmp = repology_project_group(search, name=list(tmp.keys())[-1])
        result.update(tmp)

    return result


def repology_project_group(
    search: str, name: str = ""
) -> RepologyProjectGroup:
    exc = None
    timeout = 1
    for _ in range(5):
        try:
            resp = requests.get(
                REPOLOGY(f"projects/{name}"),
                params={"search": search},
                timeout=timeout,
            )
            result = json.loads(resp.text)
            break
        except requests.exceptions.ReadTimeout as e:
            exc = e
            timeout *= 2
            time.sleep(1)
    else:
        assert exc
        raise exc

    return result


def fuzzy_key(pkg: str) -> KeyFunc:
    def _fuzzy_key(P: str) -> float:
        return -fuzzy_match(pkg, P)

    return _fuzzy_key


def fuzzy_match(S: str, T: str) -> float:
    # Initialize matrix of zeros
    rows = len(S) + 1
    cols = len(T) + 1
    distance = np.zeros((rows, cols), dtype=int)

    # Populate matrix of zeros with the indeces of each character of both
    # strings
    for i in range(1, rows):
        for k in range(1, cols):
            distance[i][0] = i
            distance[0][k] = k

    # Iterate over the matrix to compute the cost of deletions,insertions
    # and/or substitutions
    for col in range(1, cols):
        for row in range(1, rows):
            if S[row - 1] == T[col - 1]:
                # If the characters are the same in the two strings in a given
                # position [i,j] then the cost is 0
                cost = 0
            else:
                # In order to align the results with those of the Python
                # Levenshtein package, if we choose to calculate the ratio the
                # cost of a substitution is 2. If we calculate just distance,
                # then the cost of a substitution is 1.
                cost = 2
            distance[row][col] = min(
                distance[row - 1][col] + 1,  # Cost of deletions
                distance[row][col - 1] + 1,  # Cost of insertions
                distance[row - 1][col - 1] + cost,
            )  # Cost of substitutions

    # Computation of the Levenshtein Distance Ratio
    ratio = ((len(S) + len(T)) - distance[row][col]) / (len(S) + len(T))
    return ratio


if __name__ == "__main__":
    main()
