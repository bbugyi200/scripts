import argparse
import atexit
import getpass
import logging
import os
from pathlib import Path
import pickle
import signal
import subprocess as sp
import sys
import time
from types import FrameType
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

import libtorrent as lib
import libtorrent.worker as worker


log = logging.getLogger(lib.LOGGER_NAME)


def main() -> int:
    args = parse_cli_args()

    lib.magnet_queue.maxsize = args.maxsize

    with gutils.logging.context(log, debug=args.debug, verbose=args.verbose):
        register_handlers()
        create_pidfile(args)

        time.sleep(args.delay)

        setup_env(args.vpn, args.download_dir)

        # Remove any torrents that might have been saved from your
        # last P2P session.
        worker.kill_all_workers()

        worker.new_torrent_worker(args)
        worker.join_workers()

        return 0


def parse_cli_args() -> argparse.Namespace:
    parser = gutils.ArgumentParser(description=lib.__doc__)
    parser.add_argument("magnet", help="The torrent magnet file.")

    default = "/media/bryan/zeus/media/Entertainment/Movies"
    parser.add_argument(
        "-w",
        type=Path,
        dest="download_dir",
        default=default,
        help=(
            "The directory that the torrents will be downloaded to. "
            "Defaults to {}.".format(default)
        ),
    )

    default = 0
    parser.add_argument(
        "-D",
        type=int,
        dest="delay",
        default=default,
        help=(
            "Delay starting the script for DELAY seconds. "
            "Defaults to {}.".format(default)
        ),
    )

    default = 0
    parser.add_argument(
        "-t",
        type=float,
        dest="timeout",
        default=default,
        help=(
            "Time (in hours) to attempt to complete download before timing "
            "out. If set to 0, this script will run forever without ever "
            "timing out. Defaults to {}.".format(default)
        ),
    )

    default = 0
    parser.add_argument(
        "--maxsize",
        type=int,
        dest="maxsize",
        default=default,
        help=(
            "Max number of torrents allowed to download at one time "
            "(additional torrents will be enqueued and start when a space "
            "opens up). Defaults to {}.".format(default)
        ),
    )

    default = "nyc"
    parser.add_argument(
        "--vpn",
        type=str,
        dest="vpn",
        default=default,
        help="VPN to connect to. Defaults to {}.".format(default),
    )

    return parser.parse_args()


def register_handlers() -> None:
    def term_handler(signum: signal.Signals, frame: FrameType) -> None:
        log.debug(
            "Terminated via {} signal.".format(signal.Signals(signum).name)
        )
        worker.kill_all_workers()
        sys.exit(128 + signum)

    def usr1_handler(signum: signal.Signals, frame: FrameType) -> None:
        log.debug("SIGUSR1 signal received.")
        with lib.ARGS_FILE.open("rb") as f:
            child_args = pickle.load(f)

        lib.wait_for_first_magnet()
        worker.new_torrent_worker(child_args)

    signal.signal(signal.SIGTERM, term_handler)
    signal.signal(signal.SIGINT, term_handler)
    signal.signal(signal.SIGUSR1, usr1_handler)


def setup_env(vpn: str, download_dir: str) -> None:
    log.info("Connecting to VPN and starting P2P client daemon...")

    def setup(*cmd: str) -> None:
        try:
            sp.check_call(cmd)
        except sp.CalledProcessError as e:
            log.error(
                "Failed to setup the proper environment for torrenting."
            )

            raise e

    def teardown(*cmd: str) -> None:
        atexit.register(lambda: sp.Popen(cmd))

    setup("PIA", "start", vpn)
    teardown("PIA", "stop")

    setup(
        "sudo",
        "chown",
        "-R",
        "{0}:{0}".format(getpass.getuser()),
        download_dir,
    )
    teardown("sudo", "chown", "-R", "plex:plex", download_dir)

    setup("sudo", "-E", "deluged")
    teardown("sudo", "killall", "deluged")

    setup("sudo", "-E", "deluge-web", "--fork")
    teardown("sudo", "killall", "deluge-web")


def create_pidfile(args: argparse.Namespace) -> None:
    """Duplicate Process Management"""
    try:
        gutils.create_pidfile()
    except gutils.StillAliveException as e:
        with lib.ARGS_FILE.open("wb") as f:
            pickle.dump(args, f)

        log.debug("Sending SIGUSR1 to {}.".format(e.pid))
        os.kill(e.pid, signal.SIGUSR1)

        # Exit without invoking exit handler.
        os._exit(0)
