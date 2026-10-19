"""Logging helpers shared by application and production configuration."""

import logging

from flask import g, has_request_context


class RequestIdFilter(logging.Filter):
    """Attach the current request ID to every log record."""

    def filter(self, record):
        record.request_id = (
            getattr(g, "request_id", "-") if has_request_context() else "-"
        )
        return True
