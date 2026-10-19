"""First-run onboarding: goal, time, experience, and a first spoken sentence."""

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_wtf.csrf import validate_csrf
from werkzeug.exceptions import BadRequest

from app import db
from app.learning.analytics import record_event
from app.learning.service import get_or_create_local_user

onboarding = Blueprint(
    "onboarding", __name__, url_prefix="/welcome"
)

GOALS = [
    {
        "value": "everyday",
        "label": "Everyday Korean",
        "hint": "Cafés, directions, friends, daily life",
    },
    {
        "value": "travel",
        "label": "Travel",
        "hint": "Airports, hotels, restaurants, emergencies",
    },
    {
        "value": "work",
        "label": "Work",
        "hint": "Meetings, email, honorifics, colleagues",
    },
    {
        "value": "culture",
        "label": "K-drama & music",
        "hint": "Understand dialogue and lyrics",
    },
    {
        "value": "topik",
        "label": "TOPIK",
        "hint": "Exam skills, reading, writing",
    },
    {
        "value": "family",
        "label": "Family & heritage",
        "hint": "Speak with family and reconnect",
    },
]

TIMES = [
    {"value": 3, "label": "3 minutes", "hint": "A minimum day"},
    {"value": 10, "label": "10 minutes", "hint": "The daily loop"},
    {"value": 25, "label": "25 minutes", "hint": "Deep practice"},
]

EXPERIENCE = [
    {
        "value": "new",
        "label": "I'm completely new",
        "hint": "Start with Hangul and survival phrases",
    },
    {
        "value": "hangul",
        "label": "I know some Hangul",
        "hint": "You can decode, but speaking is new",
    },
    {
        "value": "some",
        "label": "I can handle some conversation",
        "hint": "You know phrases and basic grammar",
    },
    {
        "value": "intermediate",
        "label": "I'm intermediate",
        "hint": "You want to fix gaps and speak more",
    },
]

GOAL_VALUES = {goal["value"] for goal in GOALS}
TIME_VALUES = {time["value"] for time in TIMES}
EXPERIENCE_VALUES = {item["value"] for item in EXPERIENCE}


def _check_csrf():
    if current_app.config.get("WTF_CSRF_ENABLED", True):
        try:
            validate_csrf(request.form.get("csrf_token"))
        except Exception as error:
            raise BadRequest("Invalid or missing CSRF token") from error


def _valid_timezone(value):
    try:
        ZoneInfo(value)
        return value
    except (KeyError, ValueError, ZoneInfoNotFoundError):
        return "UTC"


def _user():
    return get_or_create_local_user()


@onboarding.route("/", methods=["GET", "POST"], strict_slashes=False)
def welcome():
    user = _user()
    if user.onboarding_complete:
        return redirect(url_for("learn.today"))

    error = None
    if request.method == "POST":
        _check_csrf()
        goal = request.form.get("goal", "")
        experience = request.form.get("experience", "")
        daily_minutes = request.form.get("daily_minutes", type=int)
        timezone = _valid_timezone(request.form.get("timezone") or "UTC")

        if goal not in GOAL_VALUES:
            error = "Choose a learning goal."
        elif daily_minutes not in TIME_VALUES:
            error = "Choose a daily practice time."
        elif experience not in EXPERIENCE_VALUES:
            error = "Choose your starting point."
        else:
            user.goal = goal
            user.daily_minutes = daily_minutes
            user.experience = experience
            user.timezone = timezone
            db.session.commit()
            record_event(
                user.id,
                "onboarding_profile_saved",
                goal=goal,
                daily_minutes=daily_minutes,
                experience=experience,
            )
            return redirect(url_for("onboarding.first_word"))

    return render_template(
        "welcome.html",
        goals=GOALS,
        times=TIMES,
        experience_options=EXPERIENCE,
        error=error,
        user=user,
    )


@onboarding.route("/first-word")
def first_word():
    user = _user()
    if user.onboarding_complete:
        return redirect(url_for("learn.today"))
    return render_template("welcome_first_word.html", user=user)


@onboarding.route("/complete", methods=["POST"])
def complete():
    _check_csrf()
    user = _user()
    user.onboarding_complete = True
    db.session.commit()
    record_event(user.id, "onboarding_complete")
    return redirect(url_for("learn.today"))
