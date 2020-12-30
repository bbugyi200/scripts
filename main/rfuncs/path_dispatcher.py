import cgi
import logging
from typing import Iterable

from . import routes
from .authenticator import Authenticator
from .types import AuthStatus, Environ, MutableEnviron, RouteMap, StartResponse


log = logging.getLogger(__name__)


class PathDispatcher:
    def __init__(self, server_token: str, route_map: RouteMap) -> None:
        self.route_map = route_map
        self.authenticator = Authenticator(server_token)

    def __call__(
        self, environ: MutableEnviron, start_response: StartResponse
    ) -> Iterable[bytes]:
        _params = cgi.FieldStorage(environ["wsgi.input"], environ=environ)
        params = {key: _params.getvalue(key) for key in _params.keys()}

        method = None
        if "token" in params:
            client_token = params["token"]
            del params["token"]
            environ["params"] = params

            path = environ["PATH_INFO"]
            method = environ["REQUEST_METHOD"].lower()
            route = self.route_map.get(
                (method, path), routes.Errors.notfound_404
            )

            log.info(
                f"New Client Request: method={method!r}, path={path!r},"
                f" params={params!r}"
            )

            client_addr = _get_client_address(environ)
            auth_status = self.authenticator.check(client_addr, client_token)
            if auth_status is AuthStatus.DENIED:
                route = routes.Errors.badauth_401
            elif auth_status is AuthStatus.SUSPENDED:
                route = routes.Errors.suspended_403
        else:
            route = routes.Errors.no_token_401

        for resp_msg in route(environ, start_response):
            if isinstance(resp_msg, str):
                resp_msg = resp_msg.encode("utf-8")

            if method is not None:
                log.info(
                    f"{method.upper()} response from {path} route: {resp_msg!r}"
                )

            yield resp_msg


def _get_client_address(environ: Environ) -> str:
    try:
        return environ["HTTP_X_FORWARDED_FOR"].split(",")[-1].strip()
    except KeyError:
        return environ["REMOTE_ADDR"]
