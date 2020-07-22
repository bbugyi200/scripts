"""
Zathura Helper Script. Used to Search for and then Open Documents in Zathura.
"""

import os
from pathlib import Path
import re
import signal
import socket
import subprocess as sp
import sys
import time
from typing import Iterable, List, NamedTuple, Sequence

import gutils
from loguru import logger as log


xdg_data_dir = gutils.xdg.init('data')
CACHE_FILE = xdg_data_dir / 'recently_opened_docs'
FIND_CACHE_FILE = xdg_data_dir / 'all_docs'


@gutils.catch
def main(argv: Sequence[str] = None) -> int:
    if argv is None:
        argv = sys.argv

    args = parse_cli_args(argv)

    gutils.logging.configure(__file__, debug=args.debug, verbose=args.verbose)

    return run(args)


class Arguments(NamedTuple):
    verbose: bool
    debug: bool
    generate_cache: bool
    quiet: bool
    overwrite: bool
    refresh: bool


def parse_cli_args(argv: Sequence[str]) -> Arguments:
    parser = gutils.ArgumentParser()
    parser.add_argument(
        '-C',
        dest='generate_cache',
        action='store_true',
        help='Re-generate the document cache (aka the "find command cache").',
    )
    parser.add_argument(
        '-q',
        '--quiet',
        dest='quiet',
        action='store_true',
        help=(
            'Do not prompt the user to choose a document. Use with -C to '
            'silently re-generate the document cache (aka the "find command  '
            'cache").'
        ),
    )
    parser.add_argument(
        '-x',
        dest='overwrite',
        action='store_true',
        help='Close current Zathura instance before opening new one.',
    )
    parser.add_argument(
        '-R',
        dest='refresh',
        action='store_true',
        help='Closes current Zathura instance and reopens same document.',
    )

    args = parser.parse_args(argv[1:])
    kwargs = dict(args._get_kwargs())

    return Arguments(**kwargs)


def run(args: Arguments) -> int:
    doc_pttrn = r'.*\.\(pdf\|epub\|djvu\|ps\|okular\)'

    all_docs = None
    if args.generate_cache or not os.path.isfile(FIND_CACHE_FILE):
        directory_list = ['/home/bryan/Sync', '/home/bryan/projects']
        if socket.gethostname() == 'athena':
            directory_list.append(
                '/media/bryan/hercules/archive/home/bryan/Sync'
            )

        cmd_list = ['find']
        cmd_list.extend(directory_list)
        cmd_list.extend(
            ['-path', '/home/bryan/Sync/.dropbox.cache', '-prune', '-o']
        )
        cmd_list.extend(['-regex', doc_pttrn])

        out = sp.check_output(cmd_list)
        all_docs = out.decode().strip()

        with open(FIND_CACHE_FILE, 'w') as f:
            f.write(all_docs)

    if args.quiet:
        sys.exit(0)

    if all_docs is None:
        out = sp.check_output(['cat', FIND_CACHE_FILE])
        all_docs = out.decode().strip()

    # Append any docs found in the Downloads directory.
    out = sp.check_output(
        ['find', '/home/bryan/Downloads', '-regex', doc_pttrn]
    )
    all_docs = all_docs + '\n' + out.decode().strip()
    log.trace('----- Downloads -----\n{}', out.decode().strip())

    try:
        cmd = (
            'wmctrl -lx | grep -E "zathura|okular" | tr -s " " | cut -d\' \''
            ' -f5- | grep -o ".*\\.\\(pdf\\|djvu\\|epub\\|okular\\)"'
        )
        decoded = gutils.shell(cmd)

        open_docs = [Path(x) for x in decoded.split('\n')]
        log.debug('Open Docs: {}'.format(open_docs))
    except sp.CalledProcessError:
        open_docs = []
        log.debug('No documents are currently open in zathura.')

    with open(CACHE_FILE, 'r') as f:
        cached_docs = [Path(x.strip()) for x in f.readlines()]

    ordered_docs = promote_cached_docs(
        [Path(doc) for doc in all_docs.split('\n')], cached_docs
    )

    if open_docs:
        ordered_docs = demote_open_docs(ordered_docs, open_docs)

    pretty_docs = [
        re.sub('^/home/bryan/Sync/var/books/', '', str(doc))
        for doc in ordered_docs
    ]

    if args.refresh:
        doc = ordered_docs[-1]
    else:
        ps = sp.Popen(
            ['printf', '{}'.format('\n'.join(pretty_docs))], stdout=sp.PIPE
        )
        out = sp.check_output(
            ['rofi', '-p', 'Document', '-m', '-4', '-dmenu', '-i'],
            stdin=ps.stdout,
        )
        ps.wait()

        output = out.decode().strip()

        if output.startswith('/'):
            doc = Path(output)
        else:
            doc = Path('/home/bryan/Sync/var/books/{}'.format(output))

    add_to_cache(doc, [] if args.overwrite else open_docs)

    active_window_class = gutils.shell('active_window_class')
    replace = args.overwrite or args.refresh
    if active_window_class == 'Zathura':
        open_document('zathura', doc, replace=replace)
    elif active_window_class == 'okular':
        open_document('okular', doc, opts=['--unique'], replace=replace)
    else:
        open_document('okular', doc, replace=replace)

    time.sleep(0.2)
    sp.check_call(['fullscreen'])


def open_document(
    cmd: str, doc: Path, *, opts: Sequence[str] = None, replace: bool = False
) -> None:
    if opts is None:
        opts = []

    if replace:
        pid = int(gutils.shell('active_window_pid'))
        log.debug('Killing Document Instance: {}'.format(pid))
        os.kill(pid, signal.SIGTERM)

    cmd_list = [cmd]
    cmd_list.extend(opts)
    cmd_list.append(str(doc))

    log.debug('Opening {} in {}...'.format(doc, cmd))
    sp.Popen(cmd_list, stdout=sp.DEVNULL, stderr=sp.STDOUT)


def promote_cached_docs(
    docs: Sequence[Path], cached_docs: Sequence[Path]
) -> List[Path]:
    """Docs in Cache File are Brought to the Top of the List of Options"""
    D = docs[:]
    for c in list(reversed(cached_docs)):
        if c in D:
            D.remove(c)
            D.insert(0, c)
    return D


def demote_open_docs(
    docs: Sequence[Path], open_docs: Iterable[Path]
) -> List[Path]:
    """Open Docs are Moved to the Bottom of the List of Options"""
    D = docs[:]
    E = []
    for odoc in open_docs:
        for doc in docs:
            if str(odoc) in str(doc):
                try:
                    D.remove(doc)
                    E.append(doc)
                except ValueError:
                    # Protects against multiple attempts to remove the same doc
                    # which happens when the same doc is opened up in multiple
                    # different instances.
                    pass
    D.extend(E)
    return D


def add_to_cache(doc: Path, open_docs: Sequence[Path]) -> None:
    """Adds/moves doc to the Top of the Cache File"""
    log.debug('Adding {} to cache file...'.format(doc))
    if os.path.isfile(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cached_docs = f.read().strip().split('\n')

        if doc in cached_docs:
            cached_docs.remove(str(doc))

        idx = 0
        for cdoc in cached_docs:
            if any(str(odoc) in str(cdoc) for odoc in open_docs):
                idx += 1
            else:
                break

        cached_docs.insert(idx, str(doc))

        with open(CACHE_FILE, 'w') as f:
            f.write('\n'.join(cached_docs[:100]))
    else:
        with open(CACHE_FILE, 'w') as f:
            f.write(str(doc))


if __name__ == "__main__":
    main()
