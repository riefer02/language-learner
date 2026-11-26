"""Run the small Node contract tests for the Look up history helpers."""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_translate_state_javascript_contract():
    result = subprocess.run(
        ["node", "--test", "tests/js/translate_state.test.js"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
