import hmac
import json
import os
import re
import sqlite3
import uuid

import click
from flask import Flask, Response, abort, current_app, g, jsonify, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

from config import config

db = SQLAlchemy()
migrate = Migrate()


@event.listens_for(Engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record):
    """Make SQLite safe for concurrent readers and short writers."""
    if not isinstance(dbapi_connection, sqlite3.Connection):
        return
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
    finally:
        cursor.close()


def _ensure_directories(app):
    for key in ("AUDIO_DIR", "MEDIA_TMP_DIR"):
        path = app.config.get(key)
        if not path:
            raise RuntimeError(f"{key} must be configured")
        os.makedirs(path, exist_ok=True)


def _constant_time_equal(left, right):
    """Compare arbitrary text safely, including non-ASCII credentials."""
    return hmac.compare_digest(str(left).encode("utf-8"), str(right).encode("utf-8"))


def _check_basic_auth():
    """Optional single-password gate for non-local deployments."""
    if not current_app.config.get("REQUIRE_AUTH", False):
        return None
    if request.path == "/healthz":
        return None

    password = current_app.config.get("APP_PASSWORD")
    if not password:
        message = (
            "REQUIRE_AUTH is enabled but APP_PASSWORD is not set. "
            "Set APP_PASSWORD or disable REQUIRE_AUTH."
        )
        if request.path.startswith("/api/"):
            return jsonify({"error": message}), 503
        return Response(message, status=503, mimetype="text/plain")

    # Slow down credential guessing without blocking legitimate retries.
    limiter = current_app.extensions.get("rate_limiter")
    if limiter is not None:
        from app.utils.rate_limit import get_client_ip

        allowed, retry_after = limiter.hit(
            f"auth:{get_client_ip()}", limit=10, window_seconds=60
        )
        if not allowed:
            return Response(
                "Too many authentication attempts",
                status=429,
                headers={"Retry-After": str(retry_after)},
                mimetype="text/plain",
            )

    auth = request.authorization
    expected_user = current_app.config.get("APP_USERNAME", "kiku")
    if (
        not auth
        or auth.type != "basic"
        or not _constant_time_equal(auth.username or "", expected_user)
        or not _constant_time_equal(auth.password or "", password)
    ):
        if request.path.startswith("/api/"):
            return (
                jsonify({"error": "Authentication required"}),
                401,
                {"WWW-Authenticate": 'Basic realm="Kiku", charset="UTF-8"'},
            )
        return Response(
            "Authentication required",
            status=401,
            headers={"WWW-Authenticate": 'Basic realm="Kiku", charset="UTF-8"'},
            mimetype="text/plain",
        )
    return None


def _register_security_headers(app):
    @app.after_request
    def add_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "microphone=(self)")
        response.headers["Content-Security-Policy"] = app.config[
            "CONTENT_SECURITY_POLICY"
        ]
        if request.is_secure:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        response.headers["X-Request-ID"] = getattr(g, "request_id", "")
        return response


def _register_cli(app):
    @app.cli.command("media-audit")
    @click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON.")
    def media_audit(as_json):
        """Report orphaned and missing audio files."""
        from app.models import Conversation, Item, Phrase
        from app.utils.media import (
            audit_media,
            referenced_audio_filenames,
        )

        phrase_paths = [
            row[0] for row in db.session.query(Phrase.audio_path).all() if row[0]
        ]
        conversation_paths = [
            row[0] for row in db.session.query(Conversation.audio_path).all() if row[0]
        ]
        item_paths = [
            row[0] for row in db.session.query(Item.audio_path).all() if row[0]
        ]
        referenced = referenced_audio_filenames(
            phrase_paths, conversation_paths, item_paths
        )
        orphans, missing = audit_media(app.config["AUDIO_DIR"], referenced)

        payload = {
            "audio_dir": app.config["AUDIO_DIR"],
            "referenced": len(referenced),
            "orphans": orphans,
            "missing": missing,
        }
        if as_json:
            click.echo(json.dumps(payload, indent=2))
            return

        click.echo(f"Audio dir: {payload['audio_dir']}")
        click.echo(f"Referenced files: {payload['referenced']}")
        click.echo(f"Orphaned files: {len(orphans)}")
        for name in orphans:
            click.echo(f"  orphan  {name}")
        click.echo(f"Missing files: {len(missing)}")
        for name in missing:
            click.echo(f"  missing {name}")

    @app.cli.command("generate-vapid-keys")
    def generate_vapid_keys():
        """Generate a VAPID key pair for browser push reminders."""
        import base64

        from cryptography.hazmat.primitives import serialization
        from py_vapid import Vapid

        vapid = Vapid()
        vapid.generate_keys()
        raw_public = vapid.public_key.public_bytes(
            serialization.Encoding.X962,
            serialization.PublicFormat.UncompressedPoint,
        )
        public_key = (
            base64.urlsafe_b64encode(raw_public).rstrip(b"=").decode()
        )
        private_key = vapid.private_pem().decode().replace("\n", "\\n")
        click.echo(f"VAPID_PUBLIC_KEY={public_key}")
        click.echo(f'VAPID_PRIVATE_KEY="{private_key}"')
        click.echo(
            "\nAdd these to .env, restart the app, then run "
            "`flask send-reminders --dry-run`."
        )

    @app.cli.command("send-reminders")
    @click.option(
        "--dry-run",
        is_flag=True,
        help="List learners whose reminder window is open without sending.",
    )
    def send_reminders(dry_run):
        """Send at most one due-card reminder per learner per local day."""
        from app.services.push import PushConfigError, send_due_reminders

        try:
            results = send_due_reminders(dry_run=dry_run)
        except PushConfigError as error:
            raise click.ClickException(str(error)) from error

        if not results:
            click.echo("No reminders are due.")
            return

        for result in results:
            click.echo(
                f"user {result['user_id']}: {result['due']} due, "
                f"{result['subscriptions']} subscription(s), "
                f"local {result['local_time']}, sent {result['sent']}"
            )

    @app.cli.command("media-gc")
    @click.option(
        "--delete",
        is_flag=True,
        help="Actually delete orphans. Without this flag the command is a dry run.",
    )
    @click.option(
        "--older-than",
        default=86400,
        show_default=True,
        type=int,
        help="Only delete orphans older than this many seconds.",
    )
    def media_gc(delete, older_than):
        """Safely remove unreferenced audio files."""
        import time

        from app.models import Conversation, Item, Phrase
        from app.utils.media import audit_media, referenced_audio_filenames

        phrase_paths = [
            row[0] for row in db.session.query(Phrase.audio_path).all() if row[0]
        ]
        conversation_paths = [
            row[0] for row in db.session.query(Conversation.audio_path).all() if row[0]
        ]
        item_paths = [
            row[0] for row in db.session.query(Item.audio_path).all() if row[0]
        ]
        referenced = referenced_audio_filenames(
            phrase_paths, conversation_paths, item_paths
        )
        audio_dir = app.config["AUDIO_DIR"]
        orphans, _missing = audit_media(audio_dir, referenced)
        cutoff = time.time() - max(0, older_than)

        candidates = []
        for name in orphans:
            path = os.path.join(audio_dir, name)
            try:
                if os.path.getmtime(path) <= cutoff:
                    candidates.append(path)
            except OSError:
                continue

        if not delete:
            click.echo(
                f"Dry run: {len(candidates)} of {len(orphans)} orphaned files "
                "are old enough to delete. Re-run with --delete to remove them."
            )
            for path in candidates:
                click.echo(f"  would delete {os.path.basename(path)}")
            return

        removed = 0
        for path in candidates:
            try:
                os.remove(path)
                removed += 1
            except OSError as error:
                click.echo(f"Could not delete {path}: {error}", err=True)
        click.echo(f"Deleted {removed} orphaned audio file(s).")


