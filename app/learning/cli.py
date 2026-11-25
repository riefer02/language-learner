"""CLI commands for the learning loop."""

import json
import uuid
from datetime import UTC, datetime

import click
from flask import current_app

from app import db
from app.learning.analytics import metrics_summary
from app.learning.seed_data import seed_content
from app.models import ContentReport, Item
from app.models_language import Language
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

    @app.cli.command("seed-amharic")
    def seed_amharic_command():
        """Insert the starter Amharic deck and fidel content metadata."""
        from app.languages.seed import seed_amharic

        result = seed_amharic()
        click.echo(
            f"Amharic language {result['language_id']}: "
            f"{result['created_items']} new item(s), "
            f"{result['total_items']} total, "
            f"{result['created_cards']} review card(s)."
        )

    @app.cli.command("metrics")
    def metrics_command():
        """Print the alpha activation and retention summary."""
        click.echo(json.dumps(metrics_summary(), indent=2))

    @app.cli.command("language-audit")
    def language_audit_command():
        """Report legacy-to-language-core backfill coverage."""
        from app.models import Conversation, Event, Item, Phrase, User
        from app.models_language import ItemForm, ItemGloss, Language

        languages = Language.query.order_by(Language.code.asc()).all()
        items = Item.query.all()
        untagged_items = sum(1 for item in items if item.language_id is None)
        items_without_form = sum(1 for item in items if not item.forms)
        items_without_gloss = sum(1 for item in items if not item.glosses)

        payload = {
            "languages": [
                {"code": language.code, "active": language.is_active}
                for language in languages
            ],
            "items": len(items),
            "items_untagged": untagged_items,
            "items_without_primary_form": items_without_form,
            "items_without_gloss": items_without_gloss,
            "item_forms": ItemForm.query.count(),
            "item_glosses": ItemGloss.query.count(),
            "phrases_untagged": Phrase.query.filter(
                Phrase.target_language_id.is_(None)
            ).count(),
            "conversations_untagged": Conversation.query.filter(
                Conversation.language_id.is_(None)
            ).count(),
            "users_untagged": User.query.filter(
                User.target_language_id.is_(None)
            ).count(),
            "events_untagged": Event.query.filter(
                Event.language_id.is_(None)
            ).count(),
        }
        click.echo(json.dumps(payload, indent=2))

    @app.cli.command("content-reports")
    @click.option(
        "--status",
        "report_status",
        default="open",
        show_default=True,
        type=click.Choice(["open", "accepted", "rejected", "all"]),
    )
    @click.option("--limit", default=50, show_default=True, type=int)
    def content_reports_command(report_status, limit):
        """List learner-flagged content corrections."""
        query = ContentReport.query
        if report_status != "all":
            query = query.filter(ContentReport.status == report_status)
        reports = (
            query.order_by(
                ContentReport.created_at.desc(), ContentReport.id.desc()
            )
            .limit(max(1, limit))
            .all()
        )
        if not reports:
            click.echo("No content reports.")
            return
        for report in reports:
            click.echo(
                f"#{report.id} [{report.status}] "
                f"{report.surface}/{report.kind}"
            )
            click.echo(f"  shown:    {report.snapshot_text or '(none)'}")
            if report.suggested_text:
                click.echo(f"  suggest:  {report.suggested_text}")
            if report.context:
                click.echo(f"  context:  {report.context}")
            if report.note:
                click.echo(f"  note:     {report.note}")
            if report.item_id:
                click.echo(f"  item:     #{report.item_id}")
            if report.phrase_id:
                click.echo(f"  phrase:   #{report.phrase_id}")
            if report.scene_slug:
                click.echo(
                    f"  scene:    {report.scene_slug} step {report.step_index}"
                )
            if report.resolution_note:
                click.echo(f"  resolved: {report.resolution_note}")

    @app.cli.command("content-report-close")
    @click.argument("report_id", type=int)
    @click.option(
        "--status",
        "decision",
        required=True,
        type=click.Choice(["accepted", "rejected"]),
    )
    @click.option("--note", "resolution_note", default=None)
    def content_report_close_command(report_id, decision, resolution_note):
        """Mark a content report accepted or rejected.

        Accepting a report attached to an item marks that item native-checked.
        It does not rewrite the text; edit the item (and clear cached audio when
        the target text changed) as a separate, deliberate step.
        """
        report = db.session.get(ContentReport, report_id)
        if report is None:
            raise click.ClickException(f"No content report #{report_id}.")
        report.status = decision
        report.resolved_at = datetime.now(UTC)
        if resolution_note:
            report.resolution_note = resolution_note.strip()[:1000]

        if decision == "accepted" and report.item_id:
            item = db.session.get(Item, report.item_id)
            if item is not None and report.kind != "audio":
                item.review_status = "native_checked"
                item.reviewed_at = datetime.now(UTC)
                if (
                    report.suggested_text
                    and report.suggested_text != item.target_text
                ):
                    click.echo(
                        "Note: the suggestion differs from the current target "
                        "text. Review the item and, if target_text changed, "
                        "clear audio_path, then run `flask generate-item-audio`."
                    )
        db.session.commit()
        click.echo(f"Report #{report.id} marked {report.status}.")

    @app.cli.command("content-check")
    @click.argument("item_id", type=int)
    @click.option(
        "--uncheck", is_flag=True, help="Clear a previous native-check."
    )
    def content_check_command(item_id, uncheck):
        """Mark an item as confirmed by a native speaker, or clear it."""
        item = db.session.get(Item, item_id)
        if item is None:
            raise click.ClickException(f"No item #{item_id}.")
        item.review_status = "unchecked" if uncheck else "native_checked"
        item.reviewed_at = None if uncheck else datetime.now(UTC)
        db.session.commit()
        click.echo(f"Item #{item.id} is {item.review_status}.")

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
    @click.option(
        "--language",
        "language_code",
        default=None,
        help="Only items in this language code (e.g. ko, am).",
    )
    def generate_item_audio(limit, voice, force, dry_run, language_code):
        """Pre-generate cached audio for review items.

        This is intentionally a separate, explicit command: it spends API
        credits, so it never runs as part of seeding or app startup.
        """
        query = Item.query
        if language_code:
            language = Language.query.filter_by(code=language_code).first()
            if language is None:
                raise click.ClickException(
                    f"Unknown language code: {language_code}"
                )
            query = query.filter(Item.language_id == language.id)
        items = [
            item
            for item in query.order_by(Item.id.asc()).all()
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
                click.echo(f"  {item.id}: {item.target_text} — {item.gloss}")
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
                    f"{safe_audio_filename(item.gloss, max_length=20)}_"
                    f"{uuid.uuid4().hex[:6]}.mp3"
                )
                staged = batch.path(filename)
                language = (
                    db.session.get(Language, item.language_id)
                    if item.language_id
                    else None
                )
                generate_audio(
                    item.target_text,
                    staged,
                    voice=voice,
                    language_code=language.code if language else "ko",
                )
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
                click.echo(f"  {item.id}: {item.target_text} → {filename}")

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
