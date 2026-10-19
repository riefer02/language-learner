"""Consistent HTML and JSON error handling."""

from flask import g, jsonify, render_template, request
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge


def _request_id():
    return getattr(g, "request_id", "")


def _wants_json():
    return request.path.startswith("/api/") or (
        request.accept_mimetypes.best == "application/json"
    )


def _message_for(error):
    if isinstance(error, RequestEntityTooLarge):
        return "Request body is too large"
    if error.code == 404:
        return "Resource not found" if _wants_json() else "Page not found"
    if error.code == 405:
        return "Method not allowed"
    if error.code == 415:
        return "Unsupported media type"
    if error.code == 429:
        return "Too many requests. Please try again later."
    if error.code and 400 <= error.code < 500:
        return error.description or "Bad request"
    return "An internal error occurred"


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        status = error.code or 500
        message = _message_for(error)
        if _wants_json():
            return (
                jsonify({"error": message, "request_id": _request_id()}),
                status,
            )
        return render_template("error.html", error=message), status

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.exception(
            "Unhandled error [request_id=%s] %s", _request_id(), error
        )
        message = "An internal error occurred"
        if _wants_json():
            return (
                jsonify({"error": message, "request_id": _request_id()}),
                500,
            )
        return render_template("error.html", error=message), 500
