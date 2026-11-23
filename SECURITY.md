# Security

Kiku is currently a **local-first single-user application**. Do not expose it to
the public internet without adding real accounts and reviewing the deployment
configuration.

## Reporting

Please report vulnerabilities privately through GitHub’s **Report a
vulnerability** flow (Security → Advisories) rather than a public issue.

## Before exposing the app

1. Set `FLASK_ENV=production`.
2. Set a random `SECRET_KEY` of at least 32 characters.
3. Set `APP_PASSWORD` and `REQUIRE_AUTH=true` (or add real accounts).
4. Serve over HTTPS and keep `SESSION_COOKIE_SECURE=true`.
5. Use a single gunicorn worker or move rate limiting to Redis.
6. Review the CSP and the `X-Frame-Options`/HSTS headers in `config.py`.
7. Keep `.env`, databases, backups, and raw audio out of version control.

## Known deployment debt

- Flask 2.0 / Werkzeug 2.0 / SQLAlchemy 1.4 are pinned and need an upgrade path.
- The rate limiter is in-process, so multiple workers multiply limits.
- Push subscriptions are fetched server-side; validate endpoints before a
  public deployment.
- There is no license file yet. Choose one before accepting contributions.
