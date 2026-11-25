"""Regression coverage for the adversarial review findings."""

import re
from datetime import timedelta
from pathlib import Path

from app import db
from app.languages.seed import seed_amharic
from app.learning.analytics import retention_signal, weekly_recap
from app.learning.scheduler import utcnow
from app.learning.service import get_or_create_local_user, new_cards_seen_today
from app.models import ContentReport, Item, ReviewCard, ReviewLog
from app.models_language import Language


def _seed_both(client, app):
    response = client.get("/ko/learn")
    response.close()
    with app.app_context():
        seed_amharic()


def _prefer(app, code):
    with app.app_context():
        user = get_or_create_local_user()
        language = Language.query.filter_by(code=code).one()
        user.target_language_id = language.id
        db.session.commit()
        return language.id


def test_unknown_language_prefixes_404(client):
    client.get("/ko/learn")

    assert client.get("/en/learn").status_code == 404
    assert client.get("/es/learn").status_code == 404


def test_unprefixed_pages_use_the_preferred_language(client, app):
    _seed_both(client, app)
    _prefer(app, "am")

    from flask import g, url_for

    with app.test_request_context("/design"):
        # Simulate a fresh request; Flask's test client can keep a previous
        # request's g.lang_code alive between calls.
        g.pop("lang_code", None)
        assert url_for("learn.today") == "/am/learn/"


def test_settings_select_follows_the_url_language(client, app):
    _seed_both(client, app)
    _prefer(app, "ko")

    page = client.get("/am/settings")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    start = html.index('id="settings-language"')
    block = html[start : start + 600]
    assert re.search(r'value="am"\s+selected', block)


def test_header_language_switch_clears_review_session(client):
    client.get("/ko/learn")
    with client.session_transaction() as session:
        session["review_mode"] = 3
        session["review_limit"] = 4
        session["review_count"] = 2

    response = client.post("/language", data={"code": "ko"})

    assert response.status_code == 302
    with client.session_transaction() as session:
        assert "review_mode" not in session
        assert "review_limit" not in session
        assert "review_count" not in session


def test_legacy_new_conversation_preserves_the_path(client):
    client.get("/ko/learn")

    response = client.get("/conversations/new")

    assert response.status_code == 301
    assert response.headers["Location"].endswith("/ko/conversations/new")


def test_amharic_teacher_redirects_to_today(client, app):
    _seed_both(client, app)
    _prefer(app, "am")

    response = client.get("/am/learn/teacher")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/am/learn/")


def test_manifest_has_no_hardcoded_language_urls():
    manifest = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "static"
        / "manifest.webmanifest"
    ).read_text()

    assert '"/ko/' not in manifest
    assert '"/am/' not in manifest


def test_csp_allows_blob_media(client):
    response = client.get("/ko/learn")

    assert "media-src 'self' blob:" in response.headers["Content-Security-Policy"]


def test_accept_without_a_matching_suggestion_does_not_mark_checked(
    client, app, runner
):
    client.get("/ko/learn")
    with app.app_context():
        item = Item.query.order_by(Item.id.asc()).first()
        item_id = item.id

    client.post(
        "/api/content-reports",
        json={
            "surface": "review",
            "item_id": item_id,
            "kind": "meaning",
            "suggested_text": "완전히 다른 문장",
        },
    )
    with app.app_context():
        report_id = ContentReport.query.one().id

    result = runner.invoke(
        args=["content-report-close", str(report_id), "--status", "accepted"]
    )

    assert result.exit_code == 0, result.output
    assert "Not marking native-checked" in result.output
    with app.app_context():
        assert db.session.get(Item, item_id).review_status == "unchecked"

    rerun = runner.invoke(
        args=["content-report-close", str(report_id), "--status", "rejected"]
    )
    assert rerun.exit_code != 0


