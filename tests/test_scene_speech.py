"""Voice answers inside mission scenes."""

import io

from app.learning.scene_data import SCENES
from app.models import SceneSession, SpeechAttempt


class _Transcription:
    def __init__(self, text):
        self.text = text


class _Transcriptions:
    def __init__(self, text):
        self.text = text

    def create(self, **_kwargs):
        return _Transcription(self.text)


class _Audio:
    def __init__(self, text):
        self.transcriptions = _Transcriptions(text)


class _Client:
    def __init__(self, text):
        self.audio = _Audio(text)


def _post_audio(client, slug, text):
    return client.post(
        f"/ko/learn/scenes/{slug}/speak",
        data={"audio": (io.BytesIO(b"fake-audio"), "answer.webm")},
        content_type="multipart/form-data",
    )


def test_scene_speech_accepts_matching_transcript(app, client):
    scene = SCENES[0]
    client.get(f"/ko/learn/scenes/{scene['slug']}")
    app.extensions["openai_client"] = _Client(scene["steps"][0]["expected"][0])

    response = _post_audio(client, scene["slug"], "hello")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["accepted"] is True
    assert payload["step_index"] == 1
    with app.app_context():
        session = SceneSession.query.filter_by(scene_slug=scene["slug"]).first()
        assert session.step_index == 1
        assert SpeechAttempt.query.count() == 1
        assert SpeechAttempt.query.first().acceptable is True


def test_scene_speech_rejects_wrong_transcript(app, client):
    scene = SCENES[0]
    client.get(f"/ko/learn/scenes/{scene['slug']}")
    app.extensions["openai_client"] = _Client("안녕하세요")

    response = _post_audio(client, scene["slug"], "hello")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["accepted"] is False
    assert payload["hint"]
    with app.app_context():
        session = SceneSession.query.filter_by(scene_slug=scene["slug"]).first()
        assert session.step_index == 0
        assert SpeechAttempt.query.count() == 1
        assert SpeechAttempt.query.first().acceptable is False


def test_scene_speech_returns_503_when_disabled(app, client):
    app.config["SPEECH_SCORING_ENABLED"] = False
    scene = SCENES[0]
    client.get(f"/ko/learn/scenes/{scene['slug']}")

    response = _post_audio(client, scene["slug"], "hello")

    assert response.status_code == 503


def test_scene_speech_requires_audio(client):
    scene = SCENES[0]
    client.get(f"/ko/learn/scenes/{scene['slug']}")

    response = client.post(f"/ko/learn/scenes/{scene['slug']}/speak", data={})

    assert response.status_code == 400
