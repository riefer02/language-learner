"""Speech scoring and Sound Gym coverage."""

import io

from app import db
from app.models import Event, SpeechAttempt
from app.services.speech import score_transcript


def test_score_transcript_exact_and_partial(app):
    with app.app_context():
        exact = score_transcript("안녕하세요", "안녕하세요")
        partial = score_transcript("안녕하세요", "안녕하세")
        wrong = score_transcript("안녕하세요", "감사합니다")

        assert exact["acceptable"] is True
        assert exact["band"] == "clear"
        assert partial["match_score"] > 0.5
        assert wrong["acceptable"] is False
        assert wrong["band"] == "try_again"


def test_speech_score_route_records_attempt_and_no_audio(app, client):
    response = client.post(
        "/learn/api/speech-score",
        data={
            "target_text": "안녕하세요",
            "duration_ms": "1200",
            "audio": (io.BytesIO(b"fake-audio-bytes"), "answer.webm"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["transcript"] == "안녕하세요"
    assert payload["acceptable"] is True
    assert payload["match_score"] == 1.0
    with app.app_context():
        assert SpeechAttempt.query.count() == 1
        attempt = SpeechAttempt.query.first()
        assert attempt.target_text == "안녕하세요"
        assert attempt.transcript == "안녕하세요"
        assert attempt.duration_ms == 1200
        assert Event.query.filter_by(name="speech_attempt").count() == 1


def test_speech_score_requires_audio(client):
    response = client.post(
        "/learn/api/speech-score",
        data={"target_text": "안녕하세요"},
    )

    assert response.status_code == 400


def test_speech_score_rejects_non_korean_target(client):
    response = client.post(
        "/learn/api/speech-score",
        data={
            "target_text": "hello",
            "audio": (io.BytesIO(b"fake-audio"), "answer.webm"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400


def test_speech_score_returns_503_when_disabled(app, client):
    app.config["SPEECH_SCORING_ENABLED"] = False

    response = client.post(
        "/learn/api/speech-score",
        data={
            "target_text": "안녕하세요",
            "audio": (io.BytesIO(b"fake-audio"), "answer.webm"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 503


def test_metrics_cli_reports_activation(app, runner):
    from app.learning.analytics import record_event
    from app.learning.service import get_or_create_local_user

    with app.app_context():
        user = get_or_create_local_user()
        user.onboarding_complete = True
        db.session.commit()
        record_event(user.id, "review_submitted", rating=3)

    result = runner.invoke(args=["metrics"])

    assert result.exit_code == 0
    assert '"activation_rate": 1.0' in result.output
    assert '"users_with_reviews": 1' in result.output


def test_sound_gym_page_renders(client):
    response = client.get("/learn/sound-gym")

    assert response.status_code == 200
    assert b"Train your ear" in response.data
    assert b"Perception" in response.data
    assert b"Production" in response.data
    assert "불".encode() in response.data
