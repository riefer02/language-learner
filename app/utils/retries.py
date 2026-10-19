"""Bounded retries for transient OpenAI failures."""

import random
import time

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)

TRANSIENT_ERRORS = (
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    InternalServerError,
)


def is_transient_error(error):
    """Return True only for errors that are safe to retry."""
    if isinstance(error, TRANSIENT_ERRORS):
        return True
    if isinstance(error, APIStatusError):
        status = getattr(error, "status_code", None)
        return status == 429 or (
            isinstance(status, int) and 500 <= status <= 599
        )
    return False


def call_with_retries(fn, attempts=3, base_delay=0.5, max_delay=4.0, sleep=time.sleep):
    """Call ``fn`` with exponential backoff for transient OpenAI errors.

    Authentication, validation, and other non-transient errors are raised
    immediately. The final error is re-raised after the last attempt.
    """
    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    for attempt in range(attempts):
        try:
            return fn()
        except Exception as error:
            if not is_transient_error(error) or attempt == attempts - 1:
                raise

            delay = min(max_delay, base_delay * (2**attempt))
            # Jitter avoids a thundering herd when several requests retry.
            delay *= random.uniform(0.5, 1.0)
            sleep(delay)
