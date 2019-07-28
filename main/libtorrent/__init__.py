"""Script to make torrenting movies and TV shows easier (wraps a P2P client).

Connects to a VPN (using Private Internet Access), downloads the torrent
(using a magnet file), disconnects from the VPN when the download is finished,
and then sends me a text message to let me know the download is complete.

Multiple torrents can be downloaded at the same time by simply running this
script multiple times (using different magnet files). If another instance of
this script is running, the primary instance will be signaled to enqueue the
new magnet file for download.
"""

import queue
import time

import gutils
from loguru import logger as log


DELUGE = ["sudo", "-E", "deluge-console"]
ARGS_FILE = gutils.xdg.init("data") / "args"
LOGGER_NAME = "torrent"

magnet_queue: "queue.Queue[str]" = queue.Queue()


def notify_and_log(msg: str) -> None:
    log.debug(msg)
    gutils.notify(msg, title=LOGGER_NAME)


def wait_for_first_magnet() -> None:
    while magnet_queue.empty():
        time.sleep(0.5)
