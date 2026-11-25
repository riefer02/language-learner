"""Style contract: the token migration may only get better.

The budgets are deliberate. If a change reduces the raw-color or raw-px count,
lower the budget in the same commit. New UI should use the semantic tokens in
``:root`` and the spacing/type scales, not add another hex value or pixel.
"""

import re
from collections import Counter
from pathlib import Path

CSS_PATH = Path(__file__).resolve().parents[1] / "app" / "static" / "css" / "style.css"
TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "app" / "templates"

# Current debt after the first token sweep. These may go down, never up.
MAX_UNIQUE_HEX = 14
MAX_HEX_DECLARATIONS = 19
MAX_RAW_PX = 508


def _split_root():
    css = CSS_PATH.read_text()
    end = css.index("}", css.index(":root"))
    return css[: end + 1], css[end + 1 :]


def _outside_root():
    return _split_root()[1]


def test_raw_colors_do_not_grow():
    outside = _outside_root()
    hexes = re.findall(r"#[0-9a-fA-F]{3,8}\b", outside)

    assert len({h.lower() for h in hexes}) <= MAX_UNIQUE_HEX
    assert len(hexes) <= MAX_HEX_DECLARATIONS


def test_raw_pixels_do_not_grow():
    outside = _outside_root()

    assert len(re.findall(r"(?<![\w-])\d+px", outside)) <= MAX_RAW_PX


def test_no_hardcoded_asset_versions():
    for template in TEMPLATE_DIR.glob("*.html"):
        text = template.read_text()
        assert "?v=20" not in text, f"{template.name} hardcodes an asset version"


def test_no_duplicate_top_level_selectors():
    css, _ = _split_root()
    selectors = Counter(
        match.strip()
        for match in re.findall(r"(?m)^([^\s@/{}][^{}]*)\{", css)
    )
    duplicates = [
        selector
        for selector, count in selectors.items()
        if count > 1 and len(selector) < 100
    ]

    assert duplicates == []
