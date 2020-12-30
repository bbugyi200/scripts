from typing import Callable, Sequence

import prometheus_client as pc

from .types import Route, RouteMap


route_time = pc.Summary(
    "rfserver_route_time",
    "The amount of time spent in each route.",
    ["endpoint"],
)


class RouteRegistry:
    def __init__(self) -> None:
        self.map: RouteMap = {}

    def to_route_map(self) -> RouteMap:
        return self.map

    def register(
        self, path: str, methods: Sequence[str] = None
    ) -> Callable[[Route], Route]:
        if methods is None:
            methods = ["GET"]

        def _register(route: Route) -> Route:
            assert methods is not None
            timed_route = route_time.labels(endpoint=path).time()(route)
            for method in methods:
                self.map[method.lower(), path] = timed_route
            return timed_route

        return _register
