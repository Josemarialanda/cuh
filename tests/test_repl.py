import io

from cuh.repl import repl


def session(text):
    out, err = io.StringIO(), io.StringIO()
    code = repl(io.StringIO(text), out, err)
    return code, out.getvalue(), err.getvalue()


def test_echo_and_blocks():
    code, out, err = session("2 plus 3 cuh\nfam sq takes x cuh\npull up with x times x cuh\ndone cuh\nayo sq 7 cuh\n")
    assert code == 0
    assert out == "cuh(100%)> 5\ncuh(100%)>   ...>   ...> cuh(100%)> 49\ncuh(100%)> \n"


def test_skipped_line_costs_respect():
    code, out, err = session("1 cuh\nhello\n2 cuh\n")
    assert "...?" in out
    assert "cuh(50%)>" in out


def test_disrespect_quits():
    code, out, err = session("1 cuh\na\nb\nc\nsay it fr 2 cuh\n")
    assert code == 2
    assert "2\n" not in out
    assert out.endswith("i'm out. (respect: 25%)\n")


def test_errors_keep_going():
    code, out, err = session("say it nope cuh\nsay it fr 1 cuh\n")
    assert 'never met' in err or 'who is' in err
    assert "1\n" in out


def test_exit():
    code, out, err = session("i'm out cuh\nsay it fr 1 cuh\n")
    assert code == 0 and "1\n" not in out
