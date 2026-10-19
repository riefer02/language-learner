"""Onboarding and Hangul bootcamp coverage."""

from app.models import User


def _enable_onboarding(app):
    app.config["ONBOARDING_ENABLED"] = True


def test_learn_redirects_to_welcome_on_first_run(app, client):
    _enable_onboarding(app)

    response = client.get("/learn")

    assert response.status_code == 302
    assert "/welcome" in response.headers["Location"]


def test_welcome_page_renders_choices(app, client):
    _enable_onboarding(app)

    response = client.get("/welcome")

    assert response.status_code == 200
    assert b"What do you want Korean to do for you?" in response.data
    assert b"Everyday Korean" in response.data
    assert b"10 minutes" in response.data


def test_welcome_post_saves_profile(app, client):
    _enable_onboarding(app)

    response = client.post(
        "/welcome",
        data={
            "goal": "travel",
            "daily_minutes": "25",
            "experience": "some",
            "timezone": "Asia/Seoul",
        },
    )

    assert response.status_code == 302
    assert "/welcome/first-word" in response.headers["Location"]
    with app.app_context():
        user = User.query.first()
        assert user.goal == "travel"
        assert user.daily_minutes == 25
        assert user.experience == "some"
        assert user.timezone == "Asia/Seoul"
        assert user.onboarding_complete is False


def test_welcome_rejects_invalid_goal(app, client):
    _enable_onboarding(app)

    response = client.post(
        "/welcome",
        data={
            "goal": "not-a-goal",
            "daily_minutes": "10",
            "experience": "new",
            "timezone": "UTC",
        },
    )

    assert response.status_code == 200
    assert b"Choose a learning goal" in response.data


def test_first_word_page_and_completion(app, client):
    _enable_onboarding(app)
    client.post(
        "/welcome",
        data={
            "goal": "everyday",
            "daily_minutes": "10",
            "experience": "new",
            "timezone": "UTC",
        },
    )

    page = client.get("/welcome/first-word")
    assert page.status_code == 200
    assert "안녕하세요".encode() in page.data
    assert b"Record yourself" in page.data

    complete = client.post("/welcome/complete")

    assert complete.status_code == 302
    assert complete.headers["Location"].endswith("/learn/")
    with app.app_context():
        assert User.query.first().onboarding_complete is True


def test_onboarding_post_requires_csrf_when_enabled(app, client):
    _enable_onboarding(app)
    app.config["WTF_CSRF_ENABLED"] = True

    response = client.post(
        "/welcome",
        data={
            "goal": "everyday",
            "daily_minutes": "10",
            "experience": "new",
            "timezone": "UTC",
        },
    )

    assert response.status_code == 400


def test_hangul_index_and_lessons(client):
    index = client.get("/learn/hangul")

    assert index.status_code == 200
    assert b"Hangul bootcamp" in index.data
    assert b"Read Korean by Sunday" in index.data

    lesson = client.get("/learn/hangul/letters")

    assert lesson.status_code == 200
    assert b"The 14 basic consonants" in lesson.data
    assert b"data-answer" in lesson.data


def test_unknown_hangul_lesson_returns_404(client):
    response = client.get("/learn/hangul/not-a-lesson")

    assert response.status_code == 404
