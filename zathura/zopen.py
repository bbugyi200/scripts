"""
Zathura helper script. Used to search for and then open documents in Zathura.
"""

from dataclasses import dataclass
import os
from pathlib import Path
import re
import signal
import socket
import subprocess as sp
import sys
import time
from typing import Iterable, List, Optional, Sequence, Union

from bugyi import cli, xdg
from bugyi.core import main_factory, shell
from bugyi.errors import BErr, BResult
from bugyi.result import Err, Ok
from loguru import logger as log


PathLike = Union[str, Path]

_XDG_DATA_DIR = xdg.init_full_dir("data")
ALL_DOCS_CACHE_FILE = _XDG_DATA_DIR / "all_docs"
BOOKS_DIR = "/home/bryan/Sync/var/books"
MAX_MOST_RECENT_DOCS = 100
MOST_RECENT_CACHE_FILE = _XDG_DATA_DIR / "recently_opened_docs"

_DOC_FILE_EXTS = ("pdf", "epub", "djvu", "ps", "okular")
_DOC_FILE_EXT_GROUP = r"\({}\)".format(r"\|".join(_DOC_FILE_EXTS))
DOC_PTTRN = rf".*\.{_DOC_FILE_EXT_GROUP}"


@dataclass(frozen=True)
class Arguments(cli.Arguments):
    generate_cache: bool
    quiet: bool
    overwrite: bool
    refresh: bool


def parse_cli_args(argv: Sequence[str]) -> Arguments:
    parser = cli.ArgumentParser()
    parser.add_argument(
        "-C",
        "--generate-cache",
        action="store_true",
        help="Re-generate the document cache.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        dest="quiet",
        action="store_true",
        help=(
            "Do not prompt the user to choose a document. Use with -C to "
            "silently re-generate the document cache."
        ),
    )
    parser.add_argument(
        "-x",
        "--overwrite",
        action="store_true",
        help="Close current Zathura instance before opening new one.",
    )
    parser.add_argument(
        "-R",
        "--refresh",
        action="store_true",
        help="Closes current Zathura instance and reopens same document.",
    )

    args = parser.parse_args(argv[1:])

    kwargs = dict(args._get_kwargs())
    kwargs["generate_cache"] = (
        kwargs["generate_cache"] or not Path(ALL_DOCS_CACHE_FILE).is_file()
    )

    return Arguments(**kwargs)


def run(args: Arguments) -> int:
    all_docs = get_all_docs(use_cache=not args.generate_cache)

    if args.generate_cache:
        with open(ALL_DOCS_CACHE_FILE, "w") as f:
            f.writelines([str(adoc).rstrip() + "\n" for adoc in all_docs])

    if args.quiet:
        return 0

    mr_cache_path = Path(MOST_RECENT_CACHE_FILE)
    mr_cache_path.touch()
    with open(mr_cache_path, "r") as f:
        most_recent_docs = [Path(x.strip()) for x in f.readlines()]

    ordered_docs = promote_most_recent_docs(all_docs, most_recent_docs)

    open_docs = get_open_docs()
    if open_docs:
        ordered_docs = demote_open_docs(ordered_docs, open_docs)

    pretty_docs = [
        Path(re.sub(f"^{BOOKS_DIR}/", "", str(doc))) for doc in ordered_docs
    ]

    doc: Optional[PathLike]
    if args.refresh:
        # We assume that this should be the current (i.e. focused) doc, but it
        # isn't always. With that said, this almost always works.
        doc = ordered_docs[-1]
    else:
        doc_r = choose_doc_to_open(pretty_docs)
        if isinstance(doc_r, Err):
            e = doc_r.err()
            log.error(
                "An error occurred while the user was choosing a doc to"
                " open:\n{}",
                e.report(),
            )
            return 1

        doc = doc_r.ok()

    replace = args.overwrite or args.refresh
    open_document(doc, replace=replace)

    # We sleep for a second here so the open docs list has time to be updated
    # properly. When the -x or -R option is used, for example.
    if replace:
        time.sleep(1)
        open_docs = get_open_docs()

    add_to_mr_cache(most_recent_docs, doc, open_docs)

    return 0


