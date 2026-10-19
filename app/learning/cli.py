"""CLI commands for the learning loop."""

import click

from app.learning.seed_data import seed_content


def register_learning_cli(app):
    @app.cli.command("seed-content")
    def seed_content_command():
        """Insert the starter Korean content and create review cards."""
        user, created_items, created_cards = seed_content()
        click.echo(
            f"User {user.id}: added {created_items} item(s), "
            f"created {created_cards} review card(s)."
        )
