import os
import tempfile
from datetime import timedelta
from typing import ClassVar

from dotenv import load_dotenv

# Load .env before any configuration class attributes are evaluated.
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'korean_learner.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS: ClassVar[dict] = {"pool_pre_ping": True}

    AUDIO_DIR = os.path.join(basedir, "app/static/audio")
    MEDIA_TMP_DIR = os.path.join(basedir, "instance", "media_tmp")
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1 MB is ample for JSON prompts.

    # AI providers. Clients are created lazily; a missing key does not prevent
    # the app from booting, running migrations, or executing tests.
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    TRANSLATION_MODEL = os.environ.get("TRANSLATION_MODEL", "gpt-5.6-luna")
    CONVERSATION_MODEL = os.environ.get("CONVERSATION_MODEL", "gpt-5.6-luna")
    TTS_MODEL = os.environ.get("TTS_MODEL", "gpt-audio-1.5")
    TTS_VOICE_1 = os.environ.get("TTS_VOICE_1", "onyx")
    TTS_VOICE_2 = os.environ.get("TTS_VOICE_2", "nova")
    OPENAI_TIMEOUT_CONNECT = 5.0
    OPENAI_TIMEOUT_READ = 30.0

    # Abuse controls. In-memory by default; swap the extension for a Redis
    # implementation when running more than one worker.
    RATE_LIMIT_ENABLED = _env_bool("RATE_LIMIT_ENABLED", True)
    RATE_LIMIT_TRANSLATE = _env_int("RATE_LIMIT_TRANSLATE", 10)
    RATE_LIMIT_CONVERSATION = _env_int("RATE_LIMIT_CONVERSATION", 5)
    RATE_LIMIT_WINDOW_SECONDS = _env_int("RATE_LIMIT_WINDOW_SECONDS", 60)
    RATE_LIMIT_MAX_KEYS = _env_int("RATE_LIMIT_MAX_KEYS", 10_000)
    TRUST_PROXY = _env_bool("TRUST_PROXY", False)

    # Learning-science guardrail: new material is a budget, not a binge.
    NEW_CARDS_PER_DAY = _env_int("NEW_CARDS_PER_DAY", 10)
    ONBOARDING_ENABLED = _env_bool("ONBOARDING_ENABLED", True)
    REVIEW_SESSION_LIMITS: ClassVar[dict] = {3: 4, 10: 20, 25: 50}

    # Speech checks are transcript-based evidence, not a pronunciation grade.
    SPEECH_SCORING_ENABLED = _env_bool("SPEECH_SCORING_ENABLED", True)
    SPEECH_PROVIDER = os.environ.get("SPEECH_PROVIDER", "openai")
    SPEECH_TRANSCRIBE_MODEL = os.environ.get(
        "SPEECH_TRANSCRIBE_MODEL", "gpt-transcribe"
    )
    SPEECH_MAX_BYTES = _env_int("SPEECH_MAX_BYTES", 5 * 1024 * 1024)
    SPEECH_ACCEPT_THRESHOLD = 0.72
    SCENE_MATCH_THRESHOLD = 0.78

    # Real-time speaking teacher. Uses the OpenAI key above.
    TEACHER_ENABLED = _env_bool("TEACHER_ENABLED", True)
    TEACHER_PROVIDER = os.environ.get("TEACHER_PROVIDER", "openai_realtime")
    TEACHER_MODEL = os.environ.get("TEACHER_MODEL", "gpt-realtime-2.1-mini")
    TEACHER_VOICE = os.environ.get("TEACHER_VOICE", "marin")
    TEACHER_TRANSCRIBE_MODEL = os.environ.get(
        "TEACHER_TRANSCRIBE_MODEL", "gpt-transcribe"
    )
    TEACHER_MAX_SESSION_MINUTES = _env_int("TEACHER_MAX_SESSION_MINUTES", 15)
    TEACHER_DAILY_MINUTES = _env_int("TEACHER_DAILY_MINUTES", 20)
    TEACHER_TIMEOUT_SECONDS = float(
        os.environ.get("TEACHER_TIMEOUT_SECONDS", "20")
    )

    # PWA push reminders. Generate keys with `flask generate-vapid-keys`.
    VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY")
    VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY")
    VAPID_SUBJECT = os.environ.get(
        "VAPID_SUBJECT", "mailto:hello@kiku.example"
    )
    PUSH_ENABLED = _env_bool("PUSH_ENABLED", True)
    REMINDER_WINDOW_MINUTES = _env_int("REMINDER_WINDOW_MINUTES", 15)

    # Optional stop-gap auth. Real per-user accounts arrive in Phase 1.
    REQUIRE_AUTH = _env_bool("REQUIRE_AUTH", False)
    APP_USERNAME = os.environ.get("APP_USERNAME", "kiku")
    APP_PASSWORD = os.environ.get("APP_PASSWORD")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", False)
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Local-day accounting for the new-card budget and streak. A real per-user
    # timezone arrives with accounts; this config covers local/single-user mode.
    LEARNER_TIMEZONE = os.environ.get("LEARNER_TIMEZONE", "UTC")

    # Security headers. CSP is deliberately strict: no inline scripts are used.
    CONTENT_SECURITY_POLICY = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "img-src 'self' data:; "
        "media-src 'self'; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'"
    )

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

    @staticmethod
    def init_app(app):
        import logging
        from logging.handlers import RotatingFileHandler

        if not app.config.get("SECRET_KEY") or app.config["SECRET_KEY"] == (
            "dev-key-change-in-production"
        ):
            raise RuntimeError("SECRET_KEY must be set to a strong value in production")

        log_path = os.environ.get("LOG_PATH", "app.log")
        file_handler = RotatingFileHandler(
            log_path, maxBytes=10 * 1024 * 1024, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s: %(message)s "
                "[%(request_id)s] [%(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)

        from app.logging_utils import RequestIdFilter

        file_handler.addFilter(RequestIdFilter())
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info("Korean Language Learner startup")


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    SECRET_KEY = "test-secret"
    WTF_CSRF_ENABLED = False
    RATE_LIMIT_ENABLED = False
    REQUIRE_AUTH = False
    ONBOARDING_ENABLED = False
    # Keep the legacy end-to-end tests able to drain the full seed deck.
    REVIEW_SESSION_LIMITS: ClassVar[dict] = {3: 100, 10: 100, 25: 100}
    # A file-backed SQLite database keeps every connection pointed at the same
    # schema. Tests override this with a per-test temp file via create_app().
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URI",
        f"sqlite:///{os.path.join(tempfile.mkdtemp(prefix='kiku-test-'), 'test.db')}",
    )
    AUDIO_DIR = tempfile.mkdtemp(prefix="kiku-test-audio-")
    MEDIA_TMP_DIR = tempfile.mkdtemp(prefix="kiku-test-tmp-")


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
