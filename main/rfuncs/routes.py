import json
import logging
from typing import Iterable

from .authenticator import ATTEMPT_LIMIT, ATTEMPT_PERIOD
from .route_registry import RouteRegistry
from .types import AnyStr, Environ, StartResponse


PLAIN_HEADER = [("Content-type", "text/plain")]

log = logging.getLogger(__name__)
route_registry = RouteRegistry()
route = route_registry.register


class Errors:
    @staticmethod
    def badauth_401(
        _environ: Environ, start_response: StartResponse
    ) -> Iterable[AnyStr]:
        start_response("401 Not Authorized", PLAIN_HEADER)
        yield "Not Authorized: Bad Access Token"

    @staticmethod
    def suspended_403(
        _environ: Environ, start_response: StartResponse
    ) -> Iterable[AnyStr]:
        start_response("403 Forbidden", PLAIN_HEADER)
        yield (
            "Access Suspended: This client address has made more than"
            f" {ATTEMPT_LIMIT} in the last {ATTEMPT_PERIOD} minutes. Access"
            " has been temporarily suspended. Check back later."
        )

    @staticmethod
    def notfound_404(
        _environ: Environ, start_response: StartResponse
    ) -> Iterable[AnyStr]:
        start_response("404 Not Found", PLAIN_HEADER)
        yield "Not Found"


@route("/sendmail", methods=["POST"])
def sendmail(
    environ: Environ, start_response: StartResponse
) -> Iterable[AnyStr]:
    import pymail

    start_response("200 OK", [("Content-type", "text/html")])

    params = environ["params"]
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

    yield (
        f"{status_msg}: sendmail(to={to!r}, subject={subject!r},"
        f" body={body!r})\n"
    )