def get_all_docs(*, use_cache: bool) -> List[Path]:
    if use_cache:
        assert Path(ALL_DOCS_CACHE_FILE).is_file()
        out = sp.check_output(["cat", ALL_DOCS_CACHE_FILE])
        all_docs_string = out.decode().strip()
    else:
        directory_list = ["/home/bryan/Sync/var/books", "/home/bryan/projects"]
        if socket.gethostname() == "athena":
            directory_list.append(
                "/mnt/hercules/archive/home/bryan/Sync/var/books"
            )

        cmd_list = ["find"]
        cmd_list.extend(directory_list)
        cmd_list.extend(
            ["-path", "/home/bryan/Sync/.dropbox.cache", "-prune", "-o"]
        )
        cmd_list.extend(["-regex", DOC_PTTRN])

        out = sp.check_output(cmd_list)
        all_docs_string = out.decode().strip()

    # Append any docs found in the Downloads directory.
    out = sp.check_output(
        ["find", "/home/bryan/Downloads", "-regex", DOC_PTTRN]
    )
    downloads_docs_string = out.decode().strip()
    all_docs_string = all_docs_string + "\n" + downloads_docs_string
    log.trace("----- Downloads -----\n{}", downloads_docs_string)

    all_docs = [
        Path(adoc)
        for adoc in all_docs_string.split("\n")
        if Path(adoc).is_file()
    ]
    return all_docs


def promote_most_recent_docs(
    docs: Iterable[PathLike], most_recent_docs: Iterable[PathLike]
) -> List[Path]:
    """Docs in Cache File are Brought to the Top of the List of Options"""
    docs = path_list(docs)
    most_recent_docs = path_list(most_recent_docs)

    new_docs = list(docs)
    for mr_doc in list(reversed(most_recent_docs)):
        if mr_doc in new_docs:
            new_docs.remove(mr_doc)
            new_docs.insert(0, mr_doc)
    return new_docs


def demote_open_docs(
    docs: Iterable[PathLike], open_docs: Iterable[PathLike]
) -> List[Path]:
    """Open Docs are Moved to the Bottom of the List of Options"""
    docs = path_list(docs)

    new_docs = list(docs)
    sorted_open_docs = []
    for odoc in open_docs:
        for doc in docs:
            if str(odoc) in str(doc):
                try:
                    new_docs.remove(doc)
                    sorted_open_docs.append(doc)
                except ValueError:
                    # Protects against multiple attempts to remove the same doc
                    # which happens when the same doc is opened up in multiple
                    # different instances.
                    pass
    new_docs.extend(sorted_open_docs)
    return new_docs


def choose_doc_to_open(available_docs: Iterable[PathLike]) -> BResult[Path]:
    printf_ps = sp.Popen(
        [
            "printf",
            "{}".format("\n".join(str(adoc) for adoc in available_docs)),
        ],
        stdout=sp.PIPE,
    )
    rofi_ps = sp.Popen(
        ["rofi", "-p", "Document", "-m", "-4", "-dmenu", "-i"],
        stdout=sp.PIPE,
        stdin=printf_ps.stdout,
    )
    printf_ps.wait()

    stdout, stderr = rofi_ps.communicate()

    if rofi_ps.returncode != 0:
        emsg = "The 'rofi' command failed."

        if stdout:
            emsg += f"\n\n----- STDOUT -----\n{stdout.decode().strip()}"

        if stderr:
            emsg += f"\n\n----- STDERR -----\n{stderr.decode().strip()}"

        return BErr(emsg)

    assert stdout
    output = stdout.decode().strip()

    if output.startswith("/"):
        doc = Path(output)
    else:
        doc = Path(f"{BOOKS_DIR}/{output}")

    return Ok(doc)


