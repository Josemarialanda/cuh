import io
from pathlib import Path

import pytest

from cuh.interpreter import run_source

EXAMPLES = Path(__file__).parent.parent / "examples"
EXIT_CODES = {"disrespect": 2, "spam": 3}


@pytest.mark.parametrize("path", sorted(EXAMPLES.glob("*.cuh")), ids=lambda p: p.stem)
def test_golden(path):
    buf = io.StringIO()
    code = run_source(path.read_text(), str(path), out=buf, err=buf)
    assert code == EXIT_CODES.get(path.stem, 0)
    assert buf.getvalue() == path.with_suffix(".out").read_text()
