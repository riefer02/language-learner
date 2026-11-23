"""Resources search and reference surface."""

def test_resources_page_renders(client):
    client.get("/ko/learn")

    response = client.get("/ko/resources")

    assert response.status_code == 200
    assert b"Look it up. Then use it." in response.data
    assert b"Hangul bootcamp" in response.data
    assert b"Phrase library" in response.data


def test_resources_searches_korean_and_english(client, app):
    client.get("/ko/learn")

    korean = client.get("/ko/resources?q=커피")
    english = client.get("/ko/resources?q=coffee")

    assert korean.status_code == 200
    assert "커피".encode() in korean.data
    assert english.status_code == 200
    assert b"coffee" in english.data.lower()


def test_resources_filters_by_type_and_level(client, app):
    client.get("/ko/learn")

    grammar = client.get("/ko/resources?type=grammar")
    level_two = client.get("/ko/resources?level=2")

    assert grammar.status_code == 200
    assert "은/는".encode() in grammar.data
    assert b"level 2" in level_two.data.lower()


def test_resources_empty_state(client):
    client.get("/ko/learn")

    response = client.get("/ko/resources?q=zzzz-not-in-deck")

    assert response.status_code == 200
    assert b"No matches yet" in response.data


def test_nav_uses_resources_and_scenes_not_legacy_tools(client):
    response = client.get("/ko/learn")

    assert b"Scenes" in response.data
    assert b"Resources" in response.data
    assert b"New Phrase" not in response.data
    assert b">Library<" not in response.data
