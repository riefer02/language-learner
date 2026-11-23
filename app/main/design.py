"""A live, local style guide for the Kiku design system."""

from flask import render_template

from app.main import main


@main.route("/design")
def design():
    return render_template("design.html")
