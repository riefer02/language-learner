"""Home, language entry points, and legacy URL redirects."""

from flask import redirect, render_template, url_for

from app.learning.service import current_language
from app.main import main


@main.route("/")
def root():
    language = current_language()
    return redirect(
        url_for("main.index", lang_code=language.code if language else "ko")
    )


def _default_language_code():
    language = current_language()
    return language.code if language else "ko"


def _legacy_redirect(path):
    return redirect(f"/{_default_language_code()}{path}", code=301)


@main.route("/settings")
def legacy_settings():
    return _legacy_redirect("/settings")


@main.route("/library")
def legacy_library():
    return _legacy_redirect("/library")


@main.route("/dictionary")
def legacy_dictionary():
    return _legacy_redirect("/dictionary")


@main.route("/resources")
def legacy_resources():
    return _legacy_redirect("/resources")


@main.route("/conversations")
@main.route("/conversations/new")
@main.route("/conversations/<int:conversation_id>")
def legacy_conversations(conversation_id=None):
    if conversation_id is None:
        return _legacy_redirect("/conversations")
    return _legacy_redirect(f"/conversations/{conversation_id}")


@main.route("/learn")
@main.route("/learn/<path:rest>")
def legacy_learn(rest=""):
    suffix = f"/learn/{rest}" if rest else "/learn"
    return _legacy_redirect(suffix)


@main.route("/welcome")
@main.route("/welcome/<path:rest>")
def legacy_welcome(rest=""):
    suffix = f"/welcome/{rest}" if rest else "/welcome"
    return _legacy_redirect(suffix)


@main.route("/<lang_code>/")
def index():
    language = current_language()
    return render_template("index.html", language=language)
