"""Consistent HTML and JSON error handling."""

from flask import Response, current_app, g, jsonify, render_template, request
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


def _plain_text(message, status):
    """Last-resort body used when even the error template cannot render."""
    return Response(
        f"{message}\nrequest_id={_request_id()}\n",
        status=status,
        mimetype="text/plain",
    )


def _render_error_page(message, status):
    """Render the styled error page, degrading to plain text.

    The page extends ``base.html``, so it needs the template loader and its
    context processors to be healthy.  If the whole template folder is missing
    (a stale interpreter after moving the checkout, a bad ``root_path``) the
    fallback keeps the original traceback visible instead of masking it with a
    secondary ``TemplateNotFound: error.html``.
    """
    try:
        return render_template("error.html", error=message), status
    except Exception:
        current_app.logger.exception(
            "Could not render error.html [request_id=%s]", _request_id()
        )
        return _plain_text(message, status)


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
        return _render_error_page(message, status)

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
        return _render_error_page(message, 500)
