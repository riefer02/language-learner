"""Error-handler and startup-guard tests.

Covers the failure that bit a dev server after the checkout was moved: the app
could not open its database, and the 500 handler crashed too because
``error.html`` could not be found.  Also pins the two guards that make such a
misconfiguration visible at startup instead of on every request.
"""

import jinja2
import pytest
from sqlalchemy import text

from app import errors as error_handlers


def test_missing_page_renders_html_error(client):
    response = client.get("/ko/this-page-does-not-exist")

    assert response.status_code == 404
    assert response.mimetype == "text/html"
    assert b"Page not found" in response.data


def test_missing_api_route_renders_json_error(client):
    response = client.get("/api/this-route-does-not-exist")

    assert response.status_code == 404
    assert response.mimetype == "application/json"
    assert response.get_json()["error"] == "Resource not found"


def test_error_page_falls_back_to_text_when_template_missing(client, monkeypatch):
    def explode(*args, **kwargs):
        raise jinja2.TemplateNotFound("error.html")

    monkeypatch.setattr(error_handlers, "render_template", explode)

    response = client.get("/ko/this-page-does-not-exist")

    assert response.status_code == 404
    assert response.mimetype == "text/plain"
    assert b"Page not found" in response.data
    assert b"request_id=" in response.data


@pytest.mark.parametrize("path", ["/ko/this-page-does-not-exist", "/api/nope"])
def test_error_handler_never_masks_the_original_error(app, path):
    """A 500 raised from a view still reaches the handler, not the debugger."""

    def boom():
        raise RuntimeError("kaboom")

    endpoint = f"boom-error-test-{path.strip('/').replace('/', '-')}"
    app.add_url_rule(path, endpoint, boom)

    response = app.test_client().get(path)

    assert response.status_code == 500


def test_sqlite_directory_is_created_at_startup(tmp_path):
    """A database path in a missing directory must not fail on first query."""
    from app import create_app, db

    db_path = tmp_path / "nested" / "deeper" / "kiku.db"
    overrides = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "AUDIO_DIR": str(tmp_path / "audio"),
        "MEDIA_TMP_DIR": str(tmp_path / "media"),
        "SECRET_KEY": "test",
    }

    app = create_app("testing", overrides=overrides)

    assert db_path.parent.is_dir()
    with app.app_context():
        db.session.execute(text("SELECT 1"))


def test_empty_database_uri_is_not_parsed():
    """``DATABASE_URL=`` in .env must not crash the directory guard."""
    from app import _ensure_sqlite_directory

    class EmptyUriApp:
        def __init__(self):
            self.config = {"SQLALCHEMY_DATABASE_URI": ""}

    # Would raise ArgumentError: Could not parse rfc1738 URL from string ''.
    _ensure_sqlite_directory(EmptyUriApp())


def test_uncreatable_database_directory_names_the_database(tmp_path):
    """A permission problem should say which database it was creating."""
    from app import create_app

    blocker = tmp_path / "not-a-dir"
    blocker.write_text("file, not a directory")

    overrides = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{blocker / 'sub' / 'kiku.db'}",
        "AUDIO_DIR": str(tmp_path / "audio"),
        "MEDIA_TMP_DIR": str(tmp_path / "media"),
        "SECRET_KEY": "test",
    }

    with pytest.raises(RuntimeError, match="SQLite database at"):
        create_app("testing", overrides=overrides)


def test_verify_checkout_path_rejects_a_gone_directory():
    """A server outliving a rename must say so, not 500 on every request."""
    from app import _verify_checkout_path

    class StaleApp:
        root_path = "/Users/andrew/Code/korean-language-learner"

    with pytest.raises(RuntimeError, match="no longer exists"):
        _verify_checkout_path(StaleApp())


def test_verify_checkout_path_accepts_a_real_checkout(app):
    from app import _verify_checkout_path

    _verify_checkout_path(app)


def test_create_app_actually_calls_the_checkout_guard(monkeypatch):
    """Deleting the guard call in create_app must fail this suite, not just prod."""
    from flask import Flask

    import app as app_module

    class StaleFlask(Flask):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.root_path = "/Users/andrew/Code/korean-language-learner"

    monkeypatch.setattr(app_module, "Flask", StaleFlask)

    with pytest.raises(RuntimeError, match="no longer exists"):
        app_module.create_app("testing", overrides={"TESTING": True})


