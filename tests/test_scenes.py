"""Scene roleplay flow: progress, tolerant matching, and debrief cards."""

from app.learning.scene_data import SCENES
from app.learning.scenes import get_scene
from app.models import Event, Item, ReviewCard, SceneSession


def test_scene_list_renders(client):
    response = client.get("/learn/scenes")

    assert response.status_code == 200
    assert b"Use Korean before you feel ready" in response.data
    assert "Order at a café".encode() in response.data


def test_scene_start_renders_first_character_line(client):
    response = client.get("/learn/scenes/cafe-order")

    assert response.status_code == 200
    assert b"Step 1 of 3" in response.data
    assert "어서 오세요".encode() in response.data


def test_correct_answer_advances_scene(client, app):
    scene = get_scene("cafe-order")
    client.get("/learn/scenes/cafe-order")

    response = client.post(
        "/learn/scenes/cafe-order/answer",
        data={"answer": scene["steps"][0]["expected"][0]},
    )

    assert response.status_code == 302
    with app.app_context():
        session = SceneSession.query.filter_by(scene_slug="cafe-order").first()
        assert session.step_index == 1
        assert session.completed is False


def test_incorrect_answer_keeps_step_and_shows_hint(client, app):
    client.get("/learn/scenes/cafe-order")

    response = client.post(
        "/learn/scenes/cafe-order/answer",
        data={"answer": "hello"},
    )

    assert response.status_code == 200
    assert b"Not quite" in response.data
    with app.app_context():
        session = SceneSession.query.filter_by(scene_slug="cafe-order").first()
        assert session.step_index == 0


def test_completing_scene_creates_cards_and_debrief(client, app):
    scene = get_scene("cafe-order")
    client.get("/learn/scenes/cafe-order")
    with app.app_context():
        items_before = Item.query.count()
        cards_before = ReviewCard.query.count()

    for step in scene["steps"]:
        response = client.post(
            "/learn/scenes/cafe-order/answer",
            data={"answer": step["expected"][0]},
        )
        assert response.status_code == 302

    response = client.get("/learn/scenes/cafe-order")

    assert response.status_code == 200
    assert b"What went well" in response.data
    assert b"Cards added to your review queue" in response.data
    with app.app_context():
        session = SceneSession.query.filter_by(scene_slug="cafe-order").first()
        assert session.completed is True
        assert Item.query.count() == items_before + 3
        assert ReviewCard.query.count() == cards_before + 3
        assert Event.query.filter_by(name="scene_completed").count() == 1


def test_reset_scene_starts_over(client, app):
    scene = get_scene("cafe-order")
    client.get("/learn/scenes/cafe-order")
    client.post(
        "/learn/scenes/cafe-order/answer",
        data={"answer": scene["steps"][0]["expected"][0]},
    )

    response = client.post("/learn/scenes/cafe-order/reset")

    assert response.status_code == 302
    with app.app_context():
        session = SceneSession.query.filter_by(scene_slug="cafe-order").first()
        assert session.step_index == 0
        assert session.completed is False


def test_unknown_scene_returns_404(client):
    response = client.get("/learn/scenes/not-a-scene")

    assert response.status_code == 404


def test_all_scene_slugs_are_reachable(client):
    for scene in SCENES:
        response = client.get(f"/learn/scenes/{scene['slug']}")
        assert response.status_code == 200
