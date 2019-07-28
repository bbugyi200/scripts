import argparse
from pathlib import Path
import re
import subprocess as sp
import threading
import time
from typing import (  # noqa
    Any,
    Callable,
    Container,
    Dict,
    Generator,
    Iterable,
    Iterator,
    List,
    NoReturn,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypeVar,
    Union,
)

import gutils
from loguru import logger as log

import libtorrent as lib
from libtorrent.tracker import MagnetTracker


def new_torrent_worker(args: argparse.Namespace) -> None:
    torrent_worker = _TorrentWorker(
        magnet=args.magnet,
        download_dir=args.download_dir,
        timeout=args.timeout,
    )
    thread = threading.Thread(target=torrent_worker, daemon=True)
    thread.start()


def join_workers() -> None:
    lib.wait_for_first_magnet()
    lib.magnet_queue.join()
    lib.notify_and_log("All torrents are complete.")


def kill_all_workers() -> None:
    """Each torrent will be removed from the P2P client."""
    try:
        full_id_list = _parse_info("ID")
        log.trace("full_id_list = %s", full_id_list)  # type: ignore
    except ValueError:
        return

    all_ids = [ID.split()[1] for ID in full_id_list]
    for ID in all_ids:
        _kill_worker(ID)


def _kill_worker(ID: str) -> None:
    """Remove torrent specified by @ID from the P2P client."""
    try:
        sp.check_call(lib.DELUGE + ["rm", ID])
        log.debug(f"Removed magnet #{ID}.")
    except sp.CalledProcessError:
        log.debug(
            f"Attempted to remove magnet #{ID} but it is NOT active."
        )


def _parse_info(field: str, ID: str = None) -> Union[str, List[str]]:
    """Wrapper for the `deluge-console info` command.

    Returns:
        Return type is `str` when @ID is given and `List[str]` otherwise.
    """
    log.trace(f"ID = {ID}")  # type: ignore

    cmd = (
        f"{' '.join(lib.DELUGE)} info --sort-reverse=time_added "
        f"{'' if ID is None else ID} | awk -F: "
        f"'{{{{if ($1==\"{field}\") print $0}}}}'"
    )
    out = gutils.shell(cmd)
    ret = out.split("\n")

    if ret[0] == "":
        raise ValueError(
            "Something went wrong with the `info` function. "
            f"Local state:\n\n{locals()}"
        )

    return ret if ID is None else ret[0]


class _TorrentWorker:
    magnet_tracker = MagnetTracker()

    def __init__(self, magnet: str, download_dir: Path, timeout: float):
        self.magnet = magnet
        self.download_dir = download_dir
        self.timeout = timeout

    def __call__(self):
        log.debug(f'Added "{self.title}" to magnet queue.')

        try:
            self.download_torrent()
        finally:
            self.magnet_tracker.done()
            with self.magnet_tracker.all_work_is_done:
                _kill_worker(self.magnet_tracker[self.mt_key])

                lib.magnet_queue.get()
                lib.magnet_queue.task_done()

    @property
    def title(self) -> str:
        match = re.search("&dn=(.*?)&", self.magnet)
        if match:
            return match.group(1)
        else:
            return "UNKNOWN TITLE"

    @property
    def mt_key(self) -> int:
        """Magnet Tracker Key

        A key which can be used to index into the magnet tracker in order to
        retrieve the Deluge ID corresponding to this worker's magnet.
        """
        if getattr(self, '_mt_key', None) is None:
            self._enqueue_download()

            id_list = [ID.split()[1]
                       for ID in _parse_info("ID")]

            self._mt_key = self.magnet_tracker.new(id_list)

        log.trace("mt_key = %s", self._mt_key)  # type: ignore
        return self._mt_key

    def download_torrent(self) -> None:
        download_started = False

        i = 0
        while True:
            SLEEP_TIME = 5

            i += 1
            if self.timeout:
                SECONDS_IN_HOUR = 3600
                if i > (self.timeout * SECONDS_IN_HOUR / SLEEP_TIME):
                    raise RuntimeError(
                        f'Torrent is still attempting to download '
                        f'"{self.title}" after {self.timeout:.1f} hour(s) '
                        'elapsed time. Shutting down early.'
                    )

            time.sleep(SLEEP_TIME)

            # Note that when the `self.mt_key` property is accessed,
            # the Deluge download is automatically enqueued.
            full_state = _parse_info(
                "State",
                ID=self.magnet_tracker[self.mt_key],
            )

            state = str(full_state).split()[1]
            if state == "Downloading":
                download_started = True
            elif state == "Seeding" or (
                state == "Queued" and download_started
            ):
                lib.notify_and_log(f'Finished Downloading "{self.title}".')
                return

    def _enqueue_download(self) -> None:
        """Add magnet file to Deluge's download queue."""
        for i in range(10):
            time.sleep(1)

            try:
                sp.check_call(
                    lib.DELUGE +
                    ["add", "-p", str(self.download_dir), self.magnet]
                )
            except sp.CalledProcessError:
                magnet_was_added = False
            else:
                magnet_was_added = True

            if magnet_was_added:
                log.debug(
                    f'Added "{self.title}" to Deluge\'s '
                    "download queue."
                )

                lib.magnet_queue.put(self.magnet)

                break
        else:
            raise RuntimeError(
                'Unable to add "{self.title}" to deluges\'s download '
                'queue.'
            )
