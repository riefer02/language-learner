"""PWA files and operational endpoints."""

from flask import current_app, jsonify, render_template, send_from_directory
from sqlalchemy import text

from app import db
from app.main import main


@main.route("/offline")
def offline():
    return render_template("offline.html")


@main.route("/sw.js")
def service_worker():
    response = send_from_directory(
        current_app.static_folder, "sw.js", mimetype="application/javascript"
    )
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response


@main.route("/healthz")
def healthz():
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        current_app.logger.exception("Health check database probe failed")
        return jsonify({"status": "degraded", "database": "unavailable"}), 503
    return jsonify({"status": "ok"}), 200
