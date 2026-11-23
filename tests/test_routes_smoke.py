"""Route smoke tests.

These are intentionally shallow: they prove the app boots and that the API
contract for obvious bad input does not regress.  Failure paths that the
Platform/AI streams are actively fixing are marked ``xfail(strict=False)`` so
this suite documents the bug without blocking the rest of Phase 0.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_index_page_renders(client):
    response = client.get("/ko/translate")

    assert response.status_code == 200


def test_language_home_redirects_to_learn(client):
    response = client.get("/ko/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ko/learn/")


def test_root_redirects_to_a_language(client):
    response = client.get("/")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ko/")


def test_library_page_renders(client):
    response = client.get("/ko/library")

    assert response.status_code == 200


def test_conversations_page_renders(client):
    response = client.get("/ko/conversations")

    assert response.status_code == 200


def test_translate_with_empty_json_returns_400(client):
    response = client.post("/api/translate", json={})

    assert response.status_code == 400
    assert response.is_json
    assert "error" in response.get_json()


def test_translate_with_malformed_json_returns_400_or_415(client):
    response = client.post(
        "/api/translate",
        data="{this is not json",
        content_type="application/json",
    )

    assert response.status_code in (400, 415)


def test_conversation_without_prompt_returns_400(client):
    response = client.post("/api/conversation", json={})

    assert response.status_code == 400
    assert response.is_json
    assert "error" in response.get_json()


def test_missing_conversation_api_returns_404(client):
    response = client.get("/api/conversations/999999")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Static security check (P0-05)
# ---------------------------------------------------------------------------

JS_PATH = ROOT / "app" / "static" / "js" / "new_conversation.js"

# ``innerHTML = ""`` (and the single/backtick variants) is the safe way to
# clear a container, so those assignments are permitted.
_EMPTY_ASSIGNMENT = re.compile(r"""^(['"]{2}|`{2})$""")
_INNER_HTML_ASSIGNMENT = re.compile(
    r"\.(?:innerHTML|outerHTML)\s*=\s*(?P<value>[^;\n]*)"
)


# P0-05 guard: the renderer was migrated to createElement/textContent, so
# this assertion is now unconditional and will catch a regression.
def test_conversation_renderer_does_not_inject_api_data_via_inner_html():
    source = JS_PATH.read_text(encoding="utf-8")

    offenders = []
    for match in _INNER_HTML_ASSIGNMENT.finditer(source):
        value = match.group("value").strip()
        if not _EMPTY_ASSIGNMENT.match(value):
            offenders.append(match.group(0).strip())

    # ``insertAdjacentHTML`` is the same injection primitive under a new name.
    insert_adjacent = "insertAdjacentHTML" in source

    assert not offenders, (
        "new_conversation.js assigns non-empty markup through innerHTML/"
        f"outerHTML: {offenders}. Render model strings with textContent and "
        "createElement instead."
    )
    assert not insert_adjacent, (
        "new_conversation.js uses insertAdjacentHTML; render model strings "
        "with textContent/createElement instead."
    )


def test_navigation_has_brand_link_and_mobile_toggle(client):
    page = client.get("/ko/learn")
    assert b'class="brand"' in page.data
    assert b'id="nav-toggle"' in page.data
    assert b'aria-controls="primary-nav"' in page.data
    assert b'id="primary-nav"' in page.data


def test_design_system_page_renders(client):
    page = client.get("/design")
    assert page.status_code == 200
    assert b"Design system" in page.data
    assert b"--primary" in page.data
