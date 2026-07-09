"""Rate limiter simple en mémoire."""
import threading
from datetime import datetime, timedelta
from collections import defaultdict


class RateLimiter:
    _instance = None

    @classmethod
    def get(cls) -> "RateLimiter":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._attempts = defaultdict(list)
        self._lock     = threading.Lock()

    def is_blocked(self, key: str, max_attempts: int = 5,
                   window_min: int = 5) -> bool:
        with self._lock:
            cutoff = datetime.now() - timedelta(minutes=window_min)
            self._attempts[key] = [
                t for t in self._attempts[key] if t > cutoff
            ]
            return len(self._attempts[key]) >= max_attempts

    def record(self, key: str):
        with self._lock:
            self._attempts[key].append(datetime.now())

    def count(self, key: str, window_min: int = 60) -> int:
        with self._lock:
            cutoff = datetime.now() - timedelta(minutes=window_min)
            return sum(1 for t in self._attempts[key] if t > cutoff)

    def reset(self, key: str):
        with self._lock:
            self._attempts[key] = []
