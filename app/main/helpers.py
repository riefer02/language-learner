"""Shared helpers for the main blueprint."""

from flask import current_app, g, jsonify, request
from flask_wtf.csrf import validate_csrf
from pydantic import ValidationError
from werkzeug.exceptions import BadRequest


def _request_id():
    return getattr(g, "request_id", "")


def _error(message, status):
    return jsonify({"error": message, "request_id": _request_id()}), status


def _parse_json(schema):
    """Return ``(model, None)`` or ``(None, error_response)``."""
    if not request.is_json:
        return None, _error("Request body must be JSON", 415)

    payload = request.get_json(silent=True)
    if payload is None:
        return None, _error("Request body must be valid JSON", 400)

    try:
        return schema.model_validate(payload), None
    except ValidationError as error:
        details = error.errors()
        message = "Invalid request"
        if details:
            location = ".".join(str(part) for part in details[0].get("loc", ()))
            message = (
                f"{location}: {details[0].get('msg')}"
                if location
                else details[0].get("msg", message)
            )
        return None, _error(message, 400)


def _check_csrf():
    if current_app.config.get("WTF_CSRF_ENABLED", True):
        token = request.headers.get("X-CSRFToken") or request.form.get(
            "csrf_token"
        )
        try:
            validate_csrf(token)
        except Exception as error:
            raise BadRequest("Invalid or missing CSRF token") from error
