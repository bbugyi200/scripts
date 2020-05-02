"""Custom Types"""

import enum
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    NamedTuple,
    Optional,
    Tuple,
    Union,
)


try:
    from sys import _OptExcInfo
    from typing import Protocol
except ImportError:
    _OptExcInfo = object  # type: ignore
    Protocol = object  # type: ignore


AnyStr = Union[str, bytes]
Environ = Mapping[str, Any]
MutableEnviron = MutableMapping[str, Any]
Route = Callable[[Environ, 'StartResponse'], Iterable[AnyStr]]
RouteMap = Dict[Tuple[str, str], Route]


class StartResponse(Protocol):
    """
    Type protocol for the 'start_response' callable that gets passed into the
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
