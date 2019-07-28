import threading
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

from loguru import logger as log


class MagnetTracker:
    """Thread-Safe Counter of Magnet Files"""

    def __init__(self):
        self.lock = threading.Lock()

        self.ids: Dict[int, str] = {}
        self.next_key = 0  # used to index into `self.ids`
        self.active_torrents = 0

        # This threading lock is not released again
        # until the last torrent worker is finished.
        self.all_work_is_done = threading.Lock()
        self.all_work_is_done.acquire()

    def __getitem__(self, i: int) -> str:
        return self.ids[i]

    def done(self) -> None:
        """Called everytime a torrent finishes downloading."""
        with self.lock:
            self.active_torrents -= 1

            if self.active_torrents == 0:
                self.all_work_is_done.release()

    def new(self, id_list: List[str]) -> int:
        """Captures ID of new torrent.

        Returns:
            An integer key that can be used to retrieve the torrent's ID
            (by indexing into `self.ids`).
        """
        log.trace("id_list = %s", id_list)  # type: ignore
        with self.lock:
            self.next_key += 1
            self.active_torrents += 1

            for ID in id_list:
                if ID in self.ids.values():
                    continue
                else:
                    self.ids[self.next_key] = ID
                    break
            else:
                raise RuntimeError(
                    "Something has gone wrong. "
                    "All Magnet IDs appear to have been used already."
                )

            return self.next_key
