from typing import Callable, Sequence

from .types import Route, RouteMap


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
            for method in methods:
                self.map[method.lower(), path] = route
            return route

        return _register
