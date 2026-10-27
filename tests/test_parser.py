import pytest

from cuh import nodes as N
from cuh.errors import CuhError
from cuh.lexer import analyze
from cuh.parser import parse


def p(src):
    return parse(analyze(src))


def expr(src):
    (stmt,) = p(src + " cuh\n")
    return stmt.expr


def test_precedence():
    e = expr("1 plus 2 times 3 is 7 and facts")
    assert isinstance(e, N.BinOp) and e.op == "and"
    cmp = e.left
    assert cmp.op == "is"
    assert cmp.left.op == "plus" and cmp.left.right.op == "times"


def test_hol_up_groups():
    e = expr("hol up 2 plus 3 aight times 4")
    assert e.op == "times" and e.left.op == "plus"


def test_ayo_args_are_greedy():
    e = expr("ayo f 1, 2 plus 3")
    assert isinstance(e, N.Call) and e.ayo and len(e.args) == 2
    assert e.args[1].op == "plus"


def test_builtins_bind_tight():
    e = expr("headcount crew is 3")
    assert e.op == "is" and isinstance(e.left, N.Unary)


def test_spot_is_postfix():
    e = expr("crew spot 1 plus 1")
    assert e.op == "plus" and isinstance(e.left, N.Index)


def test_if_chain():
    (s,) = p("if it's x cuh\n1 cuh\nor if it's y cuh\n2 cuh\nnah then cuh\n3 cuh\ndone cuh\n")
    assert isinstance(s, N.If) and len(s.branches) == 2 and len(s.otherwise) == 1


def test_comment_lines_are_never_parsed():
    assert len(p("this ( has + junk\nsay it 1 cuh\n")) == 1


@pytest.mark.parametrize("src,line", [
    ("fam f cuh\nsay it 1 cuh\n", 1),
    ("done cuh\n", 1),
    ("dip cuh\n", 1),
    ("pull up with 1 cuh\n", 1),
    ("say it 1 cuh\nno cap cuh\n", 2),
    ("cousin x 5 cuh\n", 1),
    ("say it 1 plus cuh\n", 1),
    ("say it 1 + 2 cuh\n", 1),
])
def test_syntax_errors(src, line):
    with pytest.raises(CuhError) as e:
        p(src)
    assert e.value.msg == f"nah cuh, line {line} ain't it"
