"""The `main` blueprint: home, content, settings, PWA, and translation."""

from flask import Blueprint

main = Blueprint("main", __name__)

# Imported for their route registrations on ``main``.
from app.main import (  # noqa: F401
    content,
    conversations,
    design,
    home,
    settings,
    system,
    translate,
)
