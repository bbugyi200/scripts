import argparse
import contextlib
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

import libtorrent as lib
from libtorrent import log
from libtorrent.tracker import MagnetTracker


def new_torrent_worker(args: argparse.Namespace) -> None:
    torrent_worker = _TorrentWorker(
        magnet=args.magnet,
        download_dir=args.download_dir,
        timeout=args.timeout,
    )
    thread = threading.Thread(target=torrent_worker.work, daemon=True)
    thread.start()


def join_workers() -> None:
    lib.wait_for_first_magnet()
    lib.magnet_queue.join()
    lib.notify_and_log("All torrents are complete.")


def kill_all_workers() -> None:
    """Each torrent will be removed from the P2P client."""
    try:
        full_id_list = lib.run_info_cmd("ID")
        log.vdebug("full_id_list = %s", full_id_list)  # type: ignore
    except ValueError:
        return

    all_ids = [ID.split()[1] for ID in full_id_list]
    for ID in all_ids:
        _kill_worker(ID)


def _kill_worker(ID: str) -> None:
    """Remove torrent specified by @ID from the P2P client."""
    try:
        sp.check_call(lib.DELUGE + ["rm", ID])
        log.debug("Successfully removed magnet #{}.".format(ID))
    except sp.CalledProcessError:
        log.debug(
            "Attempted to remove magnet #{} but it is NOT active.".format(ID)
        )


class _TorrentWorker:
    magnet_tracker = MagnetTracker()

    def __init__(self, magnet: str, download_dir: Path, timeout: float):
        self.magnet = magnet
        self.download_dir = download_dir
        self.timeout = timeout

    @contextlib.contextmanager
    def notify_context(self) -> Generator:
        try:
            yield
        except RuntimeError as e:
            lib.notify_and_log(str(e))
            raise

    @property
    def title(self) -> str:
        match = re.search("&dn=(.*?)&", self.magnet)
        if match:
            return match.group(1)
        else:
            return "UNKNOWN TITLE"

    def start_download(self) -> int:
        i = 0
        while True:
            time.sleep(1)
            try:
                sp.check_call(
                    lib.DELUGE +
                    ["add", "-p", str(self.download_dir), self.magnet]
                )
            except sp.CalledProcessError:
                i += 1
                if i <= 10:
                    continue
                else:
                    raise RuntimeError(
                        'Failed to start "{}".'.format(self.title)
                    )
            else:
                log.debug(
                    'Successfully added "{}".'.format(self.title)
                )

                try:
                    id_list = [ID.split()[1]
                               for ID in lib.run_info_cmd("ID")]
                    mkey = self.magnet_tracker.new(id_list)
                except ValueError:
                    raise RuntimeError(
                        "Something is not right. The torrent has been "
                        "added to the P2P client but `run_info_cmd(ID)` "
                        "has somehow failed."
                    )

                if not lib.MASTER_IS_ONLINE_FILE.exists():
                    lib.MASTER_IS_ONLINE_FILE.touch()

                return mkey

    def finish_download(self, mkey: int) -> None:
        download_started = False

        i = 0
        while True:
            SLEEP_TIME = 5

            i += 1
            if self.timeout:
                SECONDS_IN_HOUR = 3600
                if i > (self.timeout * SECONDS_IN_HOUR / SLEEP_TIME):
                    msg = (
                        'Torrent is still attempting to download "{0}" '
                        "after {1:.1f} hour(s) elapsed time. Shutting "
                        "down early.".format(self.title, self.timeout)
                    )
                    raise RuntimeError(msg)

            time.sleep(SLEEP_TIME)

            full_state = lib.run_info_cmd(
                "State",
                ID=self.magnet_tracker[mkey],
            )

            state = str(full_state).split()[1]
            if state == "Downloading":
                download_started = True
            elif state == "Seeding" or (
                state == "Queued" and download_started
            ):
                lib.notify_and_log(f'Finished Downloading "{self.title}".')
                return

    def work(self):
        """Downloads the torrent given by the @args.magnet string."""
        log.debug(
            'Adding "{}" to Magnet Queue...'.format(self.title)
        )
        lib.magnet_queue.put(self.magnet)

        try:
            mkey = self.start_download()
            self.finish_download(mkey)
        finally:
            self.magnet_tracker.done()

            with lib.the_plague:
                # The plague has been released!
                # So be it! We shall all die together!
                _kill_worker(self.magnet_tracker[mkey])

                lib.magnet_queue.get()
                lib.magnet_queue.task_done()
