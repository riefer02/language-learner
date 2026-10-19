"""Lazy OpenAI client access for application services.

Importing this module never constructs a client. The client is created on the
first call to :func:`get_openai_client`, so booting the app, running migrations,
and collecting tests do not require an API key.
"""

import os
import threading

import httpx
from flask import current_app, has_app_context
from openai import OpenAI

DEFAULT_CONNECT_TIMEOUT = 5.0
DEFAULT_READ_TIMEOUT = 30.0


def _timeout():
    """Build a timeout from app config so operators can tune it per deploy."""
    connect = DEFAULT_CONNECT_TIMEOUT
    read = DEFAULT_READ_TIMEOUT
    if has_app_context():
        connect = current_app.config.get(
            "OPENAI_TIMEOUT_CONNECT", DEFAULT_CONNECT_TIMEOUT
        )
        read = current_app.config.get(
            "OPENAI_TIMEOUT_READ", DEFAULT_READ_TIMEOUT
        )
    return httpx.Timeout(
        connect=float(connect),
        read=float(read),
        write=10.0,
        pool=5.0,
    )

_INJECTED = object()

_client = None
_client_api_key = None
_client_lock = threading.Lock()


class OpenAIConfigError(RuntimeError):
    """Raised when an OpenAI call is attempted without an API key."""


def _config_value(name):
    """Read a config value from Flask when available, else from the environment."""
    if has_app_context():
        value = current_app.config.get(name)
        if value:
            return value
    return os.environ.get(name)


def _injected_client():
    if not has_app_context():
        return None
    return current_app.extensions.get("openai_client")


def get_openai_client():
    """Return a lazily created OpenAI client.

    A client injected via ``current_app.extensions["openai_client"]`` takes
    precedence, which lets tests run without a key or network access.
    """
    global _client, _client_api_key

    injected = _injected_client()
    if injected is not None:
        return injected

    with _client_lock:
        api_key = _config_value("OPENAI_API_KEY")

        if _client is not None and (
            _client_api_key is _INJECTED or _client_api_key == api_key
        ):
            return _client

        if not api_key:
            raise OpenAIConfigError(
                "OPENAI_API_KEY is not configured. Set it in the environment or "
                "Flask config before calling an AI service."
            )

        _client = OpenAI(
            api_key=api_key,
            timeout=_timeout(),
            max_retries=0,
        )
        _client_api_key = api_key
        return _client


def set_openai_client_for_testing(client):
    """Install a fake client without requiring Flask config or an API key."""
    global _client, _client_api_key
    with _client_lock:
        _client = client
        _client_api_key = _INJECTED


def reset_openai_client():
    """Drop the cached client, usually between tests or after key rotation."""
    global _client, _client_api_key
    with _client_lock:
        _client = None
        _client_api_key = None
