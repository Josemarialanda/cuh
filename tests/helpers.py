import io
import textwrap

from cuh.interpreter import run_source


def run(src, seed=None, stdin="", path="<cuh>"):
    """Run a program; returns (exit code, combined stdout+stderr)."""
    buf = io.StringIO()
    code = run_source(textwrap.dedent(src).strip("\n") + "\n", path, out=buf, err=buf,
                      inp=io.StringIO(stdin), seed=seed)
    return code, buf.getvalue()


def ok(src, **kw):
    code, out = run(src, **kw)
    assert code == 0, out
    return out
