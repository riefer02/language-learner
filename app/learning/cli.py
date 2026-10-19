"""CLI commands for the learning loop."""

import uuid

import click
from flask import current_app

from app import db
from app.learning.seed_data import seed_content
from app.models import Item
from app.services.audio import generate_audio
from app.utils.media import AudioBatch, remove_files, safe_audio_filename


def register_learning_cli(app):
    @app.cli.command("seed-content")
    def seed_content_command():
        """Insert the starter Korean content and create review cards."""
        user, created_items, created_cards = seed_content()
        click.echo(
            f"User {user.id}: added {created_items} item(s), "
            f"created {created_cards} review card(s)."
        )

    @app.cli.command("generate-item-audio")
    @click.option("--limit", default=0, type=int, help="Only process N items.")
    @click.option("--voice", default=None, help="Override the configured TTS voice.")
    @click.option(
        "--force",
        is_flag=True,
        help="Regenerate audio even when an item already has a file.",
    )
    @click.option(
        "--dry-run",
        is_flag=True,
        help="List what would be generated without calling the API.",
    )
    def generate_item_audio(limit, voice, force, dry_run):
        """Pre-generate cached audio for review items.

        This is intentionally a separate, explicit command: it spends API
        credits, so it never runs as part of seeding or app startup.
        """
        items = [
            item
            for item in Item.query.order_by(Item.id.asc()).all()
            if force or not item.audio_path
        ]
        if limit and limit > 0:
            items = items[:limit]

        if not items:
            click.echo("No items need audio.")
            return

        voice = voice or current_app.config.get("TTS_VOICE_1", "onyx")
        if dry_run:
            click.echo(
                f"Dry run: would generate {len(items)} item(s) with voice {voice}."
            )
            for item in items:
                click.echo(f"  {item.id}: {item.korean} — {item.english}")
            return

        audio_dir = current_app.config["AUDIO_DIR"]
        batch = AudioBatch(current_app.config["MEDIA_TMP_DIR"])
        pending = []
        generated = 0
        try:
            for item in items:
                pending = []
                filename = (
                    f"item_{item.id}_"
                    f"{safe_audio_filename(item.english, max_length=20)}_"
                    f"{uuid.uuid4().hex[:6]}.mp3"
                )
                staged = batch.path(filename)
                generate_audio(item.korean, staged, voice=voice)
                pending = batch.commit_to(
                    audio_dir, [(staged, filename)]
                )
                old_path = item.audio_path
                item.audio_path = f"/static/audio/{filename}"
                db.session.add(item)
                db.session.commit()
                # The file is referenced now; do not include it in rollback.
                pending = []
                generated += 1
                click.echo(f"  {item.id}: {item.korean} → {filename}")

                if old_path and old_path != item.audio_path:
                    old_file = old_path.rsplit("/", 1)[-1]
                    remove_files([f"{audio_dir}/{old_file}"])
        except Exception as error:
            db.session.rollback()
            remove_files(pending)
            current_app.logger.exception("Item audio generation failed")
            raise click.ClickException(
                f"Audio generation failed after {generated} item(s): {error}"
            ) from error
        finally:
            batch.cleanup()

        click.echo(f"Generated audio for {generated} item(s).")
