import os
import sys

from flask_migrate import upgrade as migrate_upgrade

from app import create_app, db
from app.models import Phrase

env = os.environ.get("FLASK_ENV", "development")
app = create_app(env)


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "Phrase": Phrase}


@app.cli.command("init-db")
def init_db():
    """Apply all database migrations (safe to run repeatedly)."""
    with app.app_context():
        migrate_upgrade()
    print("Database is up to date.")


if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))

    local_hosts = {"127.0.0.1", "localhost", "::1"}
    if host not in local_hosts and not app.config.get("REQUIRE_AUTH"):
        print(
            "WARNING: binding to a non-local address without REQUIRE_AUTH. "
            "Set APP_PASSWORD and REQUIRE_AUTH=true before exposing this app.",
            file=sys.stderr,
        )

    # Never expose the Werkzeug debugger on a non-local interface.
    debug = env == "development" and host in local_hosts
    app.run(host=host, port=port, debug=debug)
