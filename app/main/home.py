"""Home, language entry points, and legacy URL redirects."""

from flask import abort, redirect, render_template, request, session, url_for

from app import db
from app.languages.variants import default_register, register_choices
from app.learning.service import current_language, get_or_create_local_user
from app.main import main
from app.main.helpers import _check_csrf
from app.models_language import Language


@main.route("/")
def root():
    language = current_language()
    return redirect(
        url_for("main.home", lang_code=language.code if language else "ko")
    )


@main.route("/<lang_code>/")
def home():
    """The app home is Today, not the translation utility."""
    return redirect(url_for("learn.today"))


@main.route("/language", methods=["POST"])
def set_language():
    """Switch the learner's language from the header and land on Today."""
    _check_csrf()
    code = request.form.get("code")
    language = Language.query.filter_by(code=code, is_active=True).first()
    if language is None:
        abort(400, description="Unknown language")
    user = get_or_create_local_user()
    user.target_language_id = language.id
    for key in ("review_mode", "review_limit", "review_count"):
        session.pop(key, None)
    db.session.commit()
    return redirect(url_for("learn.today", lang_code=language.code))


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
@main.route("/conversations/<int:conversation_id>")
def legacy_conversations(conversation_id=None):
    if conversation_id is None:
        return _legacy_redirect("/conversations")
    return _legacy_redirect(f"/conversations/{conversation_id}")


@main.route("/conversations/new")
def legacy_new_conversation():
    return _legacy_redirect("/conversations/new")


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


@main.route("/<lang_code>/translate")
def index():
    language = current_language()
    code = language.code if language else "ko"
    return render_template(
        "index.html",
        language=language,
        q=(request.args.get("q") or "").strip()[:500],
        run=request.args.get("run") == "1",
        registers=register_choices(code),
        default_register=default_register(code),
    )
