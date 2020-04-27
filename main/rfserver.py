"""(R)emote (F)unction Server"""

import argparse
import cgi
import enum
import json
import logging
import os
from pathlib import Path
import sys
import time
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)
from wsgiref.simple_server import make_server

import rfclient

try:
    from sys import _OptExcInfo
    from typing import Protocol
except ImportError:
    _OptExcInfo = object  # type: ignore
    Protocol = object  # type: ignore


log = logging.getLogger(__name__)

ATTEMPT_LIMIT = 10
ATTEMPT_PERIOD = 10  # In minutes
PLAIN_HEADER = [("Content-type", "text/plain")]

# Custom Types
AnyStr = Union[str, bytes]
Environ = Mapping[str, Any]
Params = Mapping[str, Any]
Handler = Callable[[Params, Environ, 'StartResponse'], Iterable[AnyStr]]


class StartResponse(Protocol):
    """
    Type definition for the 'start_response' callable that gets passed into the
    route handlers.
    """
    def __call__(
        self,
        status: str,
        headers: List[Tuple[str, str]],
        exc_info: Optional[_OptExcInfo] = None,
    ) -> Callable[[bytes], Any]:
        pass


class AccessRecord(NamedTuple):
    client_addr: str
    granted: bool
    time: float


class AuthStatus(enum.Enum):
    GRANTED = "GRANTED"
    DENIED = "DENIED"
    SUSPENDED = "SUSPENDED"

    def __str__(self) -> str:
        return self.value


def notfound_404(
    _params: Params, _environ: Environ, start_response: StartResponse
) -> Iterable[AnyStr]:
    start_response("404 Not Found", PLAIN_HEADER)
    yield "Not Found"


def badauth_401(
    _params: Params, _environ: Environ, start_response: StartResponse
) -> Iterable[AnyStr]:
    start_response("401 Not Authorized", PLAIN_HEADER)
    yield "Not Authorized: Bad Access Token"


def suspended_403(
    _params: Params, _environ: Environ, start_response: StartResponse
) -> Iterable[AnyStr]:
    start_response("403 Forbidden", PLAIN_HEADER)
    yield (
        "Access Suspended: This client address has made more than"
        f" {ATTEMPT_LIMIT} in the last {ATTEMPT_PERIOD} minutes. Access has"
        " been temporarily suspended. Check back later."
    )


class PathDispatcher:
    def __init__(
        self, token: str, handler_map: Dict[Tuple[str, str], Handler]
    ) -> None:
        self.handler_map = handler_map
        self.authenticator = Authenticator(token)

    def __call__(
        self, environ: Dict[str, Any], start_response: StartResponse
    ) -> Iterable[bytes]:
        _params = cgi.FieldStorage(environ["wsgi.input"], environ=environ)
        params = {key: _params.getvalue(key) for key in _params.keys()}

        client_token = params["token"]
        del params["token"]

        path = environ["PATH_INFO"]
        method = environ["REQUEST_METHOD"].lower()
        handler = self.handler_map.get((method, path), notfound_404)

        log.info(
            f"New Client Request: method={method!r}, path={path!r},"
            f" params={params!r}"
        )

        client_addr = get_client_address(environ)
        auth_status = self.authenticator.check(client_addr, client_token)
        if auth_status is AuthStatus.DENIED:
            handler = badauth_401
        elif auth_status is AuthStatus.SUSPENDED:
            handler = suspended_403

        return map(
            lambda x: x.encode("utf-8") if isinstance(x, str) else x,
            handler(params, environ, start_response),
        )


class HandlerRegistry:
    def __init__(self) -> None:
        self.registry: Dict[Tuple[str, str], Handler] = {}

    def register(
        self, path: str, methods: Sequence[str] = None
    ) -> Callable[[Handler], Handler]:
        if methods is None:
            methods = ["GET"]

        def _register(handler: Handler) -> Handler:
            assert methods is not None
            for method in methods:
                self.registry[method.lower(), path] = handler
            return handler

        return _register


handler_registry = HandlerRegistry()
route = handler_registry.register


class Authenticator:
    def __init__(self, server_token: str) -> None:
        self.server_token = server_token
        self.access_records: Set[AccessRecord] = set()

    def check(self, client_addr: str, client_token: str) -> AuthStatus:
        now = time.time()

        recent_failed_attempts = [
            rec
            for rec in self.access_records
            if rec.client_addr == client_addr
            and (now - rec.time) < (ATTEMPT_PERIOD * 60)
        ]
        if len(recent_failed_attempts) > ATTEMPT_LIMIT:
            status = AuthStatus.SUSPENDED
        elif client_token == self.server_token:
            status = AuthStatus.GRANTED
        else:
            status = AuthStatus.DENIED

        arec = AccessRecord(client_addr, status == AuthStatus.GRANTED, now)
        log.info(f"Access {status}: {arec}")
        self.access_records.add(arec)

        return status


def get_client_address(environ: Environ) -> str:
    try:
        return environ['HTTP_X_FORWARDED_FOR'].split(',')[-1].strip()
    except KeyError:
        return environ['REMOTE_ADDR']


@route("/sendmail", methods=["POST"])
def sendmail(
    params: Params, _environ: Environ, start_response: StartResponse
) -> Iterable[AnyStr]:
    import pymail

    start_response("200 OK", [("Content-type", "text/html")])

    to = params["to"]
    subject = params.get("subject", "")
    body = params.get("body", "[]")
    if isinstance(body, str):
        if body.startswith('[') and body.endswith(']'):
            body = json.loads(body)
        else:
            body = [body]

    ec = pymail.sendmail(to=to, subject=subject, body=body)
    status_msg = "SUCCESS" if ec == 0 else "FAILED"

    log_msg = (
        f"{status_msg}: sendmail(to={to!r}, subject={subject!r},"
        f" body={body!r})\n"
    )
    log.info(log_msg)
    yield log_msg


def parse_cli_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=rfclient.default_port(),
        help="The network port this server will listen on.",
    )
    parser.add_argument(
        "-T",
        "--token",
        default=rfclient.default_token(),
        help="The access token used for authentication.",
    )
    args = parser.parse_args(argv[1:])
    return args


def init_logging() -> None:
    log_dir = "/var/log" if os.access("/var/log", os.W_OK) else "/var/tmp"
    log_file = Path(f"{log_dir}/{os.path.basename(__file__)}").with_suffix(
        ".log"
    )
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
        pid_dir = "/var/run" if os.access("/var/run", os.W_OK) else "/tmp"
        pid_file = Path(f"{pid_dir}/{os.path.basename(__file__)}").with_suffix(
            ".pid"
        )
        with open(pid_file, "w") as f:
            f.write(str(os.getpid()))

        dispatcher = PathDispatcher(
            args.token, handler_map=handler_registry.registry
        )

        httpd = make_server("", args.port, dispatcher)
        print(f"Serving on port {args.port}...")
        httpd.serve_forever()
    except Exception:
        log.exception("The server has crashed.")

    return 0
