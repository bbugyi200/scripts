from pathlib import Path
import queue
import re
import subprocess as sp
import threading
import time
from typing import List, Union

from bugyi.core import shell
from bugyi.tools import notify
from loguru import logger as log

from .tracker import MagnetTracker


_magnet_queue: "queue.Queue[str]" = queue.Queue()


def new_torrent_worker(
    magnet: str,
    download_dir: Path,
    timeout: float,
    *,
    use_threads: bool = True,
) -> None:
    torrent_worker = _TorrentWorker(
        magnet=magnet, download_dir=download_dir, timeout=timeout
    )

    if use_threads:
        thread = threading.Thread(target=torrent_worker, daemon=True)
        thread.start()
    else:
        torrent_worker()


def wait_for_first_magnet() -> None:
    while _magnet_queue.empty():
        time.sleep(0.5)


def join_workers() -> None:
    wait_for_first_magnet()
    _magnet_queue.join()
    notify("All torrents are complete.", title="torrent")


def kill_all_workers() -> None:
    """Each torrent will be removed from the P2P client."""
    try:
        full_id_list = _parse_info("ID")
        log.trace("full_id_list = {}", full_id_list)
    except ValueError:
        return

    all_ids = [ID.split()[1] for ID in full_id_list]
    for ID in all_ids:
        _kill_worker(ID)


def _kill_worker(ID: str) -> None:
    """Remove torrent specified by @ID from the P2P client."""
    try:
        sp.check_call(["sudo", "-E", "deluge-console", "rm", "--confirm", ID])
        log.debug(f"Removed magnet #{ID}.")
    except sp.CalledProcessError:
        log.debug(f"Attempted to remove magnet #{ID} but it is NOT active.")


def _parse_info(field: str, ID: str = None) -> Union[str, List[str]]:
    """Wrapper for the `deluge-console info` command.

    Returns:
        Return type is `str` when @ID is given and `List[str]` otherwise.
    """
    log.trace(f"ID = {ID}")

    cmd = (
        "sudo -E deluge-console info --detailed --sort-reverse=time_added"
        f" {'' if ID is None else ID} | perl -nE 'print if /^{field}:/'"
    )
    out = shell(cmd)
    ret = out.split("\n")

    if ret[0] == "":
        raise ValueError(
            "Something went wrong with the `info` function. "
            f"Local state:\n\n{locals()}"
        )

    return ret if ID is None else ret[0]


class _TorrentWorker:
    magnet_tracker = MagnetTracker()
    INVALID_TRACKER_KEY = -1

    def __init__(self, magnet: str, download_dir: Path, timeout: float):
        self.magnet = magnet
        self.download_dir = download_dir
        self.timeout = timeout

        self._mt_key = self.INVALID_TRACKER_KEY
        self.is_enqueued = False

    def __call__(self) -> None:
        log.debug(f'Added "{self.title}" to magnet queue.')

        try:
            self.download_torrent()
        finally:
            self.magnet_tracker.done()
            with self.magnet_tracker.all_work_is_done:
                _kill_worker(self.magnet_tracker[self.mt_key])

                _magnet_queue.get()
                _magnet_queue.task_done()

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
        if not self.is_enqueued:
            raise RuntimeError(
                "Download must first be enqueued before attempting to access "
                "the magnet tracker key."
            )

        if self._mt_key == self.INVALID_TRACKER_KEY:
            id_list = [ID.split()[1] for ID in _parse_info("ID")]
            self._mt_key = self.magnet_tracker.new(id_list)

        log.trace("mt_key = {mt_key}", mt_key=self._mt_key)
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
                        "Torrent is still attempting to download "
                        f"\"{self.title}\" after {self.timeout:.1f} hour(s) "
                        "elapsed time. Shutting down early."
                    )

            time.sleep(SLEEP_TIME)

            if not self.is_enqueued:
                self._enqueue_download()

            full_state = _parse_info(
                "State", ID=self.magnet_tracker[self.mt_key]
            )

            state = str(full_state).split()[1]
            if state == "Downloading":
                download_started = True
            elif state == "Seeding" or (
                state == "Queued" and download_started
            ):
                notify(
                    f'Finished Downloading "{self.title}".', title="torrent",
                )
                return

    def _enqueue_download(self) -> None:
        """Add magnet file to Deluge's download queue."""
        self.is_enqueued = True
        for _ in range(10):
            time.sleep(1)

            try:
                sp.check_call(
                    [
                        "sudo",
                        "-E",
                        "deluge-console",
                        "add",
                        "--path",
                        str(self.download_dir),
                        self.magnet,
                    ]
                )
            except sp.CalledProcessError:
                magnet_was_added = False
            else:
                magnet_was_added = True

            if magnet_was_added:
                log.debug(f'Enqueued "{self.title}" download.')

                # Careful where you put this line. It is responsible for
                # preventing a race condition.
                _magnet_queue.put(self.magnet)

                break
        else:
            raise RuntimeError(
                f'Unable to add "{self.title}" to deluges\'s download queue.'
            )
