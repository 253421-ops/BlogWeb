"""Límite de tráfico por consumidor (ventana deslizante de 60 s). Personas y servicios tienen límites distintos."""
import threading
import time
from collections import defaultdict, deque

from common.errors import too_many_requests


class RateLimiter:
    def __init__(self, user_limit: int, service_limit: int, window: float = 60.0):
        self.user_limit, self.service_limit, self.window = user_limit, service_limit, window
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, principal) -> None:
        limit = self.service_limit if principal.kind == "service" else self.user_limit
        now = time.monotonic()
        with self._lock:
            hits = self._hits[principal.sub]
            while hits and now - hits[0] >= self.window:
                hits.popleft()
            if len(hits) >= limit:
                raise too_many_requests()
            hits.append(now)
