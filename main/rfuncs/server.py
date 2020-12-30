"""Remote Function Server"""

import argparse
import logging
import os
import sys
from typing import NamedTuple, Sequence
from wsgiref.simple_server import make_server

import prometheus_client as pc

from . import client
from .path_dispatcher import PathDispatcher
from .routes import route_registry


log = logging.getLogger(__name__)
PROMETHEUS_METRICS_PORT = 9101


class Arguments(NamedTuple):
    port: int
    token: str


def parse_cli_args(argv: Sequence[str]) -> Arguments:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=client.default_port(),
        help="The network port this server will listen on.",
    )
    parser.add_argument(
        "-T",
        "--token",
        default=client.default_token(),
        help="The access token used for authentication.",
    )
    args = parser.parse_args(argv[1:])
    return Arguments(**dict(args._get_kwargs()))


def init_logging() -> None:
    log_dir = "/var/log" if os.access("/var/log", os.W_OK) else "/var/tmp"
    log_file = f"{log_dir}/rfserver.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
        datefmt="%y-%m-%d %H:%M:%S",
        filename=log_file,
        filemode="a+",
    )
    console = logging.StreamHandler()
    log.addHandler(console)


def main(argv: Sequence[str] = None) -> int:
    if argv is None:
        argv = sys.argv

    args = parse_cli_args(argv)

    init_logging()
    try:
        pc.start_http_server(PROMETHEUS_METRICS_PORT)
        pid_dir = "/var/run" if os.access("/var/run", os.W_OK) else "/tmp"
        pid_file = f"{pid_dir}/rfserver.pid"
        with open(pid_file, "w") as f:
            f.write(str(os.getpid()))

        dispatcher = PathDispatcher(
            args.token, route_map=route_registry.to_route_map()
        )

        httpd = make_server("", args.port, dispatcher)
        log.info(f"Serving on port {args.port}...")
        httpd.serve_forever()
    except Exception:
        log.exception("The remote function server has crashed.")
        raise

    return 0
