"""(R)emote (F)unction Client"""

import os
from typing import Any

try:
    from requests import Response
except ImportError:
    pass


def default_port() -> int:
    return int(os.environ["RFSERVER_PORT"])


def default_token() -> str:
    return os.environ["RFSERVER_TOKEN"]


def default_hostname() -> str:
    return os.environ["RFSERVER_HOSTNAME"]


def post(handler_name: str, **kwargs: Any) -> Response:
    import requests

    data = kwargs
    data["token"] = default_token()
    return requests.post(
        f"http://{default_hostname()}:{default_port()}/{handler_name}",
        data=data,
    )
