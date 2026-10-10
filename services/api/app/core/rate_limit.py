import threading
import time
from collections import defaultdict, deque


class LoginRateLimiter:
    """Simple in-memory limiter: max failures per window, per key (ip + email)."""

    def __init__(self, max_attempts: int = 5, window_seconds: int = 900):
        self.max_attempts = max_attempts
        self.window = window_seconds
        self._fails: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, q: deque, now: float) -> None:
        while q and now - q[0] > self.window:
            q.popleft()

    def retry_after(self, key: str) -> int:
        """Seconds to wait; 0 means allowed."""
        now = time.monotonic()
        with self._lock:
            q = self._fails[key]
            self._prune(q, now)
            if len(q) >= self.max_attempts:
                return int(self.window - (now - q[0])) + 1
            return 0

    def record_failure(self, key: str) -> None:
        with self._lock:
            self._fails[key].append(time.monotonic())

    def reset(self, key: str) -> None:
        with self._lock:
            self._fails.pop(key, None)


login_limiter = LoginRateLimiter()