def add_to_mr_cache(
    most_recent_docs: Iterable[PathLike],
    new_doc: PathLike,
    open_docs: Iterable[PathLike],
) -> None:
    new_mr_cache_lines = get_new_mr_cache_lines(
        most_recent_docs, new_doc, open_docs
    )

    # Filter out docs that don't exist anymore.
    new_mr_cache_lines = [
        mr_doc for mr_doc in new_mr_cache_lines if mr_doc.is_file()
    ]

    with open(MOST_RECENT_CACHE_FILE, "w") as f:
        f.writelines([f"{new_doc}\n" for new_doc in new_mr_cache_lines])


def get_open_docs() -> List[Path]:
    try:
        cmd = (
            'wmctrl -lx | grep -E "zathura|okular" | tr -s " " | cut -d\' \''
            f' -f5- | grep -o "{DOC_PTTRN}"'
        )

        open_docs_string = shell(cmd)
        open_docs = [Path(x) for x in open_docs_string.split("\n")]

        log.debug("Open Docs: {}".format(open_docs))
    except sp.CalledProcessError:
        open_docs = []
        log.debug("No documents are currently open in zathura.")

    return open_docs


def open_document(doc: PathLike, *, replace: bool = False) -> None:
    active_window_class = shell("active_window_class")
    if active_window_class == "Zathura":
        _open_document("zathura", doc, replace=replace)
    elif active_window_class == "okular":
        _open_document("okular", doc, opts=["--unique"], replace=replace)
    else:
        _open_document("okular", doc, replace=replace)


def _open_document(
    cmd: str,
    doc: PathLike,
    *,
    opts: Iterable[str] = None,
    replace: bool = False,
) -> None:
    if opts is None:
        opts = []

    if replace:
        pid = int(shell("active_window_pid"))
        log.debug("Killing Document Instance: {}".format(pid))
        os.kill(pid, signal.SIGTERM)

    cmd_list = [cmd]
    cmd_list.extend(opts)
    cmd_list.append(str(doc))

    log.debug("Opening {} in {}...".format(doc, cmd))
    sp.Popen(cmd_list, stdout=sp.DEVNULL, stderr=sp.STDOUT)

    # HACK: I use this to force zathura to open in fullscreen on XFCE.
    time.sleep(0.2)
    sp.Popen(["fullscreen"])


def get_new_mr_cache_lines(
    most_recent_docs: Iterable[PathLike],
    new_doc: PathLike,
    open_docs: Iterable[PathLike] = None,
) -> List[Path]:
    most_recent_docs = path_list(most_recent_docs)
    new_doc = Path(new_doc)

    if open_docs is None:
        open_docs = []
    else:
        open_docs = path_list(open_docs)

    log.debug("Adding {} to cache file...".format(new_doc))
    seen_docs = set()
    sorted_open_docs = []
    for mr_doc in most_recent_docs[:]:
        for odoc in open_docs:
            if str(odoc) in str(mr_doc):
                sorted_open_docs.append(Path(mr_doc))
                seen_docs.add(mr_doc)
                break
        else:
            if str(new_doc) == str(mr_doc):
                seen_docs.add(mr_doc)

        if mr_doc in seen_docs:
            most_recent_docs.remove(mr_doc)
        else:
            seen_docs.add(mr_doc)

    if new_doc in most_recent_docs:
        most_recent_docs.remove(new_doc)

    first_docs = sorted_open_docs[:]
    if new_doc not in first_docs:
        first_docs.append(new_doc)

    most_recent_docs[0:0] = first_docs

    return most_recent_docs[:MAX_MOST_RECENT_DOCS]


def path_list(path_like_iter: Iterable[PathLike]) -> List[Path]:
    """
    Examples:
        >>> path_list(["foo"])
        [PosixPath('foo')]

        >>> path_list(["foo", "bar"])
        [PosixPath('foo'), PosixPath('bar')]

        >>> from pathlib import Path
        >>> path_list([Path("foo")])
        [PosixPath('foo')]
    """
    return [Path(P) for P in path_like_iter]


main = main_factory(parse_cli_args, run)
if __name__ == "__main__":
    sys.exit(main())
