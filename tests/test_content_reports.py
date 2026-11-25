"""Content reports: capture, scoping, CLI triage, and native-check provenance."""

from app import db
from app.learning.service import get_or_create_local_user
from app.models import ContentReport, Item
from app.models_language import Language


def _first_item_id(app):
    with app.app_context():
        item = Item.query.order_by(Item.id.asc()).first()
        return item.id, item.target_text


def test_content_report_captures_snapshot(client, app):
    client.get("/ko/learn")
    item_id, target = _first_item_id(app)

    response = client.post(
        "/api/content-reports",
        json={
            "surface": "review",
            "item_id": item_id,
            "kind": "register",
            "suggested_text": "괜찮습니다",
            "context": "to a shop clerk",
            "note": "A native speaker said this is safer.",
        },
    )

    assert response.status_code == 201
    assert response.get_json()["status"] == "open"
    with app.app_context():
        report = ContentReport.query.one()
        assert report.item_id == item_id
        assert report.snapshot_text == target
        assert report.surface == "review"
        assert report.kind == "register"
        assert report.suggested_text == "괜찮습니다"
        assert report.context == "to a shop clerk"
        assert report.status == "open"


def test_content_report_rejects_unknown_kind(client, app):
    client.get("/ko/learn")
    item_id, _target = _first_item_id(app)

    response = client.post(
        "/api/content-reports",
        json={"surface": "review", "item_id": item_id, "kind": "vibes"},
    )

    assert response.status_code == 400
    assert "issue kind" in response.get_json()["error"]
    with app.app_context():
        assert ContentReport.query.count() == 0


def test_content_report_rejects_item_from_another_language(client, app):
    client.get("/ko/learn")
    with app.app_context():
        language = Language(code="am", name="Amharic", native_name="አማርኛ")
        db.session.add(language)
        db.session.flush()
        item = Item(
            item_type="chunk",
            target_text="ሰላም",
            gloss="Hello",
            level=1,
            language_id=language.id,
        )
        db.session.add(item)
        db.session.commit()
        item_id = item.id

    response = client.post(
        "/api/content-reports",
        json={"surface": "library", "item_id": item_id, "kind": "meaning"},
    )

    assert response.status_code == 400
    assert "active language" in response.get_json()["error"]
    with app.app_context():
        assert ContentReport.query.count() == 0


def test_content_report_uses_page_language_over_preference(client, app):
    """A /ko/ page must report in Korean even when the learner prefers Amharic."""
    client.get("/ko/learn")
    with app.app_context():
        korean = Language.query.filter_by(code="ko").one()
        amharic = Language(code="am", name="Amharic", native_name="አማርኛ")
        db.session.add(amharic)
        db.session.flush()
        user = get_or_create_local_user()
        user.target_language_id = amharic.id
        db.session.commit()
        item_id = Item.query.filter_by(language_id=korean.id).first().id

    response = client.post(
        "/api/content-reports",
        json={
            "lang": "ko",
            "surface": "review",
            "item_id": item_id,
            "kind": "meaning",
        },
    )

    assert response.status_code == 201
    with app.app_context():
        assert ContentReport.query.one().language_id == korean.id


def test_content_report_cli_lists_and_accepts(client, app, runner):
    client.get("/ko/learn")
    item_id, _target = _first_item_id(app)
    client.post(
        "/api/content-reports",
        json={
            "surface": "review",
            "item_id": item_id,
            "kind": "meaning",
        },
    )

    listed = runner.invoke(args=["content-reports"])
    assert listed.exit_code == 0, listed.output
    assert "review/meaning" in listed.output

    with app.app_context():
        report_id = ContentReport.query.one().id

    closed = runner.invoke(
        args=[
            "content-report-close",
            str(report_id),
            "--status",
            "accepted",
            "--note",
            "native confirmed",
        ]
    )
    assert closed.exit_code == 0, closed.output

    with app.app_context():
        report = db.session.get(ContentReport, report_id)
        item = db.session.get(Item, item_id)
        assert report.status == "accepted"
        assert report.resolved_at is not None
        assert report.resolution_note == "native confirmed"
        assert item.review_status == "native_checked"


def test_content_check_marks_item(client, app, runner):
    client.get("/ko/learn")
    item_id, _target = _first_item_id(app)

    result = runner.invoke(args=["content-check", str(item_id)])
    assert result.exit_code == 0, result.output
    with app.app_context():
        assert db.session.get(Item, item_id).review_status == "native_checked"

    cleared = runner.invoke(args=["content-check", str(item_id), "--uncheck"])
    assert cleared.exit_code == 0, cleared.output
    with app.app_context():
        assert db.session.get(Item, item_id).review_status == "unchecked"


def test_review_shows_native_checked_provenance(client, app):
    client.get("/ko/learn")
    with app.app_context():
        for item in Item.query.all():
            item.review_status = "native_checked"
        db.session.commit()

    response = client.get("/ko/learn/review")

    assert response.status_code == 200
    assert b"Native-checked" in response.data
    assert b"Something's off?" in response.data
    assert b'name="lang" value="ko"' in response.data


def test_audio_report_does_not_mark_text_native_checked(client, app, runner):
    client.get("/ko/learn")
    item_id, _target = _first_item_id(app)
    client.post(
        "/api/content-reports",
        json={"surface": "review", "item_id": item_id, "kind": "audio"},
    )
    with app.app_context():
        report_id = ContentReport.query.one().id

    closed = runner.invoke(
        args=["content-report-close", str(report_id), "--status", "accepted"]
    )

    assert closed.exit_code == 0, closed.output
    with app.app_context():
        assert db.session.get(Item, item_id).review_status == "unchecked"


def test_review_shows_starter_content_when_unchecked(client, app):
    client.get("/ko/learn")

    response = client.get("/ko/learn/review")

    assert response.status_code == 200
    assert b"Starter content" in response.data


def test_library_offers_content_flag_for_saved_term(client, app):
    client.get("/ko/learn")
    item_id, _target = _first_item_id(app)
    client.post(f"/ko/dictionary/{item_id}/save", data={})

    response = client.get("/ko/library")

    assert response.status_code == 200
    assert b"Something's off?" in response.data
