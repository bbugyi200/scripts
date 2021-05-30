"""Script to make torrenting movies and TV shows easier (wraps a P2P client).

Connects to a VPN (using Private Internet Access), downloads the torrent
(using a magnet file), disconnects from the VPN when the download is finished,
and then sends me a text message to let me know the download is complete.

Multiple torrents can be downloaded at the same time by simply running this
script multiple times (using different magnet files). If another instance of
this script is running, the primary instance will be signaled to enqueue the
new magnet file for download.
"""

import atexit
import getpass
import os
from pathlib import Path
import pickle
import signal
import subprocess as sp
import sys
import time
import types
from typing import NamedTuple, Sequence

import bugyi
from bugyi import cli, xdg
from bugyi.core import catch
from loguru import logger as log

from . import worker


ARGS_FILE = xdg.init_full_dir("data") / "args"


class Arguments(NamedTuple):
    magnet: str
    debug: bool
    verbose: bool
    download_dir: Path
    delay: int
    timeout: float
    pudb: bool
    threading: str
    vpn: str


@catch
def main(argv: Sequence[str] = None) -> None:
    if argv is None:
        argv = sys.argv

    args = parse_cli_args(argv)
    bugyi.logging.configure("torrent", debug=args.debug, verbose=args.verbose)

    if args.pudb:
        import pudb

        pudb.set_trace()

    register_handlers()
    create_pidfile(args)

    time.sleep(args.delay)

    setup_env(args.vpn, args.download_dir)

    worker.new_torrent_worker(
        args.magnet,
        args.download_dir,
        args.timeout,
        use_threads=(args.threading == "y"),
    )
    worker.join_workers()


def parse_cli_args(argv: Sequence[str]) -> Arguments:
    parser = cli.ArgumentParser(description=__doc__)
    parser.add_argument("magnet", help="The torrent magnet file.")
    parser.add_argument(
        "-w",
        type=Path,
        dest="download_dir",
        default="/media/bryan/zeus/media/Entertainment/Movies",
        help=(
            "The directory that the torrents will be downloaded to."
            " Defaults to %(default)s."
        ),
    )
    parser.add_argument(
        "-D",
        type=int,
        dest="delay",
        default=0,
        help=(
            "Delay starting the script for DELAY seconds."
            " Defaults to %(default)s."
        ),
    )
    parser.add_argument(
        "-t",
        type=float,
        dest="timeout",
        default=0,
        help=(
            "Time (in hours) to attempt to complete download before timing"
            " out. If set to 0, this script will run forever without ever"
            " timing out. Defaults to %(default)s."
        ),
    )
    parser.add_argument(
        "--pudb",
        action='store_true',
        help="Run `pudb.set_trace()` on startup.",
    )
    parser.add_argument(
        "--threading",
        choices=("y", "n"),
        default="y",
        help="Enable multi-threading. Defaults to '%(default)s'.",
    )
    parser.add_argument(
        "--vpn",
        type=str,
        dest="vpn",
        default="nyc",
        help="VPN to connect to. Defaults to '%(default)s'.",
    )

    args = parser.parse_args(argv[1:])
    return Arguments(**dict(args._get_kwargs()))


def register_handlers() -> None:
    def term_handler(
        signum: signal.Signals,
        frame: types.FrameType,  # pylint: disable=unused-argument
    ) -> None:
        log.debug(f"Terminated via {signal.Signals(signum).name} signal.")
        worker.kill_all_workers()
        sys.exit(128 + signum)

    def usr1_handler(
        signum: signal.Signals,  # pylint: disable=unused-argument
        frame: types.FrameType,  # pylint: disable=unused-argument
    ) -> None:
        log.debug("SIGUSR1 signal received.")
        with ARGS_FILE.open("rb") as f:
            child_args = pickle.load(f)

        worker.wait_for_first_magnet()
        worker.new_torrent_worker(
            child_args.magnet, child_args.download_dir, child_args.timeout,
        )

    signal.signal(signal.SIGTERM, term_handler)
    signal.signal(signal.SIGINT, term_handler)
    signal.signal(signal.SIGUSR1, usr1_handler)


def create_pidfile(args: Arguments) -> None:
    """Duplicate Process Management"""
    try:
        bugyi.create_pidfile()
    except bugyi.StillAliveException as e:
        with ARGS_FILE.open("wb") as f:
            pickle.dump(args, f)

        log.debug(f"Sending SIGUSR1 to {e.pid}.")
        os.kill(e.pid, signal.SIGUSR1)

        # Exit without invoking exit handler.
        os._exit(0)  # pylint: disable=protected-access


def setup_env(vpn: str, download_dir: Path) -> None:
    log.info("Connecting to VPN and starting P2P client daemon...")

    def setup(cmd: str) -> None:
        try:
            sp.check_call(cmd, shell=True)
        except sp.CalledProcessError as e:
            log.error(
                "Failed to setup the proper environment for torrenting.\n\n"
                f"The following command failed: '{cmd}'"
            )
            raise e

    def teardown(cmd: str) -> None:
        atexit.register(lambda: sp.Popen(cmd, shell=True))

    setup(f"PIA start {vpn}")
    teardown("PIA stop")

    USER = getpass.getuser()
    setup(f"sudo chown -R {USER}:{USER} {download_dir}")
    teardown(f"sudo chown -R plex:plex {download_dir}")

    setup("sudo -E deluged")
    teardown("sudo killall deluged")

    setup("sudo -E deluge-web --fork")
    teardown("sudo killall deluge-web")