def test_new_card_cap_is_language_scoped(client, app):
    client.get("/ko/learn")
    with app.app_context():
        korean = Language.query.filter_by(code="ko").one()
        card_ids = [
            card.id
            for card in ReviewCard.query.filter(
                ReviewCard.item.has(Item.language_id == korean.id)
            )
            .limit(10)
            .all()
        ]

    for card_id in card_ids:
        client.post(f"/ko/learn/review/{card_id}", data={"rating": "3"})

    with app.app_context():
        user = get_or_create_local_user()
        assert new_cards_seen_today(user.id, language_id=korean.id) == 10

    with app.app_context():
        seed_amharic()
        amharic = Language.query.filter_by(code="am").one()
        user = get_or_create_local_user()
        user.target_language_id = amharic.id
        db.session.commit()
        amharic_card = ReviewCard.query.filter(
            ReviewCard.item.has(Item.language_id == amharic.id),
            ReviewCard.reps == 0,
        ).first()
        amharic_card_id = amharic_card.id

    response = client.post(
        f"/am/learn/review/{amharic_card_id}", data={"rating": "3"}
    )

    assert response.status_code == 302


def test_weekly_and_retention_are_language_scoped(client, app):
    _seed_both(client, app)
    with app.app_context():
        user = get_or_create_local_user()
        korean = Language.query.filter_by(code="ko").one()
        amharic = Language.query.filter_by(code="am").one()
        card = ReviewCard.query.filter(
            ReviewCard.item.has(Item.language_id == korean.id)
        ).first()
        now = utcnow()
        db.session.add_all(
            [
                ReviewLog(
                    card_id=card.id,
                    user_id=user.id,
                    rating=3,
                    reviewed_at=now,
                    was_new=True,
                ),
                ReviewLog(
                    card_id=card.id,
                    user_id=user.id,
                    rating=3,
                    reviewed_at=now - timedelta(days=8),
                    was_new=True,
                ),
            ]
        )
        db.session.commit()

        assert weekly_recap(user.id, language_id=korean.id)["reviews"] == 1
        assert weekly_recap(user.id, language_id=amharic.id)["reviews"] == 0
        assert retention_signal(
            user.id, language_id=korean.id
        )["total_delayed"] == 1
        assert retention_signal(
            user.id, language_id=amharic.id
        )["total_delayed"] == 0


def test_lookup_run_flag_is_one_shot(client):
    client.get("/ko/learn")

    first = client.get("/ko/translate?q=hello&run=1")
    second = client.get("/ko/translate?q=hello")

    assert b'data-run="1"' in first.data
    assert b'data-run="0"' in second.data


def test_content_report_rejects_a_non_string_lang(client):
    client.get("/ko/learn")

    response = client.post(
        "/api/content-reports",
        json={
            "lang": ["ko"],
            "surface": "review",
            "item_id": 1,
            "kind": "meaning",
        },
    )

    assert response.status_code == 400


def test_amharic_lookup_asks_who_you_are_speaking_to(client, app):
    _seed_both(client, app)
    _prefer(app, "am")

    page = client.get("/am/translate")

    assert page.status_code == 200
    assert b'id="addressee"' in page.data
    assert b"A woman" in page.data

    korean = client.get("/ko/translate")
    assert b'id="addressee"' not in korean.data


def test_amharic_progress_and_terms_hide_korean_only_actions(client, app):
    _seed_both(client, app)
    _prefer(app, "am")
    with app.app_context():
        user = get_or_create_local_user()
        user.goal = "topik"
        db.session.commit()

    progress = client.get("/am/learn/progress")
    assert b"/am/learn/scenes" not in progress.data

    library = client.get("/am/library")
    assert b"teacher call" not in library.data

    today = client.get("/am/learn")
    assert b"Topik path" not in today.data


def test_page_help_has_an_inline_first_visit_block(client):
    client.get("/ko/learn")

    page = client.get("/ko/translate")

    assert b'class="page-help-first"' in page.data
    assert b'data-first-visit-block="kiku-help-lookup"' in page.data
