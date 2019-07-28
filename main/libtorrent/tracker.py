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

import libtorrent as lib
from libtorrent import log


class MagnetTracker:
    """Thread-Safe Counter of Magnet Files"""

    def __init__(self):
        self.lock = threading.Lock()

        self.ids: Dict[int, str] = {}
        self.next_key = 0  # used to index into `self.ids`
        self.active_torrents = 0

        # I have trapped the plague in Pandora's Box. It is contained... for
        # now.
        lib.the_plague.acquire()

    def __getitem__(self, i: int) -> str:
        return self.ids[i]

    def done(self) -> int:
        """Called everytime a torrent finishes downloading."""
        with self.lock:
            self.active_torrents -= 1

            if self.active_torrents == 0:
                # Release the plague upon the world!
                # May God have mercy on any torrent that still draws breath! ;(
                lib.the_plague.release()

            return self.active_torrents

    def new(self, id_list: List[str]) -> int:
        """Captures ID of new torrent.

        Returns:
            An integer key that can be used to retrieve the torrent's ID
            (by indexing into `self.ids`).
        """
        log.vdebug("id_list = %s", id_list)  # type: ignore
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
