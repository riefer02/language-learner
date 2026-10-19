"""Time-boxed review sessions."""

from app.models import ReviewCard, ReviewLog


def test_today_offers_session_modes(client):
    response = client.get("/learn")

    assert response.status_code == 200
    assert b"3 min" in response.data
    assert b"10 min" in response.data
    assert b"25 min" in response.data


def test_session_stops_at_limit_and_can_continue(app, client):
    app.config["REVIEW_SESSION_LIMITS"] = {3: 2, 10: 2, 25: 3}
    client.get("/learn/review?mode=3")
    with app.app_context():
        card_ids = [card.id for card in ReviewCard.query.limit(2).all()]

    first = client.post(f"/learn/review/{card_ids[0]}", data={"rating": "3"})
    second = client.post(f"/learn/review/{card_ids[1]}", data={"rating": "3"})

    assert first.status_code == 302
    assert second.status_code == 302
    assert "/review/complete" in second.headers["Location"]

    complete = client.get("/learn/review/complete")
    assert complete.status_code == 200
    assert b"Session complete" in complete.data
    assert b"3-minute block" in complete.data

    blocked = client.get("/learn/review")
    assert blocked.status_code == 302
    assert "/review/complete" in blocked.headers["Location"]

    continued = client.get("/learn/review?continue=1")
    assert continued.status_code == 200
    assert b"Show answer" in continued.data

    with app.app_context():
        assert ReviewLog.query.count() == 2
