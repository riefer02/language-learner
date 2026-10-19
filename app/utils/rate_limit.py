"""Thread-safe in-process rate limiting.

This is deliberately dependency-free. Replace the app extension with a Redis
implementation when the app runs more than one worker; the decorator contract
stays the same.
"""

import threading
import time
from collections import OrderedDict, deque
from functools import wraps

from flask import current_app, jsonify, request


def get_client_ip():
    """Return the caller IP.

    ``ProxyFix`` (enabled with TRUST_PROXY) is responsible for rewriting
    ``remote_addr`` from a trusted X-Forwarded-For chain. Parsing the raw
    header here would let any client spoof its limiter bucket.
    """
    return request.remote_addr or "unknown"


class RateLimiter:
    """Sliding-window limiter with bounded memory.

    Each key stores a deque of monotonic timestamps. Buckets are pruned on
    access and evicted oldest-first when the key cap is reached.
    """

    def __init__(self, max_keys=10_000, clock=time.monotonic):
        self._max_keys = max(1, int(max_keys))
        self._clock = clock
        self._lock = threading.Lock()
        self._buckets = OrderedDict()

    def hit(self, key, limit, window_seconds):
        """Record a hit. Return ``(allowed, retry_after_seconds)``."""
        limit = max(1, int(limit))
        window_seconds = max(1.0, float(window_seconds))
        now = self._clock()

        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                self._evict_if_needed()
                bucket = deque()
                self._buckets[key] = bucket
            else:
                self._buckets.move_to_end(key)

            cutoff = now - window_seconds
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= limit:
                retry_after = max(1, int(window_seconds - (now - bucket[0])) + 1)
                return False, retry_after

            bucket.append(now)
            return True, 0

    def _evict_if_needed(self):
        while len(self._buckets) >= self._max_keys:
            self._buckets.popitem(last=False)

    def clear(self):
        with self._lock:
            self._buckets.clear()

    def __len__(self):
        with self._lock:
            return len(self._buckets)


def rate_limit(limit, window_seconds=60, scope=None):
    """Limit a Flask view by client IP and endpoint.

    The decorator is a no-op when ``RATE_LIMIT_ENABLED`` is false, which keeps
    tests and local development predictable.
    """

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_app.config.get("RATE_LIMIT_ENABLED", True):
                return view(*args, **kwargs)

            limiter = current_app.extensions.get("rate_limiter")
            if limiter is None:
                return view(*args, **kwargs)

            bucket_scope = scope or request.endpoint or request.path
            key = f"{bucket_scope}:{get_client_ip()}"
            resolved_limit = limit() if callable(limit) else limit
            resolved_window = (
                window_seconds() if callable(window_seconds) else window_seconds
            )
            allowed, retry_after = limiter.hit(
                key,
                limit=resolved_limit,
                window_seconds=resolved_window,
            )
            if not allowed:
                response = jsonify(
                    {
                        "error": "Too many requests. Please slow down.",
                        "retry_after": retry_after,
                    }
                )
                response.status_code = 429
                response.headers["Retry-After"] = str(retry_after)
                return response

            return view(*args, **kwargs)

        return wrapped

    return decorator