def create_app(config_name=None, overrides=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    if config_name not in config:
        raise ValueError(
            f"Unknown config '{config_name}'. Choose one of: {', '.join(sorted(config))}"
        )

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    if overrides:
        app.config.update(overrides)

    config[config_name].init_app(app)
    _ensure_directories(app)

    db.init_app(app)
    migrate.init_app(app, db)

    from app.utils.rate_limit import RateLimiter

    app.extensions["rate_limiter"] = RateLimiter(
        max_keys=app.config.get("RATE_LIMIT_MAX_KEYS", 10_000)
    )

    if app.config.get("TRUST_PROXY"):
        from werkzeug.middleware.proxy_fix import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    from app.learning.cli import register_learning_cli
    from app.learning.routes import learn as learn_blueprint
    from app.main import main as main_blueprint
    from app.onboarding.routes import onboarding as onboarding_blueprint
    from app.teacher.routes import teacher as teacher_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(learn_blueprint)
    app.register_blueprint(onboarding_blueprint)
    app.register_blueprint(teacher_blueprint)
    register_learning_cli(app)

    from app.errors import register_error_handlers

    register_error_handlers(app)

    @app.before_request
    def assign_request_id():
        candidate = (request.headers.get("X-Request-ID") or "").strip()
        g.request_id = (
            candidate
            if re.fullmatch(r"[A-Za-z0-9._-]{1,64}", candidate)
            else uuid.uuid4().hex[:12]
        )

    app.before_request(_check_basic_auth)

    @app.url_value_preprocessor
    def pull_lang_code(endpoint, values):
        if not values or "lang_code" not in values:
            return
        code = values.pop("lang_code")
        from app.models_language import Language

        language = Language.query.filter_by(code=code).first()
        if language is None and code not in {"ko", "en", "am", "es", "ja"}:
            abort(404)
        g.lang_code = code
        g.language = language

    @app.url_defaults
    def add_lang_code(endpoint, values):
        if "lang_code" in values:
            return
        if endpoint in app.view_functions and app.url_map.is_endpoint_expecting(
            endpoint, "lang_code"
        ):
            values["lang_code"] = getattr(g, "lang_code", None) or "ko"

    from flask_wtf.csrf import generate_csrf

    @app.context_processor
    def inject_csrf_token():
        return {"csrf_token": generate_csrf}

    @app.context_processor
    def inject_active_language():
        from app.learning.service import current_language
        from app.models_language import Language

        try:
            language = current_language()
            languages = (
                Language.query.filter_by(is_active=True)
                .order_by(Language.id.asc())
                .all()
            )
            return {
                "active_language": language,
                "nav_languages": languages,
            }
        except Exception:
            current_app.logger.exception("Could not resolve the active language")
            return {"active_language": None, "nav_languages": []}

    @app.template_filter("has_hangul")
    def has_hangul(value):
        return any(
            "\uac00" <= char <= "\ud7a3"
            or "\u1100" <= char <= "\u11ff"
            or "\u3130" <= char <= "\u318f"
            for char in str(value)
        )

    _register_security_headers(app)
    _register_cli(app)

    return app
